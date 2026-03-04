from __future__ import annotations

from typing import Any, Dict, List

from neo4j.graph import Node, Relationship

from graphrag.storage.neo4j_client import Neo4jClient


class GraphContextRepository:
    """Neighborhood expansion operations for GraphRAG context assembly."""

    def __init__(self, neo4j: Neo4jClient):
        self._neo4j = neo4j

    @staticmethod
    def _node_to_dict(node: Node) -> Dict[str, Any]:
        return {
            "id": node.id,
            "labels": list(node.labels),
            "properties": dict(node),
        }

    @staticmethod
    def _rel_to_dict(rel: Relationship) -> Dict[str, Any]:
        return {
            "id": rel.id,
            "type": rel.type,
            "start": rel.start_node.id,
            "end": rel.end_node.id,
            "properties": dict(rel),
        }

    @staticmethod
    def _dedupe_nodes(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: set[int] = set()
        unique: List[Dict[str, Any]] = []
        for node in nodes:
            node_id = node.get("id")
            if node_id is None or node_id in seen:
                continue
            seen.add(node_id)
            unique.append(node)
        return unique

    @staticmethod
    def _dedupe_edges(edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: set[int] = set()
        unique: List[Dict[str, Any]] = []
        for edge in edges:
            edge_id = edge.get("id")
            if edge_id is None or edge_id in seen:
                continue
            seen.add(edge_id)
            unique.append(edge)
        return unique

    def expand_from_seeds(
        self,
        seed_chunk_ids: List[str],
        hops: int = 2,
        limit: int = 200,
        include_faq: bool = True,
        include_doc_url: bool = False,
    ) -> Dict[str, Any]:
        seed_ids = [cid for cid in seed_chunk_ids if cid]
        if not seed_ids:
            return {"nodes": [], "edges": [], "chunks": [], "seed_chunk_ids": []}

        hops_n = max(1, int(hops))
        rows = self._neo4j.run(
            f"""
            MATCH (seed:Chunk)
            WHERE seed.chunk_id IN $seed_ids
            OPTIONAL MATCH p = (seed)-[*1..{hops_n}]-(n)
            WITH collect(DISTINCT seed) AS seeds, collect(DISTINCT p) AS paths
            WITH seeds,
                 [n IN seeds + reduce(acc = [], p IN paths | acc + nodes(p)) | n] AS nodes,
                 reduce(relAcc = [], p IN paths | relAcc + relationships(p)) AS rels
            RETURN nodes[0..$limit] AS nodes, rels AS rels
            """,
            {"seed_ids": seed_ids, "limit": max(1, limit)},
            raw=True,
        )

        if not rows:
            return {"nodes": [], "edges": [], "chunks": [], "seed_chunk_ids": seed_ids}

        record = rows[0]
        nodes_raw: List[Node] = record.get("nodes") or []
        rels_raw: List[Relationship] = record.get("rels") or []

        nodes = self._dedupe_nodes([self._node_to_dict(n) for n in nodes_raw])
        edges = self._dedupe_edges([self._rel_to_dict(r) for r in rels_raw])

        if not include_faq:
            nodes = [n for n in nodes if "FAQ" not in n.get("labels", [])]

        node_ids = {n["id"] for n in nodes}
        edges = [e for e in edges if e.get("start") in node_ids and e.get("end") in node_ids]

        chunk_ids: List[str] = []
        for node in nodes:
            if "Chunk" in node.get("labels", []):
                chunk_id = node.get("properties", {}).get("chunk_id")
                if chunk_id:
                    chunk_ids.append(chunk_id)

        chunks: List[Dict[str, Any]] = []
        if chunk_ids:
            if include_doc_url:
                chunk_query = """
                MATCH (c:Chunk)
                WHERE c.chunk_id IN $chunk_ids
                OPTIONAL MATCH (d:Document)-[:CONTAINS]->(c)
                RETURN c.chunk_id AS chunk_id,
                       c.text AS text,
                       c.doc_id AS doc_id,
                       d.doc_id AS document_id,
                       d.title AS title,
                       d.url AS url
                """
            else:
                chunk_query = """
                MATCH (c:Chunk)
                WHERE c.chunk_id IN $chunk_ids
                OPTIONAL MATCH (d:Document)-[:CONTAINS]->(c)
                RETURN c.chunk_id AS chunk_id,
                       c.text AS text,
                       c.doc_id AS doc_id,
                       d.doc_id AS document_id,
                       d.title AS title
                """
            chunks = self._neo4j.run(chunk_query, {"chunk_ids": chunk_ids})

        return {
            "nodes": nodes,
            "edges": edges,
            "chunks": chunks,
            "seed_chunk_ids": seed_ids,
        }
