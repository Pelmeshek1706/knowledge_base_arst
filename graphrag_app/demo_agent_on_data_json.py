from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from collections import deque
from pathlib import Path
from typing import Any, Dict, List
from zipfile import ZipFile, BadZipFile
import xml.etree.ElementTree as ET

from graphrag.config import Neo4jConfig
from graphrag.storage.neo4j_client import Neo4jClient
from graphrag.graph.graph_rag import GraphRag
from graphrag.llm.lm_studio import LMStudioClient, LMStudioConfig, ChunkSplitConfig
from graphrag.orchestrator import ToolOrchestratedAgent, ToolAgentResult
from graphrag.types.models import Chunk, ChunkAnnotation, Entity
from graphrag.tools import (
    AgentToolRegistry,
    DockerMcpToolProvider,
    GraphRagToolProvider,
    ToolCallResult,
    ToolExecutionError,
)

DATA_JSON = os.environ.get("DATA_JSON", "/Users/pelmeshek1706/Desktop/projects/knowledge_agent/data/data.json")  # adjust for your machine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TRACE_MAX_CHUNKS = 8
TRACE_MAX_NODES = 25
TRACE_MAX_EDGES = 25
TRACE_MAX_ENTITIES = 20
TRACE_MAX_TAGS = 30

PROCESSED_DOCS_DIR = Path(os.environ.get("PROCESSED_DOCS_DIR", "processed_docs"))
CACHE_FILE = PROCESSED_DOCS_DIR / "llm_annotations.json"


_DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _read_docx_text(path: Path) -> str:
    try:
        with ZipFile(path) as zf:
            xml_bytes = zf.read("word/document.xml")
    except (KeyError, BadZipFile) as exc:
        raise RuntimeError(f"Invalid DOCX: {path}") from exc

    root = ET.fromstring(xml_bytes)
    paragraphs: List[str] = []
    for p in root.findall(".//w:p", _DOCX_NS):
        buf: List[str] = []
        for node in p.iter():
            tag = node.tag
            if tag.endswith("}t") and node.text:
                buf.append(node.text)
            elif tag.endswith("}tab"):
                buf.append("\t")
            elif tag.endswith("}br") or tag.endswith("}cr"):
                buf.append("\n")
        line = "".join(buf).strip()
        if line:
            paragraphs.append(line)
    return "\n".join(paragraphs)


def _read_rtf_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    # Very simple RTF cleanup; good enough for basic extraction.
    text = re.sub(r"{\\\*?\\[^{}]+}", " ", raw)
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", text)
    text = re.sub(r"[{}]", " ", text)
    return " ".join(text.split())


def _read_document_text(path: Path) -> str:
    if not path.exists():
        logger.warning("File not found: %s", path)
        return ""

    suffix = path.suffix.lower()
    try:
        if suffix == ".docx":
            return _read_docx_text(path)
        if suffix == ".rtf":
            return _read_rtf_text(path)
        if suffix in {".txt", ".md"}:
            return _read_text_file(path)
    except Exception as exc:
        logger.warning("Failed to read %s: %s", path, exc)
        return ""

    logger.warning("Unsupported file type %s for %s", suffix, path)
    return ""


def _hash_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()


