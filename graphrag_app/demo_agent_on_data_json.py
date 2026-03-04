from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

from graphrag.app.bootstrap import build_runtime, print_banner
from graphrag.app.cli_commands import (
    call_web_search,
    entity_context,
    find_entity_path,
    print_commands,
    print_graph_summary,
    search_documents,
    search_entities,
    tool_output_to_text,
)
from graphrag.app.ingest import ingest_data_json
from graphrag.app.trace_logging import print_tool_agent_trace
from graphrag.tools import ToolExecutionError

DATA_JSON = os.environ.get(
    "DATA_JSON",
    "/Users/pelmeshek1706/Desktop/projects/knowledge_agent/data/data.json",
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _visualize_agent_structure(runtime: Any) -> None:
    png_path = os.environ.get(
        "AGENT_GRAPH_PNG_PATH",
        "graphrag_app/artifacts/agent_stategraph.png",
    )
    mermaid_path = os.environ.get(
        "AGENT_GRAPH_MERMAID_PATH",
        "graphrag_app/artifacts/agent_stategraph.mmd",
    )
    visuals = runtime.orchestrated_agent.render_stategraph(
        png_output_path=png_path,
        mermaid_output_path=mermaid_path,
    )
    if not visuals:
        logger.info("StateGraph visualization is unavailable for runtime=%s", runtime.orchestrated_agent.runtime)
        return

    if visuals.get("png_path"):
        logger.info("StateGraph PNG saved to %s", visuals["png_path"])
    if visuals.get("mermaid_path"):
        logger.info("StateGraph Mermaid saved to %s", visuals["mermaid_path"])
    if visuals.get("error"):
        logger.warning("%s", visuals["error"])


def main() -> None:
    print_banner(
        "Neo4j GraphRAG Builder",
        [
            "Extracts entities, relationships, and creates knowledge graph from documents",
            "Uses local LM Studio for entity extraction",
        ],
    )

    runtime = build_runtime()
    _visualize_agent_structure(runtime)
    try:
        logger.info(
            "LangSmith tracing: enabled=%s project=%s endpoint=%s",
            getattr(runtime.llm_ingest, "tracing_enabled", False),
            getattr(runtime.llm_ingest, "tracing_project", "") or "<unset>",
            os.environ.get("LANGSMITH_ENDPOINT", "<unset>"),
        )

        ingest_data_json(runtime.client, runtime.graph, runtime.llm_ingest, DATA_JSON)
        print_graph_summary(runtime.client)

        if runtime.web_search_tool:
            logger.info("Web tool selected: %s", runtime.web_search_tool)
        else:
            logger.info("No dedicated web-search tool found. Planner will use available tools.")

        print_banner(
            "GraphRAG Agent using LM Studio",
            ["Local-first RAG agent that queries Neo4j knowledge graph"],
        )
        print_commands()

        query_count = 0
        trace_enabled = True

        while True:
            q = input("\nYou> ").strip()
            if not q:
                continue

            q_lower = q.lower()
            if q_lower in {"exit", "quit"}:
                break
            if q_lower in {"help", "?"}:
                print_commands()
                continue
            if q_lower == "stats":
                print_graph_summary(runtime.client)
                continue
            if q_lower == "tools":
                try:
                    tools = runtime.tool_registry.list_tools(refresh=True)
                except ToolExecutionError as exc:
                    logger.info("Failed to list tools: %s", exc)
                    continue
                if not tools:
                    logger.info("No MCP tools discovered.")
                    continue
                logger.info("MCP tools (%s):", len(tools))
                for spec in tools:
                    suffix = f" :: {spec.description}" if spec.description else ""
                    logger.info("  - %s%s", spec.name, suffix)
                continue
            if q_lower.startswith("tool "):
                raw = q[5:].strip()
                if not raw:
                    logger.info("Usage: tool <name> <json-arguments>")
                    continue
                tool_name, sep, args_raw = raw.partition(" ")
                payload: Dict[str, Any] = {}
                if sep and args_raw.strip():
                    try:
                        parsed = json.loads(args_raw.strip())
                    except json.JSONDecodeError as exc:
                        logger.info("Invalid JSON arguments: %s", exc)
                        continue
                    if not isinstance(parsed, dict):
                        logger.info("Tool arguments must be a JSON object.")
                        continue
                    payload = parsed
                try:
                    result = runtime.tool_registry.call_tool(tool_name, payload)
                except ToolExecutionError as exc:
                    logger.info("Tool call failed: %s", exc)
                    continue
                text = tool_output_to_text(result.output)
                logger.info("Tool result (%s):\n%s", result.tool_name, text or "<empty>")
                continue
            if q_lower.startswith("web "):
                if not runtime.web_search_tool:
                    logger.info("DuckDuckGo MCP search tool is not configured.")
                    continue
                query = q[4:].strip()
                if not query:
                    logger.info("Usage: web <query>")
                    continue
                try:
                    result = call_web_search(runtime.tool_registry, runtime.web_search_tool, query)
                except ToolExecutionError as exc:
                    logger.info("Web search failed: %s", exc)
                    continue
                text = tool_output_to_text(result.output)
                logger.info("Web results:\n%s", text or "<empty>")
                continue
            if q_lower.startswith("trace"):
                parts = q_lower.split()
                if len(parts) == 1:
                    trace_enabled = not trace_enabled
                elif len(parts) == 2 and parts[1] in {"on", "off"}:
                    trace_enabled = parts[1] == "on"
                else:
                    logger.info("Usage: trace [on|off]")
                    continue
                logger.info("Trace mode: %s", "ON" if trace_enabled else "OFF")
                continue
            if q_lower == "clear":
                logger.info("Chat history cleared (stateless in this demo).")
                continue
            if q_lower.startswith("docs "):
                topic = q[5:].strip()
                if not topic:
                    logger.info("Usage: docs <topic>")
                    continue
                rows = search_documents(runtime.client, topic)
                if not rows:
                    logger.info("No documents found for '%s'", topic)
                    continue
                logger.info("Found %s documents for '%s':", len(rows), topic)
                for r in rows:
                    logger.info("  - %s (doc_id=%s)", r.get("title") or "<untitled>", r.get("doc_id"))
                continue
            if q_lower.startswith("entity "):
                term = q[7:].strip()
                if not term:
                    logger.info("Usage: entity <name>")
                    continue
                matches = search_entities(runtime.client, term)
                if not matches:
                    logger.info("No entities found for '%s'", term)
                    continue
                if len(matches) > 1 and all(m.get("name") != term for m in matches):
                    logger.info("Multiple matches found, try exact name:")
                    for m in matches[:10]:
                        logger.info("  - %s [%s]", m.get("name"), m.get("type"))
                    continue
                name = term if any(m.get("name") == term for m in matches) else matches[0].get("name")
                ctx = entity_context(runtime.client, name)
                if not ctx:
                    logger.info("No context for entity '%s'", name)
                    continue
                logger.info("Entity: %s [%s]", ctx.get("name"), ctx.get("type"))
                neighbors = ctx.get("neighbors") or []
                if neighbors:
                    logger.info("Connections:")
                    for n in neighbors[:8]:
                        logger.info("  - %s (%s, %s)", n.get("name"), n.get("relation"), n.get("direction"))
                docs = [d for d in (ctx.get("documents") or []) if d]
                if docs:
                    logger.info("Documents:")
                    for d in docs[:8]:
                        logger.info("  - %s", d)
                continue
            if q_lower.startswith("find "):
                parts = q[5:].strip().split()
                if len(parts) < 2:
                    logger.info("Usage: find <entity1> <entity2>")
                    continue
                path = find_entity_path(runtime.client, parts[0], parts[1])
                if not path or path.get("distance") is None:
                    logger.info("No path found between '%s' and '%s'", parts[0], parts[1])
                    continue
                logger.info("Path distance: %s", path.get("distance"))
                path_nodes = [
                    n for n in (path.get("path_nodes") or []) if isinstance(n, str) and n.strip()
                ]
                relations = [
                    r for r in (path.get("relations") or []) if isinstance(r, str) and r.strip()
                ]
                logger.info("Path: %s", " -> ".join(path_nodes) if path_nodes else "<empty>")
                logger.info("Relations: %s", " | ".join(relations) if relations else "<empty>")
                continue

            query_count += 1
            logger.info("Query #%s: %s", query_count, q)
            result = runtime.orchestrated_agent.answer(q)
            print("\nAssistant>\n", result.answer)
            if trace_enabled:
                print_tool_agent_trace(result)

    finally:
        runtime.client.close()


if __name__ == "__main__":
    main()
