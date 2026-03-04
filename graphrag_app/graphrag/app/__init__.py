"""Application-layer modules for demo bootstrap, ingestion, CLI, and tracing."""

from .bootstrap import AppRuntime, build_runtime, print_banner
from .cli_commands import (
    build_tool_registry,
    call_web_search,
    entity_context,
    env_bool,
    find_entity_path,
    graph_stats,
    print_commands,
    print_graph_summary,
    search_documents,
    search_entities,
    tool_output_to_text,
)
from .ingest import ingest_data_json
from .trace_logging import print_retrieval_trace, print_tool_agent_trace, shorten_text

__all__ = [
    "AppRuntime",
    "build_runtime",
    "build_tool_registry",
    "call_web_search",
    "entity_context",
    "env_bool",
    "find_entity_path",
    "graph_stats",
    "ingest_data_json",
    "print_banner",
    "print_commands",
    "print_graph_summary",
    "print_retrieval_trace",
    "print_tool_agent_trace",
    "search_documents",
    "search_entities",
    "shorten_text",
    "tool_output_to_text",
]
