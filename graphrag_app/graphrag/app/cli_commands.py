from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List

from graphrag.graph.graph_rag import GraphRag
from graphrag.storage.neo4j_client import Neo4jClient
from graphrag.tools import (
    AgentToolRegistry,
    DockerMcpToolProvider,
    GraphRagToolProvider,
    ToolCallResult,
)

logger = logging.getLogger(__name__)


def env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def print_commands() -> None:
    logger.info("Commands:")
    logger.info("  exit | quit          - Exit session")
    logger.info("  help | ?             - Show commands")
    logger.info("  stats                - Show graph stats")
    logger.info("  tools                - Show available tools (GraphRAG + MCP)")
    logger.info("  web <query>          - Run web-search tool directly")
    logger.info("  tool <name> <json>   - Call any tool directly")
    logger.info("  docs <topic>         - Search documents")
    logger.info("  entity <name>        - Show entity context")
    logger.info("  find <e1> <e2>       - Find path between entities")
    logger.info("  trace [on|off]       - Toggle retrieval trace output")
    logger.info("  clear                - Clear chat history (stateless in this demo)")


def graph_stats(client: Neo4jClient) -> Dict[str, int]:
    def _count(label: str) -> int:
        rows = client.run(f"MATCH (n:{label}) RETURN COUNT(n) AS count")
        return int(rows[0]["count"]) if rows else 0

    rels = client.run("MATCH ()-[r]->() RETURN COUNT(r) AS count")
    return {
        "documents": _count("Document"),
        "chunks": _count("Chunk"),
        "entities": _count("Entity"),
        "tags": _count("Tag"),
        "relationships": int(rels[0]["count"]) if rels else 0,
    }


def print_graph_summary(client: Neo4jClient) -> None:
    stats = graph_stats(client)
    logger.info("=" * 40)
    logger.info("GRAPH SUMMARY")
    logger.info("=" * 40)
    logger.info("Documents:     %s", stats["documents"])
    logger.info("Chunks:        %s", stats["chunks"])
    logger.info("Entities:      %s", stats["entities"])
    logger.info("Tags:          %s", stats["tags"])
    logger.info("Relationships: %s", stats["relationships"])
    logger.info("=" * 40)


def choose_web_search_tool(tool_names: List[str]) -> str | None:
    if not tool_names:
        return None

    preferred = sorted(
        [n for n in tool_names if "duckduckgo" in n.lower() and n.lower().endswith("search")]
    )
    if preferred:
        return preferred[0]

    generic = sorted(
        [
            n
            for n in tool_names
            if (n.lower().endswith("search") or n == "search") and n.lower() not in {"graph_search"}
        ]
    )
    if generic:
        return generic[0]
    return None


def tool_output_to_text(value: Any, *, max_chars: int = 5000) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        text = value.strip()
    elif isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, indent=2)
    else:
        text = str(value)

    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def build_tool_registry(graph: GraphRag) -> tuple[AgentToolRegistry, str | None]:
    providers = [GraphRagToolProvider(graph)]
    web_search_tool: str | None = None

    if env_bool("ENABLE_MCP_TOOLS", True):
        timeout_s = int(os.environ.get("MCP_TOOL_TIMEOUT_S", "30"))
        providers.append(DockerMcpToolProvider(timeout_s=timeout_s))

    registry = AgentToolRegistry(providers)
    names = [t.name for t in registry.list_tools(refresh=True)]
    if names:
        logger.info("Discovered tools: %s", ", ".join(names))
        explicit = os.environ.get("MCP_WEB_SEARCH_TOOL", "").strip()
        if explicit:
            resolved = registry.resolve_tool_name(explicit)
            if resolved:
                web_search_tool = resolved
            else:
                logger.warning("MCP_WEB_SEARCH_TOOL='%s' not found; using auto-detected web tool.", explicit)
        if not web_search_tool:
            web_search_tool = choose_web_search_tool(names)
    else:
        logger.info("No tools discovered.")

    return registry, web_search_tool


def call_web_search(
    registry: AgentToolRegistry,
    search_tool_name: str,
    query: str,
) -> ToolCallResult:
    max_results = int(os.environ.get("MCP_WEB_MAX_RESULTS", "5"))
    return registry.call_tool(
        search_tool_name,
        {"query": query, "max_results": max_results},
    )


def search_documents(client: Neo4jClient, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
    return client.run(
        """
        MATCH (d:Document)
        OPTIONAL MATCH (d)-[:CONTAINS]->(c:Chunk)
        OPTIONAL MATCH (c)-[:HAS_TAG]->(t:Tag)
        WHERE toLower(d.title) CONTAINS toLower($topic)
           OR toLower(c.text) CONTAINS toLower($topic)
           OR toLower(t.name) CONTAINS toLower($topic)
        RETURN DISTINCT d.doc_id AS doc_id, d.title AS title, d.file_path AS file_path
        LIMIT $limit
        """,
        {"topic": topic, "limit": limit},
    )


def search_entities(client: Neo4jClient, term: str, limit: int = 10) -> List[Dict[str, Any]]:
    return client.run(
        """
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower($term)
        RETURN e.name AS name, e.type AS type
        LIMIT $limit
        """,
        {"term": term, "limit": limit},
    )


def entity_context(client: Neo4jClient, name: str) -> Dict[str, Any] | None:
    rows = client.run(
        """
        MATCH (e:Entity {name: $name})
        OPTIONAL MATCH (e)-[r1]->(n1:Entity)
        WITH e, collect(DISTINCT {name: n1.name, type: n1.type, relation: type(r1), direction: "out"}) AS out_neighbors
        OPTIONAL MATCH (e)<-[r2]-(n2:Entity)
        WITH e, out_neighbors + collect(DISTINCT {name: n2.name, type: n2.type, relation: type(r2), direction: "in"}) AS neighbors
        OPTIONAL MATCH (c:Chunk)-[:MENTIONS]->(e)
        OPTIONAL MATCH (d:Document)-[:CONTAINS]->(c)
        RETURN e.name AS name,
               e.type AS type,
               [x IN neighbors WHERE x.name IS NOT NULL] AS neighbors,
               collect(DISTINCT d.title) AS documents
        """,
        {"name": name},
    )
    return rows[0] if rows else None


def find_entity_path(client: Neo4jClient, e1: str, e2: str) -> Dict[str, Any] | None:
    rows = client.run(
        """
        MATCH (a:Entity {name: $e1}), (b:Entity {name: $e2})
        MATCH path = shortestPath((a)-[*..5]-(b))
        RETURN length(path) AS distance,
               [n IN nodes(path) | n.name] AS path_nodes,
               [r IN relationships(path) | type(r)] AS relations
        """,
        {"e1": e1, "e2": e2},
    )
    return rows[0] if rows else None