def _load_annotation_cache(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"version": 1, "docs": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("cache is not an object")
        if "docs" not in data or not isinstance(data.get("docs"), dict):
            data["docs"] = {}
        data.setdefault("version", 1)
        return data
    except Exception as exc:
        logger.warning("Failed to load cache %s: %s", path, exc)
        return {"version": 1, "docs": {}}


def _save_annotation_cache(path: Path, cache: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(cache, indent=2, ensure_ascii=True), encoding="utf-8")
    tmp_path.replace(path)


def _chunk_cfg_signature(cfg: ChunkSplitConfig) -> Dict[str, Any]:
    return {
        "mode": cfg.mode,
        "chunk_size": cfg.chunk_size,
        "chunk_overlap": cfg.chunk_overlap,
        "separators": cfg.separators or [],
        "encoding_name": cfg.encoding_name,
    }


def _cache_key(file_path: str | None, doc_id: str) -> str:
    return file_path or doc_id


def _annotation_to_dict(ann: ChunkAnnotation) -> Dict[str, Any]:
    return {
        "chunk_type": ann.chunk_type,
        "summary": ann.summary,
        "entities": [{"name": e.name, "type": e.type} for e in ann.entities],
        "relationships": ann.relationships,
        "tags": ann.tags,
        "candidate_qas": ann.candidate_qas,
    }


def _annotation_from_dict(data: Dict[str, Any]) -> ChunkAnnotation:
    entities: List[Entity] = []
    for e in data.get("entities", []) or []:
        if isinstance(e, dict):
            name = str(e.get("name", "")).strip()
            etype = str(e.get("type", "OTHER")).strip().upper()
            if name:
                entities.append(Entity(name=name, type=etype))
    relationships = [r for r in (data.get("relationships", []) or []) if isinstance(r, dict)]
    tags = [t for t in (data.get("tags", []) or []) if isinstance(t, str)]
    cqa = [q for q in (data.get("candidate_qas", []) or []) if isinstance(q, dict)]
    return ChunkAnnotation(
        chunk_type=str(data.get("chunk_type", "other")).strip(),
        summary=str(data.get("summary", "")).strip() if data.get("summary") is not None else None,
        entities=entities,
        relationships=relationships,
        tags=tags,
        candidate_qas=cqa,
    )


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
    logger.info("  tools                - Show available tools (GraphRAG + MCP)")
    logger.info("  web <query>          - Run web-search tool directly")
    logger.info("  tool <name> <json>   - Call any tool directly")
    logger.info("  docs <topic>         - Search documents")
    logger.info("  entity <name>        - Show entity context")
    logger.info("  find <e1> <e2>        - Find path between entities")
    logger.info("  trace [on|off]       - Toggle retrieval trace output")
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


def _shorten_text(text: str, limit: int = 220) -> str:
    cleaned = " ".join((text or "").strip().split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(0, limit - 3)] + "..."


def _choose_web_search_tool(tool_names: List[str]) -> str | None:
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
            if (n.lower().endswith("search") or n == "search")
            and n.lower() not in {"graph_search"}
        ]
    )
    if generic:
        return generic[0]
    return None


def _tool_output_to_text(value: Any, *, max_chars: int = 5000) -> str:
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


def _build_tool_registry(graph: GraphRag) -> tuple[AgentToolRegistry, str | None]:
    providers = [GraphRagToolProvider(graph)]
    web_search_tool: str | None = None

    if _env_bool("ENABLE_MCP_TOOLS", True):
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
            web_search_tool = _choose_web_search_tool(names)
    else:
        logger.info("No tools discovered.")

    return registry, web_search_tool


def _call_web_search(
    registry: AgentToolRegistry,
    search_tool_name: str,
    query: str,
) -> ToolCallResult:
    max_results = int(os.environ.get("MCP_WEB_MAX_RESULTS", "5"))
    return registry.call_tool(
        search_tool_name,
        {"query": query, "max_results": max_results},
    )


def _print_tool_agent_trace(result: ToolAgentResult) -> None:
    planned = result.planned_calls
    executed = result.executed_results
    logger.info("=" * 40)
    logger.info("TOOL TRACE")
    logger.info("=" * 40)
    if not planned:
        logger.info("Planner produced no tool calls.")
    else:
        logger.info("Planned calls:")
        for call in planned:
            logger.info("  - %s args=%s", call.tool_name, call.arguments)
    if not executed:
        logger.info("No tool calls executed successfully.")
    else:
        logger.info("Executed calls:")
        for item in executed:
            logger.info("  - %s provider=%s", item.tool_name, item.provider)


