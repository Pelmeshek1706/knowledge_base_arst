from __future__ import annotations

from typing import Any, Dict, List, Tuple

from graphrag.storage.neo4j_client import Neo4jClient
from graphrag.types.models import Entity, FAQEntry


class GraphWriteRepository:
    """Write/upsert operations for GraphRAG nodes and relationships."""

    _DEFAULT_ALLOWED_REL_TYPES = {
        "RELATED_TO",
        "DEPENDS_ON",
        "USES",
        "PART_OF",
        "OWNED_BY",
        "PRODUCES",
        "CONSUMES",
        "CONNECTED_TO",
        "REFERENCES",
        "IMPLEMENTS",
        "ENABLED_BY",
        "BLOCKS",
    }

    _SIMILARITY_ID_PROP = {
        "Chunk": "chunk_id",
        "FAQ": "faq_id",
        "Document": "doc_id",
    }

    def __init__(self, neo4j: Neo4jClient):
        self._neo4j = neo4j
        self.allowed_relationship_types = set(self._DEFAULT_ALLOWED_REL_TYPES)

    @staticmethod
    def _clean_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in meta.items() if v is not None}

    @staticmethod
    def _normalize_tag(tag: str) -> str | None:
        if not tag:
            return None
        value = " ".join(tag.strip().split())
        return value.lower() if value else None

    def upsert_chunk_embeddings(
        self,
        chunk_embeddings: Dict[str, List[float]],
        *,
        embedding_model: str,
    ) -> None:
        if not chunk_embeddings:
            return

        rows: List[Dict[str, Any]] = []
        for chunk_id, embedding in chunk_embeddings.items():
            if not chunk_id or not embedding:
                continue
            rows.append({"chunk_id": chunk_id, "embedding": [float(x) for x in embedding]})
        if not rows:
            return

        self._neo4j.execute_write(
            """
            UNWIND $rows AS row
            MATCH (c:Chunk {chunk_id: row.chunk_id})
            SET c.embedding = row.embedding,
                c.embedding_model = $embedding_model,
                c.embedding_dim = size(row.embedding),
                c.embedding_updated_at = datetime(),
                c.updated_at = datetime()
            """,
            {"rows": rows, "embedding_model": embedding_model},
        )

    def upsert_document(self, doc_id: str, title: str, source_type: str, source_id: str, **meta: Any) -> None:
        payload = self._clean_meta(meta)
        self._neo4j.execute_write(
            """
            MERGE (d:Document {doc_id: $doc_id})
            ON CREATE SET d.created_at = datetime()
            SET d.title = $title,
                d.source_type = $source_type,
                d.source_id = $source_id,
                d.active = true,
                d.updated_at = datetime(),
                d += $meta
            """,
            {
                "doc_id": doc_id,
                "title": title,
                "source_type": source_type,
                "source_id": source_id,
                "meta": payload,
            },
        )

    def upsert_chunk_nodes(self, doc_id: str, chunk_ids: List[str], **meta: Any) -> None:
        if not chunk_ids:
            return

        payload = self._clean_meta(meta)
        chunk_props = payload.pop("chunk_props", None)
        rows: List[Dict[str, Any]] = []
        for index, chunk_id in enumerate(chunk_ids):
            props: Dict[str, Any] = {}
            if isinstance(chunk_props, dict):
                props = self._clean_meta(chunk_props.get(chunk_id, {}))
            rows.append({"chunk_id": chunk_id, "chunk_index": index, "props": props})

        self._neo4j.execute_write(
            """
            MATCH (d:Document {doc_id: $doc_id})
            UNWIND $rows AS row
            MERGE (c:Chunk {chunk_id: row.chunk_id})
            ON CREATE SET c.created_at = datetime()
            SET c.doc_id = $doc_id,
                c.chunk_index = row.chunk_index,
                c.active = true,
                c.updated_at = datetime(),
                c += $meta,
                c += row.props
            MERGE (d)-[:CONTAINS]->(c)
            """,
            {"doc_id": doc_id, "rows": rows, "meta": payload},
        )

    def upsert_tags(self, chunk_id: str, tags: List[str]) -> None:
        normalized = [self._normalize_tag(t) for t in tags]
        normalized = [t for t in normalized if t]
        if not normalized:
            return

        self._neo4j.execute_write(
            """
            MATCH (c:Chunk {chunk_id: $chunk_id})
            UNWIND $tags AS tag_name
            MERGE (t:Tag {name: tag_name})
            MERGE (c)-[:HAS_TAG]->(t)
            """,
            {"chunk_id": chunk_id, "tags": normalized},
        )

    def upsert_entities(self, chunk_id: str, entities: List[Entity]) -> None:
        if not entities:
            return

        rows: List[Dict[str, str]] = []
        for entity in entities:
            name = (entity.name or "").strip()
            type_ = (entity.type or "").strip().upper() or "UNKNOWN"
            if not name:
                continue
            rows.append({"name": name, "type": type_})

        if not rows:
            return

        self._neo4j.execute_write(
            """
            MATCH (c:Chunk {chunk_id: $chunk_id})
            UNWIND $rows AS row
            MERGE (e:Entity {name: row.name, type: row.type})
            ON CREATE SET e.created_at = datetime()
            SET e.updated_at = datetime(),
                e.active = true
            MERGE (c)-[:MENTIONS]->(e)
            """,
            {"chunk_id": chunk_id, "rows": rows},
        )

    def upsert_entity_relationships(self, relationships: List[Dict[str, str]]) -> None:
        if not relationships:
            return

        normalized: List[Dict[str, Any]] = []
        for rel in relationships:
            source = str(rel.get("source") or rel.get("from") or "").strip()
            target = str(rel.get("target") or rel.get("to") or "").strip()
            if not source or not target:
                continue

            raw_type = str(rel.get("type") or rel.get("relation") or "").strip()
            rel_type = raw_type.upper().replace(" ", "_") if raw_type else "RELATED_TO"
            if rel_type not in self.allowed_relationship_types:
                rel_type = "RELATED_TO"

            source_type = str(rel.get("source_type") or rel.get("sourceType") or "UNKNOWN").strip().upper()
            target_type = str(rel.get("target_type") or rel.get("targetType") or "UNKNOWN").strip().upper()

            props = {
                k: v
                for k, v in rel.items()
                if k
                not in {
                    "source",
                    "from",
                    "target",
                    "to",
                    "type",
                    "relation",
                    "source_type",
                    "target_type",
                    "sourceType",
                    "targetType",
                }
            }
            if (
                raw_type
                and rel_type == "RELATED_TO"
                and raw_type.upper().replace(" ", "_") not in self.allowed_relationship_types
            ):
                props["raw_type"] = raw_type

            normalized.append(
                {
                    "source": source,
                    "target": target,
                    "source_type": source_type,
                    "target_type": target_type,
                    "rel_type": rel_type,
                    "props": props,
                }
            )

        if not normalized:
            return

        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for item in normalized:
            grouped.setdefault(item["rel_type"], []).append(item)

        for rel_type, rows in grouped.items():
            cypher = f"""
            UNWIND $rows AS row
            MERGE (a:Entity {{name: row.source, type: row.source_type}})
            MERGE (b:Entity {{name: row.target, type: row.target_type}})
            ON CREATE SET a.created_at = datetime(), b.created_at = datetime()
            SET a.updated_at = datetime(),
                b.updated_at = datetime(),
                a.active = true,
                b.active = true
            MERGE (a)-[r:{rel_type}]->(b)
            SET r += row.props,
                r.updated_at = datetime()
            """
            self._neo4j.execute_write(cypher, {"rows": rows})

    def link_document_refs(self, doc_id: str, referenced_doc_ids: List[str]) -> None:
        refs = [r for r in referenced_doc_ids if r]
        if not refs:
            return

        self._neo4j.execute_write(
            """
            MATCH (d:Document {doc_id: $doc_id})
            UNWIND $refs AS ref_id
            MATCH (r:Document {doc_id: ref_id})
            MERGE (d)-[:REFERS_TO]->(r)
            """,
            {"doc_id": doc_id, "refs": refs},
        )

    def link_similarities(self, from_label: str, edges: List[Tuple[str, str, float]]) -> None:
        if not edges:
            return

        label = from_label.strip()
        if label not in self._SIMILARITY_ID_PROP:
            raise ValueError(f"Unsupported label for similarity edges: {label}")

        id_prop = self._SIMILARITY_ID_PROP[label]
        rows = []
        for source_id, target_id, score in edges:
            if not source_id or not target_id:
                continue
            rows.append(
                {
                    "source": source_id,
                    "target": target_id,
                    "score": float(score),
                }
            )

        if not rows:
            return

        cypher = f"""
        UNWIND $rows AS row
        MATCH (a:{label} {{{id_prop}: row.source}})
        MATCH (b:{label} {{{id_prop}: row.target}})
        MERGE (a)-[r:SIMILAR_TO]->(b)
        SET r.score = row.score,
            r.updated_at = datetime()
        """
        self._neo4j.execute_write(cypher, {"rows": rows})

    def upsert_faq_node(self, faq: FAQEntry) -> None:
        payload = self._clean_meta(faq.metadata)
        self._neo4j.execute_write(
            """
            MERGE (f:FAQ {faq_id: $faq_id})
            ON CREATE SET f.created_at = datetime()
            SET f.question = $question,
                f.answer = $answer,
                f.active = true,
                f.updated_at = datetime(),
                f += $meta
            """,
            {
                "faq_id": faq.faq_id,
                "question": faq.question,
                "answer": faq.answer,
                "meta": payload,
            },
        )

    def link_faq(self, faq_id: str, chunk_ids: List[str], tags: List[str], entities: List[Entity]) -> None:
        if chunk_ids:
            self._neo4j.execute_write(
                """
                MATCH (f:FAQ {faq_id: $faq_id})
                UNWIND $chunk_ids AS chunk_id
                MATCH (c:Chunk {chunk_id: chunk_id})
                MERGE (f)-[:DERIVED_FROM]->(c)
                """,
                {"faq_id": faq_id, "chunk_ids": [c for c in chunk_ids if c]},
            )

        normalized_tags = [self._normalize_tag(t) for t in tags]
        normalized_tags = [t for t in normalized_tags if t]
        if normalized_tags:
            self._neo4j.execute_write(
                """
                MATCH (f:FAQ {faq_id: $faq_id})
                UNWIND $tags AS tag_name
                MERGE (t:Tag {name: tag_name})
                MERGE (f)-[:HAS_TAG]->(t)
                """,
                {"faq_id": faq_id, "tags": normalized_tags},
            )

        if entities:
            rows = []
            for entity in entities:
                name = (entity.name or "").strip()
                type_ = (entity.type or "").strip().upper() or "UNKNOWN"
                if not name:
                    continue
                rows.append({"name": name, "type": type_})
            if rows:
                self._neo4j.execute_write(
                    """
                    MATCH (f:FAQ {faq_id: $faq_id})
                    UNWIND $rows AS row
                    MERGE (e:Entity {name: row.name, type: row.type})
                    ON CREATE SET e.created_at = datetime()
                    SET e.updated_at = datetime(),
                        e.active = true
                    MERGE (f)-[:MENTIONS]->(e)
                    """,
                    {"faq_id": faq_id, "rows": rows},
                )

    def soft_delete_document(self, doc_id: str) -> None:
        self._neo4j.execute_write(
            """
            MATCH (d:Document {doc_id: $doc_id})
            SET d.active = false,
                d.updated_at = datetime()
            """,
            {"doc_id": doc_id},
        )
        self._neo4j.execute_write(
            """
            MATCH (d:Document {doc_id: $doc_id})-[:CONTAINS]->(c:Chunk)
            SET c.active = false,
                c.updated_at = datetime()
            """,
            {"doc_id": doc_id},
        )
        self._neo4j.execute_write(
            """
            MATCH (d:Document {doc_id: $doc_id})-[:CONTAINS]->(c:Chunk)
            MATCH (f:FAQ)-[:DERIVED_FROM]->(c)
            SET f.active = false,
                f.updated_at = datetime()
            """,
            {"doc_id": doc_id},
        )
