from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List

from graphrag.config import Neo4jConfig
from graphrag.storage.neo4j_client import Neo4jClient
from graphrag.graph.graph_rag import GraphRag
from graphrag.llm.lm_studio import LMStudioClient, LMStudioConfig, GraphRagQAAgent
from graphrag.types.models import Chunk

DATA_JSON = os.environ.get("DATA_JSON", "/Users/pelmeshek1706/Desktop/projects/knowledge_agent/data/data.json")  # adjust for your machine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _print_banner(title: str, lines: List[str]) -> None:
    if not lines:
        logger.info(title)
        return
    width = max([len(title), *[len(line) for line in lines]])
    rule = "=" * width
    logger.info(rule)
    logger.info(title)
    for line in lines:
        logger.info(line)
    logger.info(rule)


def _print_commands() -> None:
    logger.info("Commands:")
    logger.info("  exit | quit          - Exit session")
    logger.info("  help | ?             - Show commands")
    logger.info("  stats                - Show graph stats")
    logger.info("  docs <topic>         - Search documents")
    logger.info("  entity <name>        - Show entity context")
    logger.info("  find <e1> <e2>        - Find path between entities")
    logger.info("  clear                - Clear chat history (stateless in this demo)")


def _graph_stats(client: Neo4jClient) -> Dict[str, int]:
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


def _print_graph_summary(client: Neo4jClient) -> None:
    stats = _graph_stats(client)
    logger.info("=" * 40)
    logger.info("GRAPH SUMMARY")
    logger.info("=" * 40)
    logger.info("Documents:     %s", stats["documents"])
    logger.info("Chunks:        %s", stats["chunks"])
    logger.info("Entities:      %s", stats["entities"])
    logger.info("Tags:          %s", stats["tags"])
    logger.info("Relationships: %s", stats["relationships"])
    logger.info("=" * 40)