def _node_label(node: Dict[str, Any]) -> str:
    labels = node.get("labels") or []
    props = node.get("properties") or {}

    if "Entity" in labels:
        name = props.get("name") or "?"
        return f"Entity({name})"
    if "Chunk" in labels:
        chunk_id = props.get("chunk_id") or "?"
        return f"Chunk({chunk_id})"
    if "Document" in labels:
        title = props.get("title") or props.get("doc_id") or "Document"
        return f"Document({_shorten_text(str(title), 40)})"
    if "Tag" in labels:
        name = props.get("name") or "?"
        return f"Tag({name})"
    if "FAQ" in labels:
        faq_id = props.get("faq_id") or "?"
        return f"FAQ({faq_id})"
    if labels:
        return f"{labels[0]}(id={node.get('id')})"
    return f"Node(id={node.get('id')})"


def _node_detail(node: Dict[str, Any]) -> str:
    labels = node.get("labels") or []
    props = node.get("properties") or {}
    if "Entity" in labels:
        return f"Entity name={props.get('name')} type={props.get('type')}"
    if "Chunk" in labels:
        return f"Chunk chunk_id={props.get('chunk_id')} doc_id={props.get('doc_id')}"
    if "Document" in labels:
        title = _shorten_text(str(props.get("title") or ""), 60)
        return f"Document doc_id={props.get('doc_id')} title={title}"
    if "Tag" in labels:
        return f"Tag name={props.get('name')}"
    if "FAQ" in labels:
        q = _shorten_text(str(props.get("question") or ""), 60)
        return f"FAQ faq_id={props.get('faq_id')} q={q}"
    return f"Node labels={labels} props={props}"


def _pick_keyword_node(nodes: List[Dict[str, Any]], term: str) -> Dict[str, Any] | None:
    term_l = term.strip().lower()
    if not term_l:
        return None

    candidates: List[tuple[int, int, int, str, Dict[str, Any]]] = []
    for node in nodes:
        labels = node.get("labels") or []
        if "Entity" not in labels and "Tag" not in labels:
            continue
        props = node.get("properties") or {}
        name = props.get("name")
        if not name:
            continue
        name_str = str(name)
        name_l = name_str.lower()
        if name_l == term_l:
            match_rank = 0
        elif term_l in name_l:
            match_rank = 1
        else:
            continue
        label_rank = 0 if "Entity" in labels else 1
        candidates.append((match_rank, label_rank, len(name_l), name_l, node))

    if not candidates:
        return None
    candidates.sort()
    return candidates[0][4]


def _shortest_path(adj: Dict[int, List[int]], start: int, goal: int) -> List[int]:
    if start == goal:
        return [start]
    queue: deque[int] = deque([start])
    prev: Dict[int, int | None] = {start: None}
    while queue:
        cur = queue.popleft()
        for nxt in adj.get(cur, []):
            if nxt in prev:
                continue
            prev[nxt] = cur
            if nxt == goal:
                queue.clear()
                break
            queue.append(nxt)
    if goal not in prev:
        return []
    path: List[int] = []
    node = goal
    while node is not None:
        path.append(node)
        node = prev[node]
    return list(reversed(path))


