from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any, Dict, List

from graphrag.tools.langchain_tools import build_langchain_tools, extract_urls
from graphrag.tools.mcp import ToolCallResult, ToolSpec


@dataclass
class _FakeRegistry:
    calls: List[Dict[str, Any]]

    def list_tools(self, *, refresh: bool = False) -> List[ToolSpec]:
        _ = refresh
        return [
            ToolSpec(name="graph_search", provider="fake"),
            ToolSpec(name="duckduckgo.search", provider="fake"),
            ToolSpec(name="duckduckgo.fetch_content", provider="fake"),
        ]

    def resolve_tool_name(self, tool_name: str) -> str | None:
        names = [s.name for s in self.list_tools()]
        if tool_name in names:
            return tool_name
        for name in names:
            if name.endswith(f".{tool_name}"):
                return name
        return None

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolCallResult:
        self.calls.append({"tool_name": tool_name, "arguments": dict(arguments)})
        output: Any
        if "search" in tool_name and "fetch" not in tool_name:
            output = {"results": [{"url": "https://example.com", "title": "Example"}]}
        elif "fetch_content" in tool_name:
            output = "https://example.com/page content"
        else:
            output = []
        return ToolCallResult(
            tool_name=tool_name,
            arguments=dict(arguments),
            output=output,
            raw_output="",
            provider="fake",
        )


class LangChainToolsTests(unittest.TestCase):
    def test_build_tools_and_call_registry(self) -> None:
        registry = _FakeRegistry(calls=[])
        toolset = build_langchain_tools(registry)

        names = {tool.name for tool in toolset.tools}
        self.assertIn("graph_search", names)
        self.assertIn("web_search", names)
        self.assertIn("fetch_content", names)

        graph_tool = next(tool for tool in toolset.tools if tool.name == "graph_search")
        out = graph_tool.invoke({"query": "ptsd", "limit": 3})
        self.assertTrue(out["ok"])
        self.assertEqual(registry.calls[-1]["tool_name"], "graph_search")

        web_tool = next(tool for tool in toolset.tools if tool.name == "web_search")
        out2 = web_tool.invoke({"query": "latest", "max_results": 2})
        self.assertTrue(out2["ok"])
        self.assertEqual(registry.calls[-1]["tool_name"], "duckduckgo.search")

    def test_extract_urls(self) -> None:
        payload = {
            "url": "https://a.example.com",
            "items": [
                "Read https://b.example.com/path",
                {"link": "https://c.example.com"},
            ],
        }
        urls = extract_urls(payload)
        self.assertEqual(
            urls,
            [
                "https://a.example.com",
                "https://b.example.com/path",
                "https://c.example.com",
            ],
        )


if __name__ == "__main__":
    unittest.main()
