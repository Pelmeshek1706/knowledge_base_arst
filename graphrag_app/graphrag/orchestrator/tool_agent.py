from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.language_models import BaseChatModel

from graphrag.orchestrator.stategraph_agent import StateGraphKnowledgeAgent
from graphrag.tools import AgentToolRegistry, ToolCallResult, ToolExecutionError


@dataclass(frozen=True)
class PlannedToolCall:
    tool_name: str
    arguments: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolAgentResult:
    answer: str
    planned_calls: List[PlannedToolCall]
    executed_results: List[ToolCallResult]
    context: str
    planning_raw: str = ""


class ToolOrchestratedAgent:
    """
    Compatibility wrapper over two runtimes:
    - `stategraph` (default): new LangGraph StateGraph orchestration
    - `legacy`: previous custom planner/executor loop
    """

    def __init__(
        self,
        llm: Any,
        tool_registry: AgentToolRegistry,
        *,
        max_tool_calls: int = 2,
        context_max_chars: int = 12000,
        allowed_tools: Optional[List[str]] = None,
        max_deep_links: int = 1,
        max_research_iterations: int = 2,
        runtime: Optional[str] = None,
        legacy_llm: Any | None = None,
        web_budget: Optional[int] = None,
    ):
        self.runtime = (runtime or os.environ.get("AGENT_RUNTIME", "stategraph")).strip().lower()
        self._backend: Any

        if self.runtime == "legacy":
            from .legacy_tool_agent import ToolOrchestratedAgent as LegacyToolOrchestratedAgent

            backend_llm = legacy_llm or llm
            self._backend = LegacyToolOrchestratedAgent(
                backend_llm,
                tool_registry,
                max_tool_calls=max_tool_calls,
                context_max_chars=context_max_chars,
                allowed_tools=allowed_tools,
                max_deep_links=max_deep_links,
                max_research_iterations=max_research_iterations,
            )
            return

        # StateGraph runtime
        if not isinstance(llm, BaseChatModel):
            if legacy_llm is not None:
                from .legacy_tool_agent import ToolOrchestratedAgent as LegacyToolOrchestratedAgent

                self.runtime = "legacy"
                self._backend = LegacyToolOrchestratedAgent(
                    legacy_llm,
                    tool_registry,
                    max_tool_calls=max_tool_calls,
                    context_max_chars=context_max_chars,
                    allowed_tools=allowed_tools,
                    max_deep_links=max_deep_links,
                    max_research_iterations=max_research_iterations,
                )
                return
            raise TypeError(
                "StateGraph runtime requires a LangChain chat model (BaseChatModel). "
                "Provide legacy_llm or set AGENT_RUNTIME=legacy."
            )

        self._backend = StateGraphKnowledgeAgent(
            llm,
            tool_registry,
            max_tool_calls=max_tool_calls,
            context_max_chars=context_max_chars,
            allowed_tools=allowed_tools,
            max_deep_links=max_deep_links,
            max_research_iterations=max_research_iterations,
            web_budget=(
                int(web_budget)
                if web_budget is not None
                else int(os.environ.get("AGENT_WEB_BUDGET", "2"))
            ),
        )

    def answer(self, question: str) -> ToolAgentResult:
        if self.runtime == "legacy":
            return self._backend.answer(question)

        out = self._backend.answer(question)

        planned_calls = [
            PlannedToolCall(
                tool_name=str(item.get("tool_name", "")).strip(),
                arguments=item.get("arguments") if isinstance(item.get("arguments"), dict) else {},
            )
            for item in out.planned_calls
            if isinstance(item, dict)
        ]

        executed_results: List[ToolCallResult] = []
        for item in out.executed_results:
            executed_results.append(
                ToolCallResult(
                    tool_name=item.tool_name,
                    arguments=dict(item.arguments),
                    output=item.output_preview,
                    raw_output=item.output_preview,
                    provider=item.provider,
                )
            )

        return ToolAgentResult(
            answer=out.answer,
            planned_calls=planned_calls,
            executed_results=executed_results,
            context=out.context,
            planning_raw=json.dumps(out.planning_meta, ensure_ascii=False),
        )

    def render_stategraph(
        self,
        *,
        png_output_path: Optional[str] = None,
        mermaid_output_path: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Render StateGraph visualization artifacts.

        Keys:
          - png_path: saved PNG diagram path
          - mermaid_path: saved Mermaid source path
          - error: non-fatal rendering error text
        """
        if self.runtime != "stategraph":
            return {}

        compiled = getattr(self._backend, "graph", None)
        if compiled is None or not hasattr(compiled, "get_graph"):
            return {}

        drawable = compiled.get_graph()
        out: Dict[str, str] = {}

        if mermaid_output_path:
            try:
                mermaid = drawable.draw_mermaid()
                if mermaid:
                    mmd_path = Path(mermaid_output_path)
                    if not mmd_path.is_absolute():
                        mmd_path = Path.cwd() / mmd_path
                    mmd_path.parent.mkdir(parents=True, exist_ok=True)
                    mmd_path.write_text(mermaid + "\n", encoding="utf-8")
                    out["mermaid_path"] = str(mmd_path)
            except Exception as exc:
                out["error"] = f"Failed to export Mermaid diagram: {exc}"

        if png_output_path:
            png_path = Path(png_output_path)
            if not png_path.is_absolute():
                png_path = Path.cwd() / png_path
            png_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                drawable.draw_mermaid_png(output_file_path=str(png_path))
                out["png_path"] = str(png_path)
            except Exception as exc:
                # Fallback to Graphviz-based renderer when Mermaid backend is unavailable.
                try:
                    drawable.draw_png(output_file_path=str(png_path))
                    out["png_path"] = str(png_path)
                except Exception:
                    out["error"] = f"Failed to export PNG diagram: {exc}"

        return out
