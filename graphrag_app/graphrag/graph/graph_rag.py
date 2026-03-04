from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from neo4j.graph import Node, Relationship

from graphrag.storage.neo4j_client import Neo4jClient
from graphrag.types.models import Entity, FAQEntry


class GraphRag:
    """
    Graph-only GraphRAG component.

    Responsibilities
    ----------------
    - Neo4j schema for graph nodes/edges (constraints, non-vector indexes)
    - create and link nodes: Document, Chunk, Entity, Tag, FAQ
    - create semantic edges from external signals (e.g., similarity pairs)
    - neighborhood expansion for retrieval context
    """

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
    _VECTOR_INDEX_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
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
        # Allow users to override this set after instantiation if needed.
        self.allowed_relationship_types = set(self._DEFAULT_ALLOWED_REL_TYPES)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in meta.items() if v is not None}

    @staticmethod
    def _normalize_tag(tag: str) -> str | None:
        if not tag:
            return None
        value = " ".join(tag.strip().split())
        return value.lower() if value else None

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

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def setup_graph_schema(self) -> None:
        """
        Create graph constraints and non-vector indexes.
        """
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
    def _validate_index_name(cls, index_name: str) -> str:
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
        """
        Create Neo4j vector index for :Chunk(embedding).
        """
        dims = int(dimensions)
        if dims <= 0:
            raise ValueError("dimensions must be > 0")

        similarity = (similarity_function or "cosine").strip().lower()
        if similarity not in {"cosine", "euclidean"}:
            raise ValueError("similarity_function must be one of: cosine, euclidean")

        idx_name = self._validate_index_name(index_name)
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
        """
        Return embedding dimensionality from existing Chunk nodes if available.
        """
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

    def upsert_chunk_embeddings(
        self,
        chunk_embeddings: Dict[str, List[float]],
        *,
        embedding_model: str,
    ) -> None:
        """
        Store/update embeddings on Chunk nodes.
        """
        if not chunk_embeddings:
            return

        rows: List[Dict[str, Any]] = []
        for chunk_id, embedding in chunk_embeddings.items():
            if not chunk_id or not embedding:
                continue
            rows.append(
                {
                    "chunk_id": chunk_id,
                    "embedding": [float(x) for x in embedding],
                }
            )
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

    def vector_search_chunks(
        self,
        query_embedding: List[float],
        *,
        top_k: int = 8,
        index_name: str = "chunk_embedding_index",
        include_doc_url: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Run kNN vector retrieval over Chunk nodes in Neo4j.
        """
        if not query_embedding:
            return []

        idx_name = self._validate_index_name(index_name)
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

    @classmethod
    def _extract_query_terms(cls, query: str, *, max_terms: int = 8) -> List[str]:
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

    def search(
        self,
        query: str,
        *,
        limit: int = 12,
        include_doc_url: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Search local graph knowledge by human text query and return context chunks.

        Output shape is compatible with retrieval contexts:
          - chunk_id, text, doc_id, document_id, title, score
        """
        q = (query or "").strip()
        if not q:
            return []

        terms = self._extract_query_terms(q)
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

    # ------------------------------------------------------------------
    # Upserts
    # ------------------------------------------------------------------

    def upsert_document(self, doc_id: str, title: str, source_type: str, source_id: str, **meta: Any) -> None:
        """
        Create or update a Document node.
        """
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
        """
        Create or update Chunk nodes and connect them to a Document.
        """
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
        """
        Upsert Tag nodes and link them to a Chunk.
        """
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
        """
        Upsert Entity nodes and link them to a Chunk.
        """
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
        """
        Upsert entity-to-entity relationships.
        """
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
            if raw_type and rel_type == "RELATED_TO" and raw_type.upper().replace(" ", "_") not in self.allowed_relationship_types:
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

    # ------------------------------------------------------------------
    # Document/document references
    # ------------------------------------------------------------------

    def link_document_refs(self, doc_id: str, referenced_doc_ids: List[str]) -> None:
        """
        Create explicit document references (e.g., hyperlinks, citations).
        """
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

    # ------------------------------------------------------------------
    # Similarity edges (computed elsewhere)
    # ------------------------------------------------------------------

    def link_similarities(self, from_label: str, edges: List[Tuple[str, str, float]]) -> None:
        """
        Persist similarity edges between nodes.
        """
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

    # ------------------------------------------------------------------
    # FAQ graph
    # ------------------------------------------------------------------

    def upsert_faq_node(self, faq: FAQEntry) -> None:
        """
        Create or update an FAQ node.
        """
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
        """
        Link an FAQ node to supporting graph evidence.
        """
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

    # ------------------------------------------------------------------
    # Expansion / retrieval context
    # ------------------------------------------------------------------

    def expand_from_seeds(
        self,
        seed_chunk_ids: List[str],
        hops: int = 2,
        limit: int = 200,
        include_faq: bool = True,
        include_doc_url: bool = False,
    ) -> Dict[str, Any]:
        """
        Expand a graph neighborhood starting from seed chunks.
        """
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
            chunk_rows = self._neo4j.run(
                chunk_query,
                {"chunk_ids": chunk_ids},
            )
            chunks = chunk_rows

        return {
            "nodes": nodes,
            "edges": edges,
            "chunks": chunks,
            "seed_chunk_ids": seed_ids,
        }

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def soft_delete_document(self, doc_id: str) -> None:
        """
        Soft-delete a document and its dependent nodes/edges.
        """
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
