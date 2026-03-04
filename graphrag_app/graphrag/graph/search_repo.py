from __future__ import annotations

import re
from typing import Any, Dict, List

from graphrag.graph.schema_repo import GraphSchemaRepository
from graphrag.storage.neo4j_client import Neo4jClient


class GraphSearchRepository:
    """Read/search operations for graph and vector retrieval."""

    _QUERY_STOPWORDS = {
        "the",
        "and",
        "or",
        "with",
        "from",
        "into",
        "about",
        "what",
        "which",
        "where",
        "when",
        "how",
        "что",
        "это",
        "как",
        "или",
        "про",
        "для",
        "все",
        "всё",
        "now",
        "today",
        "latest",
        "current",
    }

    def __init__(self, neo4j: Neo4jClient):
        self._neo4j = neo4j

    @classmethod
    def extract_query_terms(cls, query: str, *, max_terms: int = 8) -> List[str]:
        tokens = re.findall(r"[\w-]+", (query or "").lower())
        out: List[str] = []
        seen: set[str] = set()
        for token in tokens:
            if len(token) < 3:
                continue
            if token in cls._QUERY_STOPWORDS:
                continue
            if token in seen:
                continue
            seen.add(token)
            out.append(token)
            if len(out) >= max_terms:
                break
        return out

    def vector_search_chunks(
        self,
        query_embedding: List[float],
        *,
        top_k: int = 8,
        index_name: str = "chunk_embedding_index",
        include_doc_url: bool = False,
    ) -> List[Dict[str, Any]]:
        if not query_embedding:
            return []

        idx_name = GraphSchemaRepository.validate_index_name(index_name)
        k = max(1, int(top_k))
        base = f"""
        CALL db.index.vector.queryNodes('{idx_name}', $top_k, $embedding)
        YIELD node, score
        WHERE coalesce(node.active, true)
        OPTIONAL MATCH (d:Document)-[:CONTAINS]->(node)
        RETURN node.chunk_id AS chunk_id,
               node.text AS text,
               node.doc_id AS doc_id,
               d.doc_id AS document_id,
               d.title AS title,
               score AS score
        """
        if include_doc_url:
            base = base.rstrip() + ",\n       d.url AS url\n"
        cypher = base + "\nORDER BY score DESC\nLIMIT $top_k"

        return self._neo4j.run(
            cypher,
            {"top_k": k, "embedding": [float(x) for x in query_embedding]},
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 12,
        include_doc_url: bool = False,
    ) -> List[Dict[str, Any]]:
        q = (query or "").strip()
        if not q:
            return []

        terms = self.extract_query_terms(q)
        if not terms:
            terms = [q.lower()]

        k = max(1, int(limit))
        cypher = """
        MATCH (c:Chunk)
        WHERE coalesce(c.active, true)
        OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity)
        OPTIONAL MATCH (c)-[:HAS_TAG]->(t:Tag)
        WITH c,
             toLower(coalesce(c.text, "")) AS ctext,
             collect(DISTINCT toLower(coalesce(e.name, ""))) AS entity_names,
             collect(DISTINCT toLower(coalesce(t.name, ""))) AS tag_names
        WITH c,
             ctext,
             entity_names,
             tag_names,
             size([term IN $terms WHERE ctext CONTAINS term]) AS text_hits,
             size([term IN $terms WHERE any(name IN entity_names WHERE name CONTAINS term OR term CONTAINS name)]) AS entity_hits,
             size([term IN $terms WHERE any(name IN tag_names WHERE name CONTAINS term OR term CONTAINS name)]) AS tag_hits
        WITH c, text_hits, entity_hits, tag_hits,
             (3.0 * text_hits + 2.0 * entity_hits + 1.0 * tag_hits) AS score
        WHERE score > 0
        OPTIONAL MATCH (d:Document)-[:CONTAINS]->(c)
        RETURN c.chunk_id AS chunk_id,
               c.text AS text,
               c.doc_id AS doc_id,
               d.doc_id AS document_id,
               d.title AS title,
               score AS score
        ORDER BY score DESC, c.chunk_index ASC
        LIMIT $limit
        """
        if include_doc_url:
            cypher = cypher.replace(
                "score AS score",
                "score AS score, d.url AS url",
            )
        return self._neo4j.run(
            cypher,
            {"terms": terms, "limit": k},
        )