def _build_keyword_path(debug: Dict[str, Any]) -> Dict[str, Any] | None:
    terms = debug.get("terms") or []
    graph_ctx = debug.get("graph_context") or {}
    nodes = graph_ctx.get("nodes") or []
    edges = graph_ctx.get("edges") or []
    if not terms or not nodes:
        return None

    if len(terms) == 1:
        node = _pick_keyword_node(nodes, terms[0])
        if not node:
            return {"path": [], "missing_terms": [terms[0]]}
        props = node.get("properties") or {}
        name = props.get("name")
        return {"path": [str(name)] if name else [], "missing_terms": []}

    if not edges:
        return {"path": [], "missing_terms": terms}

    node_by_id = {n.get("id"): n for n in nodes if n.get("id") is not None}
    adj: Dict[int, List[int]] = {}
    for e in edges:
        start = e.get("start")
        end = e.get("end")
        if start is None or end is None:
            continue
        adj.setdefault(start, []).append(end)
        adj.setdefault(end, []).append(start)

    term_nodes: List[Dict[str, Any]] = []
    missing_terms: List[str] = []
    for term in terms:
        node = _pick_keyword_node(nodes, term)
        if node:
            term_nodes.append(node)
        else:
            missing_terms.append(term)

    if len(term_nodes) < 2:
        return {"path": [], "missing_terms": missing_terms}

    total_path: List[int] = []
    current_id = term_nodes[0].get("id")
    if current_id is None:
        return {"path": [], "missing_terms": missing_terms}
    total_path.append(current_id)

    for node in term_nodes[1:]:
        target_id = node.get("id")
        if target_id is None:
            continue
        segment = _shortest_path(adj, current_id, target_id)
        if not segment:
            return {"path": [], "missing_terms": missing_terms}
        total_path.extend(segment[1:])
        current_id = target_id

    keywords: List[str] = []
    for node_id in total_path:
        node = node_by_id.get(node_id)
        if not node:
            continue
        labels = node.get("labels") or []
        if "Entity" not in labels and "Tag" not in labels:
            continue
        props = node.get("properties") or {}
        name = props.get("name")
        if not name:
            continue
        name_str = str(name)
        if not keywords or keywords[-1].lower() != name_str.lower():
            keywords.append(name_str)

    return {"path": keywords, "missing_terms": missing_terms}


