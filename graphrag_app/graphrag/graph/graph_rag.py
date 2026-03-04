from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from graphrag.graph.context_repo import GraphContextRepository
from graphrag.graph.schema_repo import GraphSchemaRepository
from graphrag.graph.search_repo import GraphSearchRepository
from graphrag.graph.write_repo import GraphWriteRepository
from graphrag.storage.neo4j_client import Neo4jClient
from graphrag.types.models import Entity, FAQEntry


class GraphRag:
    """
    GraphRAG facade that preserves the original public API while delegating
    responsibilities to focused repositories.
    """

    def __init__(self, neo4j: Neo4jClient):
        self._neo4j = neo4j
        self.schema_repo = GraphSchemaRepository(neo4j)
        self.write_repo = GraphWriteRepository(neo4j)
        self.search_repo = GraphSearchRepository(neo4j)
        self.context_repo = GraphContextRepository(neo4j)

    @property
    def allowed_relationship_types(self) -> set[str]:
        return set(self.write_repo.allowed_relationship_types)

    @allowed_relationship_types.setter
    def allowed_relationship_types(self, values: set[str]) -> None:
        self.write_repo.allowed_relationship_types = set(values)

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def setup_graph_schema(self) -> None:
        self.schema_repo.setup_graph_schema()

    def setup_chunk_vector_index(
        self,
        *,
        dimensions: int,
        index_name: str = "chunk_embedding_index",
        similarity_function: str = "cosine",
    ) -> None:
        self.schema_repo.setup_chunk_vector_index(
            dimensions=dimensions,
            index_name=index_name,
            similarity_function=similarity_function,
        )

    def get_chunk_embedding_dimension(self) -> Optional[int]:
        return self.schema_repo.get_chunk_embedding_dimension()

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def vector_search_chunks(
        self,
        query_embedding: List[float],
        *,
        top_k: int = 8,
        index_name: str = "chunk_embedding_index",
        include_doc_url: bool = False,
    ) -> List[Dict[str, Any]]:
        return self.search_repo.vector_search_chunks(
            query_embedding,
            top_k=top_k,
            index_name=index_name,
            include_doc_url=include_doc_url,
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 12,
        include_doc_url: bool = False,
    ) -> List[Dict[str, Any]]:
        return self.search_repo.search(
            query,
            limit=limit,
            include_doc_url=include_doc_url,
        )

    def expand_from_seeds(
        self,
        seed_chunk_ids: List[str],
        hops: int = 2,
        limit: int = 200,
        include_faq: bool = True,
        include_doc_url: bool = False,
    ) -> Dict[str, Any]:
        return self.context_repo.expand_from_seeds(
            seed_chunk_ids,
            hops=hops,
            limit=limit,
            include_faq=include_faq,
            include_doc_url=include_doc_url,
        )

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def upsert_chunk_embeddings(
        self,
        chunk_embeddings: Dict[str, List[float]],
        *,
        embedding_model: str,
    ) -> None:
        self.write_repo.upsert_chunk_embeddings(chunk_embeddings, embedding_model=embedding_model)

    def upsert_document(self, doc_id: str, title: str, source_type: str, source_id: str, **meta: Any) -> None:
        self.write_repo.upsert_document(doc_id, title, source_type, source_id, **meta)

    def upsert_chunk_nodes(self, doc_id: str, chunk_ids: List[str], **meta: Any) -> None:
        self.write_repo.upsert_chunk_nodes(doc_id, chunk_ids, **meta)

    def upsert_tags(self, chunk_id: str, tags: List[str]) -> None:
        self.write_repo.upsert_tags(chunk_id, tags)

    def upsert_entities(self, chunk_id: str, entities: List[Entity]) -> None:
        self.write_repo.upsert_entities(chunk_id, entities)

    def upsert_entity_relationships(self, relationships: List[Dict[str, str]]) -> None:
        self.write_repo.upsert_entity_relationships(relationships)

    def link_document_refs(self, doc_id: str, referenced_doc_ids: List[str]) -> None:
        self.write_repo.link_document_refs(doc_id, referenced_doc_ids)

    def link_similarities(self, from_label: str, edges: List[Tuple[str, str, float]]) -> None:
        self.write_repo.link_similarities(from_label, edges)

    def upsert_faq_node(self, faq: FAQEntry) -> None:
        self.write_repo.upsert_faq_node(faq)

    def link_faq(self, faq_id: str, chunk_ids: List[str], tags: List[str], entities: List[Entity]) -> None:
        self.write_repo.link_faq(faq_id, chunk_ids, tags, entities)

    def soft_delete_document(self, doc_id: str) -> None:
        self.write_repo.soft_delete_document(doc_id)
