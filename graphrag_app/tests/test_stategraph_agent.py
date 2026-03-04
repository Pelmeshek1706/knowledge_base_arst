from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any, Dict, List

from langchain_core.messages import AIMessage

from graphrag.orchestrator.stategraph_agent import StateGraphKnowledgeAgent
from graphrag.tools.mcp import ToolCallResult, ToolSpec


@dataclass
class _FakeRegistry:
    def list_tools(self, *, refresh: bool = False) -> List[ToolSpec]:
        _ = refresh
        return [ToolSpec(name="graph_search", provider="fake")]

    def resolve_tool_name(self, tool_name: str) -> str | None:
        if tool_name in {"graph_search", "graph_search"}:
            return "graph_search"
        return None

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolCallResult:
        _ = (tool_name, arguments)
        return ToolCallResult(
            tool_name="graph_search",
            arguments=arguments,
            output=[{"chunk_id": "c1", "text": "context"}],
            raw_output="",
            provider="fake",
        )


@dataclass
class _FakeRegistryWithWeb:
    def list_tools(self, *, refresh: bool = False) -> List[ToolSpec]:
        _ = refresh
        return [
            ToolSpec(name="graph_search", provider="fake"),
            ToolSpec(name="duckduckgo.search", provider="fake"),
            ToolSpec(name="duckduckgo.fetch_content", provider="fake"),
        ]

    def resolve_tool_name(self, tool_name: str) -> str | None:
        if tool_name == "graph_search":
            return "graph_search"
        return None

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolCallResult:
        _ = arguments
        return ToolCallResult(
            tool_name=tool_name,
            arguments={},
            output=[],
            raw_output="",
            provider="fake",
        )


class _Structured:
    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload

    def invoke(self, messages: Any) -> Dict[str, Any]:
        _ = messages
        return dict(self.payload)


class _FakeModel:
    def bind_tools(self, tools: Any) -> "_FakeModel":
        _ = tools
        return self

    def with_structured_output(self, schema: Any) -> _Structured:
        _ = schema
        return _Structured({"is_complete": True, "reason": "ok"})

    def invoke(self, messages: Any) -> AIMessage:
        text = "\n".join(str(getattr(m, "content", "")) for m in messages)
        if "Provide the final answer" in text:
            return AIMessage(content="Final answer from fake model")
        return AIMessage(content="No tool calls needed")


class StateGraphAgentTests(unittest.TestCase):
    def test_no_tool_plan_finalizes(self) -> None:
        agent = StateGraphKnowledgeAgent(
            model=_FakeModel(),
            tool_registry=_FakeRegistry(),
            allowed_tools=["graph_search"],
            web_budget=0,
            max_research_iterations=1,
        )
        result = agent.answer("What is in project docs?")
        self.assertIn("Final answer", result.answer)
        self.assertEqual(result.executed_results, [])

    def test_research_gate_treats_namespaced_web_tool_as_web(self) -> None:
        agent = StateGraphKnowledgeAgent(
            model=_FakeModel(),
            tool_registry=_FakeRegistryWithWeb(),
            allowed_tools=["graph_search", "duckduckgo.search", "duckduckgo.fetch_content"],
            web_budget=2,
            max_deep_links=1,
            max_research_iterations=2,
        )
        updates = agent._research_gate_node(
            {
                "question": "latest kiev news",
                "messages": [],
                "tool_trace": [
                    {
                        "tool_name": "duckduckgo.search",
                        "provider": "fake",
                        "arguments": {"query": "latest kiev news", "max_results": 8},
                        "output_preview": "one result",
                    }
                ],
                "sources": [{"title": "result", "url": "https://example.com/news"}],
                "web_budget": 2,
                "deep_link_budget": 1,
                "processed_message_count": 0,
                "fetched_urls": [],
                "research_iterations": 0,
            }
        )
        self.assertEqual(updates["planning_meta"]["next_step"], "deep_fetch")


if __name__ == "__main__":
    unittest.main()
