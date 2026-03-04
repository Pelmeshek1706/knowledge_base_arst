from __future__ import annotations

import re
from typing import Optional

from graphrag.storage.neo4j_client import Neo4jClient


class GraphSchemaRepository:
    """Schema and index management for GraphRAG Neo4j data."""

    _VECTOR_INDEX_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def __init__(self, neo4j: Neo4jClient):
        self._neo4j = neo4j

    def setup_graph_schema(self) -> None:
        self._neo4j.execute_write(
            """
            CREATE CONSTRAINT document_doc_id IF NOT EXISTS
            FOR (d:Document)
            REQUIRE d.doc_id IS UNIQUE
            """
        )
        self._neo4j.execute_write(
            """
            CREATE CONSTRAINT chunk_chunk_id IF NOT EXISTS
            FOR (c:Chunk)
            REQUIRE c.chunk_id IS UNIQUE
            """
        )
        self._neo4j.execute_write(
            """
            CREATE CONSTRAINT faq_faq_id IF NOT EXISTS
            FOR (f:FAQ)
            REQUIRE f.faq_id IS UNIQUE
            """
        )
        self._neo4j.execute_write(
            """
            CREATE CONSTRAINT tag_name IF NOT EXISTS
            FOR (t:Tag)
            REQUIRE t.name IS UNIQUE
            """
        )
        self._neo4j.execute_write(
            """
            CREATE CONSTRAINT entity_name_type IF NOT EXISTS
            FOR (e:Entity)
            REQUIRE (e.name, e.type) IS UNIQUE
            """
        )

    @classmethod
    def validate_index_name(cls, index_name: str) -> str:
        cleaned = (index_name or "").strip()
        if not cleaned or not cls._VECTOR_INDEX_NAME_RE.match(cleaned):
            raise ValueError(
                "Invalid vector index name. Use letters, digits and underscore; must not start with a digit."
            )
        return cleaned

    def setup_chunk_vector_index(
        self,
        *,
        dimensions: int,
        index_name: str = "chunk_embedding_index",
        similarity_function: str = "cosine",
    ) -> None:
        dims = int(dimensions)
        if dims <= 0:
            raise ValueError("dimensions must be > 0")

        similarity = (similarity_function or "cosine").strip().lower()
        if similarity not in {"cosine", "euclidean"}:
            raise ValueError("similarity_function must be one of: cosine, euclidean")

        idx_name = self.validate_index_name(index_name)
        cypher = f"""
        CREATE VECTOR INDEX {idx_name} IF NOT EXISTS
        FOR (c:Chunk) ON (c.embedding)
        OPTIONS {{
          indexConfig: {{
            `vector.dimensions`: {dims},
            `vector.similarity_function`: '{similarity}'
          }}
        }}
        """
        self._neo4j.execute_write(cypher)

    def get_chunk_embedding_dimension(self) -> Optional[int]:
        rows = self._neo4j.run(
            """
            MATCH (c:Chunk)
            WHERE c.embedding IS NOT NULL
            RETURN size(c.embedding) AS dim
            LIMIT 1
            """
        )
        if not rows:
            return None
        dim = rows[0].get("dim")
        return int(dim) if dim is not None else None