def _print_trace(debug: Dict[str, Any]) -> None:
    if not debug:
        logger.info("Trace not available.")
        return

    terms = debug.get("terms") or []
    seed_ids = debug.get("seed_chunk_ids") or []
    graph_seed_ids = debug.get("graph_seed_chunk_ids") or []
    vector_seed_ids = debug.get("vector_seed_chunk_ids") or []
    vector_hits = debug.get("vector_hits") or []
    vector_seed_error = debug.get("vector_seed_error")
    reranked_chunks = debug.get("reranked_chunks") or []
    graph_ctx = debug.get("graph_context") or {}

    nodes = graph_ctx.get("nodes") or []
    edges = graph_ctx.get("edges") or []
    docs = graph_ctx.get("documents") or []
    tags = graph_ctx.get("tags") or []
    entities = graph_ctx.get("entities") or []
    faqs = graph_ctx.get("faqs") or []
    seed_chunks = graph_ctx.get("seed_chunks") or []
    neighbor_chunks = graph_ctx.get("neighbor_chunks") or []

    logger.info("=" * 40)
    logger.info("RETRIEVAL TRACE")
    logger.info("=" * 40)
    if terms:
        logger.info("Query entities: %s", ", ".join(terms))
    if seed_ids:
        logger.info("Seed chunks: %s", ", ".join(seed_ids))
    if vector_seed_ids:
        logger.info("Vector seed chunks: %s", ", ".join(vector_seed_ids))
    if graph_seed_ids:
        logger.info("Graph seed chunks: %s", ", ".join(graph_seed_ids))
    if vector_seed_error:
        logger.info("Vector seed error: %s", vector_seed_error)
    if vector_hits:
        logger.info("Vector hits:")
        for hit in vector_hits[:8]:
            logger.info(
                "  - %s score=%.4f title=%s",
                hit.get("chunk_id"),
                float(hit.get("score", 0.0)),
                hit.get("title") or "<untitled>",
            )
    if reranked_chunks:
        logger.info("Top reranked chunks:")
        for item in reranked_chunks[:8]:
            logger.info(
                "  - %s score=%.4f source=%s v=%s g=%s t=%s",
                item.get("chunk_id"),
                float(item.get("retrieval_score", 0.0)),
                item.get("source"),
                item.get("vector"),
                item.get("graph"),
                item.get("term"),
            )

    path_info = _build_keyword_path(debug)
    if path_info:
        path = path_info.get("path") or []
        missing = path_info.get("missing_terms") or []
        if path:
            logger.info("Found text by this path -> %s", " -> ".join(path))
            if missing:
                logger.info("Path missing terms: %s", ", ".join(missing))
        elif missing:
            logger.info("Keyword path missing nodes for: %s", ", ".join(missing))
        else:
            logger.info("Keyword path not found in retrieved graph.")

    if docs:
        logger.info("Documents:")
        for d in docs[:10]:
            logger.info("  - %s (doc_id=%s)", d.get("title") or "<untitled>", d.get("doc_id"))

    if entities:
        entity_list = [f"{e.get('name')}[{e.get('type')}]" for e in entities[:TRACE_MAX_ENTITIES]]
        logger.info("Entities: %s", ", ".join(entity_list))
        if len(entities) > TRACE_MAX_ENTITIES:
            logger.info("  ... +%s more", len(entities) - TRACE_MAX_ENTITIES)

    if tags:
        logger.info("Tags: %s", ", ".join(tags[:TRACE_MAX_TAGS]))
        if len(tags) > TRACE_MAX_TAGS:
            logger.info("  ... +%s more", len(tags) - TRACE_MAX_TAGS)

    if faqs:
        logger.info("FAQ nodes: %s", len(faqs))

    if seed_chunks:
        logger.info("Seed chunk context (%s):", len(seed_chunks))
        for c in seed_chunks[:TRACE_MAX_CHUNKS]:
            snippet = _shorten_text(c.get("text") or "")
            score = c.get("retrieval_score")
            score_part = f" (score={float(score):.4f})" if score is not None else ""
            logger.info(
                "  - %s%s :: %s",
                c.get("chunk_id"),
                score_part,
                snippet,
            )
        if len(seed_chunks) > TRACE_MAX_CHUNKS:
            logger.info("  ... +%s more", len(seed_chunks) - TRACE_MAX_CHUNKS)

    if neighbor_chunks:
        logger.info("Neighbor chunk context (%s):", len(neighbor_chunks))
        for c in neighbor_chunks[:TRACE_MAX_CHUNKS]:
            snippet = _shorten_text(c.get("text") or "")
            score = c.get("retrieval_score")
            score_part = f" (score={float(score):.4f})" if score is not None else ""
            logger.info(
                "  - %s%s :: %s",
                c.get("chunk_id"),
                score_part,
                snippet,
            )
        if len(neighbor_chunks) > TRACE_MAX_CHUNKS:
            logger.info("  ... +%s more", len(neighbor_chunks) - TRACE_MAX_CHUNKS)

    if nodes:
        label_counts: Dict[str, int] = {}
        for n in nodes:
            for label in n.get("labels") or []:
                label_counts[label] = label_counts.get(label, 0) + 1
        label_summary = ", ".join(f"{k}={v}" for k, v in sorted(label_counts.items()))
        logger.info("Graph nodes: %s total%s", len(nodes), f" ({label_summary})" if label_summary else "")
        for n in nodes[:TRACE_MAX_NODES]:
            logger.info("  - %s", _node_detail(n))
        if len(nodes) > TRACE_MAX_NODES:
            logger.info("  ... +%s more", len(nodes) - TRACE_MAX_NODES)

    if edges:
        node_lookup = {n.get("id"): _node_label(n) for n in nodes if n.get("id") is not None}
        logger.info("Graph edges: %s", len(edges))
        for e in edges[:TRACE_MAX_EDGES]:
            start = node_lookup.get(e.get("start"), f"id={e.get('start')}")
            end = node_lookup.get(e.get("end"), f"id={e.get('end')}")
            logger.info("  - %s -[%s]-> %s", start, e.get("type"), end)
        if len(edges) > TRACE_MAX_EDGES:
            logger.info("  ... +%s more", len(edges) - TRACE_MAX_EDGES)


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
    vector_index_name = os.environ.get("NEO4J_VECTOR_INDEX", "chunk_embedding_index")
    vector_similarity = os.environ.get("NEO4J_VECTOR_SIMILARITY", "cosine")
    logger.info(
        "Vector retrieval config: index=%s similarity=%s embedding_model=%s backend=%s",
        vector_index_name,
        vector_similarity,
        llm.embedding_model_id,
        llm.active_embedding_backend,
    )

    vector_index_ready = False
    existing_dim = graph.get_chunk_embedding_dimension()
    if existing_dim:
        try:
            graph.setup_chunk_vector_index(
                dimensions=existing_dim,
                index_name=vector_index_name,
                similarity_function=vector_similarity,
            )
            vector_index_ready = True
            logger.info("Vector index is ready (existing dim=%s)", existing_dim)
        except Exception as exc:
            logger.warning("Failed to ensure vector index from existing embedding dim: %s", exc)

    base_dir = Path(path).resolve().parent
    chunk_cfg = ChunkSplitConfig(
        mode=os.environ.get("CHUNK_MODE", "context"),
        chunk_size=int(os.environ.get("CHUNK_SIZE", "1200")),
        chunk_overlap=int(os.environ.get("CHUNK_OVERLAP", "200")),
    )
    chunk_cfg_sig = _chunk_cfg_signature(chunk_cfg)
    cache = _load_annotation_cache(CACHE_FILE)
    cache_docs: Dict[str, Any] = cache.get("docs", {})
    cache_dirty = False

    for i, d in enumerate(docs):
        doc_id = f"doc_{i:03d}"
        title = d.get("title", "") or ""
        desc = d.get("description", "") or ""
        source_type = "json"
        source_id = d.get("file_path", f"row_{i}")
        file_path = d.get("file_path")
        resolved_path = None
        if file_path:
            p = Path(file_path)
            resolved_path = p if p.is_absolute() else (base_dir / p)

        logger.info("Processing %s: %s", doc_id, title or "<untitled>")

        graph.upsert_document(
            doc_id=doc_id,
            title=title,
            source_type=source_type,
            source_id=str(source_id),
            file_path=file_path,
            description=desc,
            source_keywords=d.get("keywords", []) or [],
        )

        doc_text = _read_document_text(resolved_path) if resolved_path else ""
        if not doc_text:
            logger.warning("No text extracted for %s; using description as fallback.", doc_id)
            doc_text = desc

        content_hash = _hash_text(doc_text)
        cache_key = _cache_key(str(resolved_path) if resolved_path else file_path, doc_id)
        entry = cache_docs.get(cache_key)
        use_cache = (
            isinstance(entry, dict)
            and entry.get("content_hash") == content_hash
            and entry.get("chunk_cfg") == chunk_cfg_sig
        )
        cached_chunks: Dict[int, Dict[str, Any]] = {}
        if use_cache:
            for c in entry.get("chunks", []) or []:
                idx = c.get("chunk_index")
                if isinstance(idx, int):
                    cached_chunks[idx] = c

        chunks = llm.split_document(doc_id, doc_text, chunk_cfg, heading_path="content")
        if not chunks:
            logger.warning("No chunks produced for %s; skipping.", doc_id)
            continue

        chunk_ids = [c.chunk_id for c in chunks]
        chunk_props = {
            c.chunk_id: {
                "text": c.text,
                "heading_path": c.heading_path or "content",
            }
            for c in chunks
        }
        graph.upsert_chunk_nodes(
            doc_id=doc_id,
            chunk_ids=chunk_ids,
            chunk_props=chunk_props,
        )

        embedded_rows = client.run(
            """
            MATCH (c:Chunk)
            WHERE c.chunk_id IN $chunk_ids
              AND c.embedding IS NOT NULL
              AND c.embedding_model = $embedding_model
            RETURN c.chunk_id AS chunk_id
            """,
            {"chunk_ids": chunk_ids, "embedding_model": llm.embedding_model_id},
        )
        embedded_chunk_ids = {r.get("chunk_id") for r in embedded_rows if r.get("chunk_id")}
        chunks_to_embed = [c for c in chunks if c.chunk_id not in embedded_chunk_ids]
        embedded_now = 0
        if chunks_to_embed:
            try:
                vectors = llm.embed_texts([c.text for c in chunks_to_embed])
                if vectors:
                    if not vector_index_ready:
                        graph.setup_chunk_vector_index(
                            dimensions=len(vectors[0]),
                            index_name=vector_index_name,
                            similarity_function=vector_similarity,
                        )
                        vector_index_ready = True
                    graph.upsert_chunk_embeddings(
                        {
                            chunk.chunk_id: vec
                            for chunk, vec in zip(chunks_to_embed, vectors)
                        },
                        embedding_model=llm.embedding_model_id,
                    )
                    embedded_now = len(vectors)
            except Exception as exc:
                logger.warning(
                    "Embedding failed for %s (%s chunks): %s",
                    doc_id,
                    len(chunks_to_embed),
                    exc,
                )

        # LLM annotation -> entities/relationships + tags per chunk (with cache)
        total_entities = 0
        total_relationships = 0
        total_tags = 0
        updated_chunks: List[Dict[str, Any]] = []
        for chunk in chunks:
            cached = cached_chunks.get(chunk.chunk_index)
            cached_ann = cached.get("annotation") if isinstance(cached, dict) else None
            if cached and cached.get("text_hash") == _hash_text(chunk.text) and isinstance(cached_ann, dict):
                ann = _annotation_from_dict(cached_ann)
            else:
                ann = llm.annotate_chunk(chunk)
                cache_dirty = True
            graph.upsert_entities(chunk.chunk_id, ann.entities)
            graph.upsert_entity_relationships(ann.relationships)
            graph.upsert_tags(chunk.chunk_id, ann.tags)
            total_entities += len(ann.entities)
            total_relationships += len(ann.relationships)
            total_tags += len(ann.tags)
            updated_chunks.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": chunk.chunk_index,
                    "text_hash": _hash_text(chunk.text),
                    "annotation": _annotation_to_dict(ann),
                }
            )
        cache_docs[cache_key] = {
            "doc_id": doc_id,
            "file_path": file_path,
            "content_hash": content_hash,
            "chunk_cfg": chunk_cfg_sig,
            "chunks": updated_chunks,
            "updated_at": int(time.time()),
        }
        logger.info(
            "  OK chunks=%s embedded(new=%s cached=%s model=%s backend=%s) entities=%s rels=%s tags=%s",
            len(chunks),
            embedded_now,
            len(embedded_chunk_ids),
            llm.embedding_model_id,
            llm.active_embedding_backend,
            total_entities,
            total_relationships,
            total_tags,
        )

    if cache_dirty:
        cache["docs"] = cache_docs
        _save_annotation_cache(CACHE_FILE, cache)
        logger.info("Saved LLM cache: %s", CACHE_FILE)


