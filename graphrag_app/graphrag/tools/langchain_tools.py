from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from graphrag.tools.mcp import AgentToolRegistry, ToolExecutionError


class GraphSearchArgs(BaseModel):
    """Arguments for local graph search."""

    query: str = Field(..., min_length=1, description="Natural-language query for local graph knowledge")
    limit: int = Field(default=12, ge=1, le=64, description="Maximum number of graph rows")


class WebSearchArgs(BaseModel):
    """Arguments for web search."""

    query: str = Field(..., min_length=1, description="Internet search query")
    max_results: int = Field(default=8, ge=1, le=20, description="Maximum number of web results")


class FetchContentArgs(BaseModel):
    """Arguments for page content fetch."""

    url: str = Field(..., min_length=5, description="Absolute URL to fetch content for")


class ThinkArgs(BaseModel):
    """Arguments for reflection tool."""

    reflection: str = Field(..., min_length=3, description="Short reasoning note used for planning")


@dataclass(frozen=True)
class LangChainToolset:
    tools: List[BaseTool]
    graph_tool: Optional[str]
    web_tool: Optional[str]
    fetch_tool: Optional[str]


def is_web_search_tool(name: str) -> bool:
    n = (name or "").strip().lower()
    if not n or n == "graph_search":
        return False
    return n == "search" or n.endswith(".search") or ("duckduckgo" in n and "search" in n)


def is_fetch_content_tool(name: str) -> bool:
    n = (name or "").strip().lower()
    return n == "fetch_content" or n.endswith(".fetch_content")


def _pick_web_tool(candidates: Sequence[str]) -> Optional[str]:
    names = [n for n in candidates if is_web_search_tool(n)]
    if not names:
        return None
    preferred = sorted([n for n in names if "duckduckgo" in n.lower()])
    if preferred:
        return preferred[0]
    return sorted(names)[0]


def _safe_preview(value: Any, *, max_chars: int = 2500) -> str:
    if isinstance(value, str):
        text = value.strip()
    elif isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    if len(text) > max_chars:
        return text[: max_chars - 3] + "..."
    return text


def extract_urls(value: Any) -> List[str]:
    found: List[str] = []
    seen: set[str] = set()

    def _add(url: str) -> None:
        cleaned = (url or "").strip().rstrip(".,;:)]}>")
        if not cleaned or cleaned in seen:
            return
        seen.add(cleaned)
        found.append(cleaned)

    def _walk(obj: Any) -> None:
        if obj is None:
            return
        if isinstance(obj, str):
            for match in re.findall(r"https?://[^\s<>\]\"')]+", obj):
                _add(match)
            return
        if isinstance(obj, dict):
            for key, val in obj.items():
                key_lower = str(key).lower()
                if key_lower in {"url", "href", "link", "source"} and isinstance(val, str):
                    _add(val)
                else:
                    _walk(val)
            return
        if isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(value)
    return found


def build_langchain_tools(
    tool_registry: AgentToolRegistry,
    *,
    allowed_tools: Optional[List[str]] = None,
) -> LangChainToolset:
    specs = tool_registry.list_tools(refresh=True)
    available = [s.name for s in specs]
    if allowed_tools:
        allowed = {n for n in allowed_tools if n}
        available = [n for n in available if n in allowed]

    graph_tool = tool_registry.resolve_tool_name("graph_search")
    if graph_tool and allowed_tools and graph_tool not in set(allowed_tools):
        graph_tool = None

    web_tool = _pick_web_tool(available)

    fetch_tool = None
    for name in available:
        if is_fetch_content_tool(name):
            fetch_tool = name
            break

    def _registry_call(registry_tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = tool_registry.call_tool(registry_tool, args)
            return {
                "ok": True,
                "tool": result.tool_name,
                "provider": result.provider,
                "arguments": result.arguments,
                "output": result.output,
                "preview": _safe_preview(result.output),
                "urls": extract_urls(result.output),
            }
        except ToolExecutionError as exc:
            return {
                "ok": False,
                "tool": registry_tool,
                "provider": "",
                "arguments": args,
                "output": "",
                "preview": str(exc),
                "urls": [],
            }

    @tool("graph_search", parse_docstring=True, args_schema=GraphSearchArgs)
    def graph_search(query: str, limit: int = 12) -> Dict[str, Any]:
        """Search local Neo4j GraphRAG knowledge base.

        Args:
            query: User query for project/domain knowledge.
            limit: Max rows to return.
        """
        if not graph_tool:
            return {
                "ok": False,
                "tool": "graph_search",
                "provider": "",
                "arguments": {"query": query, "limit": limit},
                "output": [],
                "preview": "graph_search tool is unavailable",
                "urls": [],
            }
        return _registry_call(graph_tool, {"query": query, "limit": int(limit)})

    @tool("web_search", parse_docstring=True, args_schema=WebSearchArgs)
    def web_search(query: str, max_results: int = 8) -> Dict[str, Any]:
        """Search the internet via configured MCP provider.

        Args:
            query: Search query.
            max_results: Number of results to request.
        """
        if not web_tool:
            return {
                "ok": False,
                "tool": "web_search",
                "provider": "",
                "arguments": {"query": query, "max_results": max_results},
                "output": [],
                "preview": "web_search tool is unavailable",
                "urls": [],
            }
        return _registry_call(web_tool, {"query": query, "max_results": int(max_results)})

    @tool("fetch_content", parse_docstring=True, args_schema=FetchContentArgs)
    def fetch_content(url: str) -> Dict[str, Any]:
        """Fetch full page content for a URL.

        Args:
            url: Absolute page URL.
        """
        if not fetch_tool:
            return {
                "ok": False,
                "tool": "fetch_content",
                "provider": "",
                "arguments": {"url": url},
                "output": "",
                "preview": "fetch_content tool is unavailable",
                "urls": [],
            }
        return _registry_call(fetch_tool, {"url": url})

    @tool("think", parse_docstring=True, args_schema=ThinkArgs)
    def think(reflection: str) -> Dict[str, Any]:
        """Record a short reflection step in the research loop.

        Args:
            reflection: Short reflection for reasoning trace.
        """
        return {
            "ok": True,
            "tool": "think",
            "provider": "internal",
            "arguments": {"reflection": reflection},
            "output": f"Reflection recorded: {reflection}",
            "preview": reflection,
            "urls": [],
        }

    active_tools: List[BaseTool] = [graph_search]
    if web_tool:
        active_tools.append(web_search)
    if fetch_tool:
        active_tools.append(fetch_content)
    active_tools.append(think)

    return LangChainToolset(
        tools=active_tools,
        graph_tool=graph_tool,
        web_tool=web_tool,
        fetch_tool=fetch_tool,
    )
