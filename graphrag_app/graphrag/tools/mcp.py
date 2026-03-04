from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol, Sequence


class ToolExecutionError(RuntimeError):
    """Raised when external tool execution fails."""


@dataclass(frozen=True)
class ToolSpec:
    """Unified tool metadata used by the agent."""

    name: str
    description: str = ""
    input_schema: Dict[str, Any] = field(default_factory=dict)
    provider: str = ""


@dataclass(frozen=True)
class ToolCallResult:
    """Normalized execution result for any external tool provider."""

    tool_name: str
    arguments: Dict[str, Any]
    output: Any
    raw_output: str
    provider: str


class ToolProvider(Protocol):
    """Contract for pluggable tool providers."""

    name: str

    def list_tools(self, *, refresh: bool = False) -> List[ToolSpec]:
        raise NotImplementedError

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolCallResult:
        raise NotImplementedError


def _extract_json_block(text: str) -> Any:
    payload = (text or "").strip()
    if not payload:
        return payload
    try:
        return json.loads(payload)
    except Exception:
        pass

    starts = [idx for idx in (payload.find("{"), payload.find("[")) if idx >= 0]
    if not starts:
        return payload
    start = min(starts)
    candidate = payload[start:]
    try:
        return json.loads(candidate)
    except Exception:
        return payload