def _search_documents(client: Neo4jClient, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
    rows = client.run(
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
    return rows


def _search_entities(client: Neo4jClient, term: str, limit: int = 10) -> List[Dict[str, Any]]:
    rows = client.run(
        """
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower($term)
        RETURN e.name AS name, e.type AS type
        LIMIT $limit
        """,
        {"term": term, "limit": limit},
    )
    return rows


def _entity_context(client: Neo4jClient, name: str) -> Dict[str, Any] | None:
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


def _find_entity_path(client: Neo4jClient, e1: str, e2: str) -> Dict[str, Any] | None:
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


def ingest_data_json(client: Neo4jClient, graph: GraphRag, llm: LMStudioClient, path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        docs = json.load(f)

    logger.info("Loading documents from %s", path)
    logger.info("Found %s documents", len(docs))

    graph.setup_graph_schema()
    logger.info("Neo4j schema ready")

    for i, d in enumerate(docs):
        doc_id = f"doc_{i:03d}"
        title = d.get("title", "") or ""
        desc = d.get("description", "") or ""
        source_type = "json"
        source_id = d.get("file_path", f"row_{i}")

        logger.info("Processing %s: %s", doc_id, title or "<untitled>")

        graph.upsert_document(
            doc_id=doc_id,
            title=title,
            source_type=source_type,
            source_id=str(source_id),
            file_path=d.get("file_path"),
        )

        # one chunk per doc for MVP
        chunk_id = f"{doc_id}_c000"
        graph.upsert_chunk_nodes(
            doc_id=doc_id,
            chunk_ids=[chunk_id],
            chunk_props={
                chunk_id: {
                    "text": desc,
                    "heading_path": "description",
                }
            },
        )

        # tags from data.json keywords
        keywords = d.get("keywords", []) or []
        if isinstance(keywords, list):
            graph.upsert_tags(chunk_id, [str(x) for x in keywords])

        # LLM annotation -> entities/relationships + extra tags
        ann = llm.annotate_chunk(
            Chunk(chunk_id=chunk_id, doc_id=doc_id, chunk_index=0, text=desc)
        )
        graph.upsert_entities(chunk_id, ann.entities)
        graph.upsert_entity_relationships(ann.relationships)
        graph.upsert_tags(chunk_id, ann.tags)
        logger.info(
            "  OK chunk=%s tags=%s entities=%s rels=%s extra_tags=%s",
            chunk_id,
            len(keywords) if isinstance(keywords, list) else 0,
            len(ann.entities),
            len(ann.relationships),
            len(ann.tags),
        )


def main() -> None:
    _print_banner(
        "Neo4j GraphRAG Builder",
        [
            "Extracts entities, relationships, and creates knowledge graph from documents",
            "Uses local LM Studio for entity extraction",
        ],
    )
    neo4j_cfg = Neo4jConfig(
        uri=os.environ.get("NEO4J_URI", "neo4j://localhost:7687"),
        username=os.environ.get("NEO4J_USER", "your_username_here"),  # replace with your username
        password=os.environ.get("NEO4J_PASSWORD", "your_password_here"),  # replace with your password
    )

    lm_cfg = LMStudioConfig(
        base_url=os.environ.get("LMSTUDIO_URL", "http://localhost:1234"),
        model=os.environ.get("LMSTUDIO_MODEL", "meta-llama-3.1-8b-instruct"),
    )

    client = Neo4jClient(neo4j_cfg)
    client.connect()
    logger.info("Connected to Neo4j at %s", neo4j_cfg.uri)
    logger.info("LM Studio: %s | model=%s", lm_cfg.base_url, lm_cfg.model)

    try:
        graph = GraphRag(client)
        graph.allowed_relationship_types = {"RELATED_TO", "USES", "REQUIRES", "PART_OF"}
        llm = LMStudioClient(lm_cfg)

        # Ingest once (comment out if already ingested)
        ingest_data_json(client, graph, llm, DATA_JSON)
        _print_graph_summary(client)

        agent = GraphRagQAAgent(client, graph, llm, default_hops=2, seed_limit=8, expansion_limit=50)

        _print_banner(
            "GraphRAG Agent using LM Studio",
            ["Local-first RAG agent that queries Neo4j knowledge graph"],
        )
        _print_commands()
        query_count = 0
        while True:
            q = input("\nYou> ").strip()
            if not q:
                continue
            q_lower = q.lower()
            if q_lower in {"exit", "quit"}:
                break
            if q_lower in {"help", "?"}:
                _print_commands()
                continue
            if q_lower == "stats":
                _print_graph_summary(client)
                continue
            if q_lower == "clear":
                logger.info("Chat history cleared (stateless in this demo).")
                continue
            if q_lower.startswith("docs "):
                topic = q[5:].strip()
                if not topic:
                    logger.info("Usage: docs <topic>")
                    continue
                rows = _search_documents(client, topic)
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
                matches = _search_entities(client, term)
                if not matches:
                    logger.info("No entities found for '%s'", term)
                    continue
                if len(matches) > 1 and all(m.get("name") != term for m in matches):
                    logger.info("Multiple matches found, try exact name:")
                    for m in matches[:10]:
                        logger.info("  - %s [%s]", m.get("name"), m.get("type"))
                    continue
                name = term if any(m.get("name") == term for m in matches) else matches[0].get("name")
                ctx = _entity_context(client, name)
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
                path = _find_entity_path(client, parts[0], parts[1])
                if not path or path.get("distance") is None:
                    logger.info("No path found between '%s' and '%s'", parts[0], parts[1])
                    continue
                logger.info("Path distance: %s", path.get("distance"))
                logger.info("Path: %s", " -> ".join(path.get("path_nodes") or []))
                logger.info("Relations: %s", " | ".join(path.get("relations") or []))
                continue

            query_count += 1
            logger.info("Query #%s: %s", query_count, q)
            res = agent.answer(q)
            print("\nAssistant>\n", res.answer)

            if res.citations:
                print("\nCitations:")
                for c in res.citations:
                    print(f"- {c.title} :: doc_id={c.doc_id} chunk_id={c.chunk_id}")

            # debug is useful while iterating retrieval quality
            # print("\nDEBUG:", res.debug)

    finally:
        client.close()


if __name__ == "__main__":
    main()
