from __future__ import annotations

from typing import Any, Dict, List

from graphrag.graph.graph_rag import GraphRag

from .mcp import ToolCallResult, ToolExecutionError, ToolSpec


class GraphRagToolProvider:
    """Local knowledge graph search tool provider."""

    def __init__(self, graph: GraphRag, *, tool_name: str = "graph_search", default_limit: int = 12):
        self.name = "graph_rag"
        self._graph = graph
        self._tool_name = tool_name.strip() or "graph_search"
        self._default_limit = max(1, int(default_limit))

    def list_tools(self, *, refresh: bool = False) -> List[ToolSpec]:
        _ = refresh
        return [
            ToolSpec(
                name=self._tool_name,
                description=(
                    "Searches local Neo4j GraphRAG knowledge base by natural-language query and "
                    "returns relevant context chunks with scores."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "minimum": 1, "default": self._default_limit},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
                provider=self.name,
            )
        ]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolCallResult:
        requested = (tool_name or "").strip()
        if requested != self._tool_name:
            raise ToolExecutionError(f"tool '{requested}' is not provided by {self.name}")
        if not isinstance(arguments, dict):
            raise ToolExecutionError("arguments must be a JSON object")

        query = str(arguments.get("query", "")).strip()
        if not query:
            raise ToolExecutionError("graph_search requires non-empty 'query'")
        limit = arguments.get("limit", self._default_limit)
        try:
            limit_n = max(1, int(limit))
        except Exception as exc:
            raise ToolExecutionError("graph_search 'limit' must be an integer") from exc

        rows = self._graph.search(query, limit=limit_n)
        return ToolCallResult(
            tool_name=self._tool_name,
            arguments={"query": query, "limit": limit_n},
            output=rows,
            raw_output="",
            provider=self.name,
        )

