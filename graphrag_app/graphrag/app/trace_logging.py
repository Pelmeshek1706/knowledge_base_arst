from __future__ import annotations

import logging
from collections import deque
from typing import Any, Dict, List

from graphrag.orchestrator import ToolAgentResult

logger = logging.getLogger(__name__)

TRACE_MAX_CHUNKS = 8
TRACE_MAX_NODES = 25
TRACE_MAX_EDGES = 25
TRACE_MAX_ENTITIES = 20
TRACE_MAX_TAGS = 30


def shorten_text(text: str, limit: int = 220) -> str:
    cleaned = " ".join((text or "").strip().split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(0, limit - 3)] + "..."


def print_tool_agent_trace(result: ToolAgentResult) -> None:
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
        return f"Document({shorten_text(str(title), 40)})"
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
        title = shorten_text(str(props.get("title") or ""), 60)
        return f"Document doc_id={props.get('doc_id')} title={title}"
    if "Tag" in labels:
        return f"Tag name={props.get('name')}"
    if "FAQ" in labels:
        q = shorten_text(str(props.get("question") or ""), 60)
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


def build_keyword_path(debug: Dict[str, Any]) -> Dict[str, Any] | None:
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


def print_retrieval_trace(debug: Dict[str, Any]) -> None:
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

    path_info = build_keyword_path(debug)
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
            snippet = shorten_text(c.get("text") or "")
            score = c.get("retrieval_score")
            score_part = f" (score={float(score):.4f})" if score is not None else ""
            logger.info("  - %s%s :: %s", c.get("chunk_id"), score_part, snippet)
        if len(seed_chunks) > TRACE_MAX_CHUNKS:
            logger.info("  ... +%s more", len(seed_chunks) - TRACE_MAX_CHUNKS)

    if neighbor_chunks:
        logger.info("Neighbor chunk context (%s):", len(neighbor_chunks))
        for c in neighbor_chunks[:TRACE_MAX_CHUNKS]:
            snippet = shorten_text(c.get("text") or "")
            score = c.get("retrieval_score")
            score_part = f" (score={float(score):.4f})" if score is not None else ""
            logger.info("  - %s%s :: %s", c.get("chunk_id"), score_part, snippet)
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