class DockerMcpToolProvider:
    """
    Adapter over Docker MCP Toolkit CLI.

    Designed as a reusable provider for any MCP-based tool that is available
    through `docker mcp ...`.
    """

    def __init__(self, *, docker_bin: str = "docker", timeout_s: int = 30):
        self.name = "docker_mcp"
        self.docker_bin = docker_bin
        self.timeout_s = max(1, int(timeout_s))
        self._cache: List[ToolSpec] = []

    def _run(self, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            timeout=self.timeout_s,
            check=False,
        )

    @staticmethod
    def _build_tool_name(server: str, tool: str) -> str:
        server_name = (server or "").strip()
        tool_name = (tool or "").strip()
        if server_name and tool_name:
            return f"{server_name}.{tool_name}"
        return tool_name or server_name

    def _parse_tools_json(self, data: Any) -> List[ToolSpec]:
        if isinstance(data, dict):
            if isinstance(data.get("tools"), list):
                entries = data["tools"]
            else:
                entries = [data]
        elif isinstance(data, list):
            entries = data
        else:
            return []

        out: List[ToolSpec] = []
        for item in entries:
            if not isinstance(item, dict):
                continue
            server = str(item.get("server", "") or item.get("serverName", "") or "").strip()
            tool = str(
                item.get("tool", "")
                or item.get("name", "")
                or item.get("toolName", "")
                or ""
            ).strip()
            if not tool:
                continue
            full_name = self._build_tool_name(server, tool)
            out.append(
                ToolSpec(
                    name=full_name,
                    description=str(item.get("description", "") or "").strip(),
                    input_schema=item.get("inputSchema") if isinstance(item.get("inputSchema"), dict) else {},
                    provider=self.name,
                )
            )
        return out

    def _parse_tools_text(self, text: str) -> List[ToolSpec]:
        lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
        if not lines:
            return []
        out: List[ToolSpec] = []
        for line in lines:
            if line.lower().startswith("tip:"):
                continue
            if line.lower().startswith("docker mcp"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            server = parts[0]
            tool = parts[1]
            if server.lower() in {"server", "name"} and tool.lower() in {"tool", "id"}:
                continue
            desc = " ".join(parts[2:]) if len(parts) > 2 else ""
            full_name = self._build_tool_name(server, tool)
            out.append(ToolSpec(name=full_name, description=desc, provider=self.name))
        return out

    def list_tools(self, *, refresh: bool = False) -> List[ToolSpec]:
        if self._cache and not refresh:
            return list(self._cache)

        commands: List[List[str]] = [
            [self.docker_bin, "mcp", "tools", "ls", "--format", "json"],
            [self.docker_bin, "mcp", "tools", "--format", "json", "ls"],
            [self.docker_bin, "mcp", "tools", "ls"],
        ]
        errors: List[str] = []
        for cmd in commands:
            proc = self._run(cmd)
            if proc.returncode != 0:
                err = (proc.stderr or proc.stdout or "").strip()
                errors.append(err)
                continue

            parsed = _extract_json_block(proc.stdout)
            tools = self._parse_tools_json(parsed)
            if not tools:
                tools = self._parse_tools_text(proc.stdout)
            if tools:
                self._cache = tools
                return list(self._cache)

        if errors:
            joined = " | ".join(e for e in errors if e)
            raise ToolExecutionError(joined or "failed to list MCP tools")
        self._cache = []
        return []

    @staticmethod
    def _build_call_arg_tokens(arguments: Dict[str, Any]) -> List[str]:
        tokens: List[str] = []
        for key, value in arguments.items():
            k = str(key).strip()
            if not k:
                continue
            if value is None:
                continue
            if isinstance(value, bool):
                v = "true" if value else "false"
            elif isinstance(value, (int, float, str)):
                v = str(value)
            else:
                v = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
            tokens.append(f"{k}={v}")
        return tokens

    def _candidate_call_commands(self, tool_name: str, arguments: Dict[str, Any]) -> List[List[str]]:
        arg_tokens = self._build_call_arg_tokens(arguments)
        args_json = json.dumps(arguments, ensure_ascii=True)
        return [
            [self.docker_bin, "mcp", "tools", "call", tool_name, *arg_tokens],
            [self.docker_bin, "mcp", "tools", "--format", "json", "call", tool_name, *arg_tokens],
            [self.docker_bin, "mcp", "tools", "call", tool_name, args_json],
            [self.docker_bin, "mcp", "tools", "--format", "json", "call", tool_name, args_json],
        ]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolCallResult:
        requested = (tool_name or "").strip()
        if not requested:
            raise ToolExecutionError("tool_name is required")
        if not isinstance(arguments, dict):
            raise ToolExecutionError("arguments must be a JSON object")

        names: List[str] = [requested]
        if "." in requested:
            names.append(requested.rsplit(".", 1)[-1])

        errors: List[str] = []
        for name in names:
            for cmd in self._candidate_call_commands(name, arguments):
                proc = self._run(cmd)
                if proc.returncode != 0:
                    err = (proc.stderr or proc.stdout or "").strip()
                    if err:
                        errors.append(err)
                    continue

                raw = (proc.stdout or "").strip()
                parsed = _extract_json_block(raw)
                return ToolCallResult(
                    tool_name=requested,
                    arguments=dict(arguments),
                    output=parsed,
                    raw_output=raw,
                    provider=self.name,
                )

        joined = " | ".join(e for e in errors if e)
        raise ToolExecutionError(joined or f"failed to call MCP tool '{requested}'")


class AgentToolRegistry:
    """Aggregates multiple providers behind one simple API."""

    def __init__(self, providers: Sequence[ToolProvider]):
        self._providers: List[ToolProvider] = list(providers)

    def list_tools(self, *, refresh: bool = False) -> List[ToolSpec]:
        merged: Dict[str, ToolSpec] = {}
        for provider in self._providers:
            try:
                specs = provider.list_tools(refresh=refresh)
            except ToolExecutionError:
                continue
            for spec in specs:
                merged.setdefault(spec.name, spec)
        return sorted(merged.values(), key=lambda item: item.name)

    def has_tool(self, tool_name: str) -> bool:
        return self.resolve_tool_name(tool_name) is not None

    def resolve_tool_name(self, tool_name: str) -> str | None:
        target = (tool_name or "").strip()
        if not target:
            return None
        names = [t.name for t in self.list_tools()]
        if target in names:
            return target

        suffix_matches = [name for name in names if name.endswith(f".{target}") or name == target]
        if len(suffix_matches) == 1:
            return suffix_matches[0]
        return None

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolCallResult:
        resolved = self.resolve_tool_name(tool_name) or tool_name
        errors: List[str] = []
        for provider in self._providers:
            try:
                return provider.call_tool(resolved, arguments)
            except ToolExecutionError as exc:
                errors.append(f"{provider.name}: {exc}")
                continue
        raise ToolExecutionError(" | ".join(errors) if errors else "no tool providers configured")