def main() -> None:
    _print_banner(
        "Neo4j GraphRAG Builder",
        [
            "Extracts entities, relationships, and creates knowledge graph from documents",
            "Uses local LM Studio for entity extraction",
        ],
    )
    neo4j_cfg = Neo4jConfig(
        uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        username=os.environ.get("NEO4J_USER", "neo4j"),
        password=os.environ.get("NEO4J_PASSWORD", "airestairest"),
    )

    lm_cfg = LMStudioConfig(
        base_url=os.environ.get("LMSTUDIO_URL", "http://localhost:1234"),
        model=os.environ.get("LMSTUDIO_MODEL", "qwen2.5-1.5b-instruct"),
        embedding_model=os.environ.get("LMSTUDIO_EMBED_MODEL"),
        embedding_fallback=_env_bool("LMSTUDIO_EMBED_FALLBACK", True),
        local_embedding_dimensions=int(os.environ.get("LOCAL_EMBED_DIMENSIONS", "384")),
    )

    client = Neo4jClient(neo4j_cfg)
    client.connect()
    logger.info("Connected to Neo4j at %s", neo4j_cfg.uri)
    logger.info(
        "LM Studio: %s | chat_model=%s | embedding_model=%s | fallback=%s | local_dim=%s",
        lm_cfg.base_url,
        lm_cfg.model,
        lm_cfg.embedding_model or lm_cfg.model,
        lm_cfg.embedding_fallback,
        lm_cfg.local_embedding_dimensions,
    )

    try:
        graph = GraphRag(client)
        graph.allowed_relationship_types = {"RELATED_TO", "USES", "REQUIRES", "PART_OF"}
        llm = LMStudioClient(lm_cfg)
        logger.info(
            "LangSmith tracing: enabled=%s project=%s endpoint=%s",
            getattr(llm, "tracing_enabled", False),
            getattr(llm, "tracing_project", "") or "<unset>",
            os.environ.get("LANGSMITH_ENDPOINT", "<unset>"),
        )

        # Ingest once (comment out if already ingested)
        ingest_data_json(client, graph, llm, DATA_JSON)
        _print_graph_summary(client)

        tool_registry, web_search_tool = _build_tool_registry(graph)
        if web_search_tool:
            logger.info("Web tool selected: %s", web_search_tool)
        else:
            logger.info("No dedicated web-search tool found. Planner will use available tools.")

        planner_tools = ["graph_search"]
        if web_search_tool:
            planner_tools.append(web_search_tool)
        orchestrated_agent = ToolOrchestratedAgent(
            llm,
            tool_registry,
            max_tool_calls=int(os.environ.get("TOOL_AGENT_MAX_CALLS", "2")),
            context_max_chars=int(os.environ.get("TOOL_AGENT_CONTEXT_MAX_CHARS", "12000")),
            allowed_tools=planner_tools,
            max_deep_links=int(os.environ.get("TOOL_AGENT_DEEP_LINKS", "1")),
            max_research_iterations=int(os.environ.get("TOOL_AGENT_RESEARCH_ITERATIONS", "2")),
        )

        _print_banner(
            "GraphRAG Agent using LM Studio",
            ["Local-first RAG agent that queries Neo4j knowledge graph"],
        )
        _print_commands()
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
                _print_commands()
                continue
            if q_lower == "stats":
                _print_graph_summary(client)
                continue
            if q_lower == "tools":
                try:
                    tools = tool_registry.list_tools(refresh=True)
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
                    result = tool_registry.call_tool(tool_name, payload)
                except ToolExecutionError as exc:
                    logger.info("Tool call failed: %s", exc)
                    continue
                text = _tool_output_to_text(result.output)
                logger.info("Tool result (%s):\n%s", result.tool_name, text or "<empty>")
                continue
            if q_lower.startswith("web "):
                if not web_search_tool:
                    logger.info("DuckDuckGo MCP search tool is not configured.")
                    continue
                query = q[4:].strip()
                if not query:
                    logger.info("Usage: web <query>")
                    continue
                try:
                    result = _call_web_search(tool_registry, web_search_tool, query)
                except ToolExecutionError as exc:
                    logger.info("Web search failed: %s", exc)
                    continue
                text = _tool_output_to_text(result.output)
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
            result = orchestrated_agent.answer(q)
            print("\nAssistant>\n", result.answer)
            if trace_enabled:
                _print_tool_agent_trace(result)

    finally:
        client.close()


if __name__ == "__main__":
    main()
