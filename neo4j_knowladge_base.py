from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from neo4j import GraphDatabase
from neo4j.graph import Node, Relationship


@dataclass
class DocumentRecord:
    """
    Representation of a single document entry in memory.

    This matches one element of your data_json list:

        {
            "title": str,
            "file_path": str,
            "description": str,
            "keywords": list[str]
        }

    Attributes
    ----------
    title : str
        Human-readable document title. If empty, file_name will be used instead.
    file_path : str
        Path to the file on disk (also used as a unique identifier in the graph).
    description : str
        Textual description / short summary of the document.
    keywords : list[str]
        List of normalized keywords describing this document. They are stored
        as :Keyword(name=...) nodes in Neo4j.

    Derived properties
    ------------------
    file_name : str
        Last path component derived from file_path (e.g. 'readme.md').
    """

    title: str
    file_path: str
    description: str
    keywords: List[str]

    @property
    def file_name(self) -> str:
        """
        Return the last path component of file_path.

        Returns
        -------
        str
            The file name extracted from self.file_path (e.g. 'readme.md').
        """
        return Path(self.file_path).name


class Neo4jKnowledgeBase:
    """
    Core graph service for your local document knowledge base.

    This class is responsible for:
    - Managing the Neo4j connection and basic schema (constraints).
    - Ingesting document metadata from your data_json structure.
    - Creating :Document and :Keyword nodes and HAS_KEYWORD / SIMILAR_TO relations.
    - Providing search utilities (by keyword, title, file_path).
    - Exporting subgraphs suitable for visualization.
    - Exposing scaffolding methods for future GraphRAG features
      (Chunk, Entity, vector search), so the public API is stable.

    Node labels
    -----------
    :Document
        Represents a document on disk.
        Properties: file_path, title, description, file_name, ingested_at.

    :Keyword
        Represents a keyword / tag extracted from your metadata.
        Properties: name.

    :Chunk (future extension)
        Represents a text chunk from a document (for RAG).
        Properties: chunk_id, text, embedding, etc.

    :Entity (future extension)
        Represents a logical entity (service, system, person, etc.).
        Properties: name, type, any extra attributes.

    Relationship types
    ------------------
    :HAS_KEYWORD
        (Document)-[:HAS_KEYWORD]->(Keyword)

    :SIMILAR_TO
        (Document)-[:SIMILAR_TO {common_keywords}]->(Document)

    :CONTAINS (future extension)
        (Document)-[:CONTAINS]->(Chunk)

    :MENTIONS (future extension)
        (Chunk)-[:MENTIONS]->(Entity)
    """

    # -------------------------------------------------------------------------
    # Lifecycle / init
    # -------------------------------------------------------------------------

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j",
    ) -> None:
        """
        Initialize the Neo4jKnowledgeBase with connection parameters.

        Parameters
        ----------
        uri : str
            Neo4j connection URI (e.g. 'neo4j://localhost:7687').
        user : str
            Neo4j username used for authentication.
        password : str
            Neo4j password used for authentication.
        database : str, default 'neo4j'
            Name of the Neo4j database to use for all queries.

        Returns
        -------
        None
            This constructor does not return a value; it prepares the driver.
        """
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._database = database

    def close(self) -> None:
        """
        Close the underlying Neo4j driver and release network resources.

        Parameters
        ----------
        None

        Returns
        -------
        None
            After this method is called, the instance can no longer
            execute queries.
        """
        self._driver.close()

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _execute_write(self, query: str, **params) -> List[Any]:
        """
        Execute a write (or mixed read/write) Cypher query in a write transaction.

        Parameters
        ----------
        query : str
            Cypher query string to execute in a write transaction.
        **params : dict
            Named parameters to pass into the Cypher query.

        Returns
        -------
        list[Any]
            A list of neo4j.Record objects representing the result rows.
            Most write operations will ignore the concrete contents.
        """

        def _tx(tx):
            result = tx.run(query, **params)
            return list(result)

        with self._driver.session(database=self._database) as session:
            return session.execute_write(_tx)

    def _execute_read(self, query: str, **params) -> List[Any]:
        """
        Execute a read Cypher query in a read transaction.

        Parameters
        ----------
        query : str
            Cypher query string to execute in a read transaction.
        **params : dict
            Named parameters to pass into the Cypher query.

        Returns
        -------
        list[Any]
            A list of neo4j.Record objects representing the result rows.
        """

        def _tx(tx):
            result = tx.run(query, **params)
            return list(result)

        with self._driver.session(database=self._database) as session:
            return session.execute_read(_tx)

    @staticmethod
    def _records_to_dicts(records: Iterable[Any]) -> List[Dict[str, Any]]:
        """
        Convert neo4j.Record objects to plain dictionaries.

        Parameters
        ----------
        records : Iterable[Any]
            Iterable of neo4j.Record objects returned by Cypher queries.

        Returns
        -------
        list[dict]
            List of dictionaries mapping column names to values for each row.
        """
        return [dict(r) for r in records]

    # -------------------------------------------------------------------------
    # Schema / constraints / maintenance
    # -------------------------------------------------------------------------

    def setup_schema(self) -> None:
        """
        Create idempotent constraints for :Document and :Keyword nodes.

        Parameters
        ----------
        None

        Returns
        -------
        None
            Constraints are created if they do not already exist:
            - Document.file_path is unique.
            - Keyword.name is unique.
        """
        # Unique Document by file_path
        self._execute_write(
            """
            CREATE CONSTRAINT document_file_path IF NOT EXISTS
            FOR (d:Document)
            REQUIRE d.file_path IS UNIQUE
            """
        )

        # Unique Keyword by name
        self._execute_write(
            """
            CREATE CONSTRAINT keyword_name IF NOT EXISTS
            FOR (k:Keyword)
            REQUIRE k.name IS UNIQUE
            """
        )

    def clear_all(self) -> None:
        """
        Delete all nodes and relationships from the database, keeping constraints.

        Parameters
        ----------
        None

        Returns
        -------
        None
            All data (nodes and relationships) are removed from the target
            database, but existing constraints / indexes remain.
        """
        self._execute_write(
            """
            MATCH (n)
            DETACH DELETE n
            """
        )

    def run_cypher(self, query: str, **params) -> List[Dict[str, Any]]:
        """
        Execute an arbitrary Cypher query and return rows as dictionaries.

        Parameters
        ----------
        query : str
            Cypher query string to be executed (read or write).
        **params : dict
            Named parameters to pass into the Cypher query.

        Returns
        -------
        list[dict]
            List of dictionaries where each dict corresponds to one
            result row and maps column names to values.

        TO DO: 
            Currently, this method always executes the query as a write
            operation. In the future, you may want to enhance it to
            automatically detect read vs. write queries.
        """
        records = self._execute_write(query, **params)
        return self._records_to_dicts(records)

    # -------------------------------------------------------------------------
    # Ingestion from data_json
    # -------------------------------------------------------------------------

    def _from_dict(self, d: Dict[str, Any]) -> DocumentRecord:
        """
        Convert a raw JSON dict entry into a validated DocumentRecord.

        Parameters
        ----------
        d : dict
            Dictionary with keys 'title', 'file_path', 'description',
            'keywords' as described by your data_json structure.

        Returns
        -------
        DocumentRecord
            Instance representing the validated canonical document entry.

        Raises
        ------
        ValueError
            If `file_path` is empty or `keywords` is not a list.
        """
        title = (d.get("title") or "").strip()
        file_path = (d.get("file_path") or "").strip()
        description = d.get("description") or ""
        keywords_raw = d.get("keywords") or []

        if not isinstance(keywords_raw, list):
            raise ValueError("`keywords` must be a list[str]")

        # Normalize keywords: strip, lower-case, drop empties, deduplicate
        normalized_keywords: List[str] = []
        for kw in keywords_raw:
            if kw is None:
                continue
            s = str(kw).strip()
            if not s:
                continue
            s_lower = s.lower()
            if s_lower not in normalized_keywords:
                normalized_keywords.append(s_lower)

        if not file_path:
            raise ValueError("`file_path` must be non-empty")

        return DocumentRecord(
            title=title or Path(file_path).name,
            file_path=file_path,
            description=description,
            keywords=normalized_keywords,
        )

    def ingest_data_json(self, data_json: List[Dict[str, Any]]) -> None:
        """
        Ingest a list of document metadata dictionaries into Neo4j.

        Parameters
        ----------
        data_json : list[dict]
            List of dictionaries, each of which must contain:
            - 'title': str
            - 'file_path': str
            - 'description': str
            - 'keywords': list[str]

        Returns
        -------
        None
            For each entry, a :Document node is created/updated and
            :Keyword nodes plus HAS_KEYWORD relationships are created.
        """
        docs = [self._from_dict(d) for d in data_json]

        for doc in docs:
            self.upsert_document(doc)
            self.attach_keywords(doc)

    # -------------------------------------------------------------------------
    # Document / keyword write operations
    # -------------------------------------------------------------------------

    def upsert_document(self, doc: DocumentRecord) -> None:
        """
        Create or update a :Document node for the given DocumentRecord.

        Parameters
        ----------
        doc : DocumentRecord
            In-memory representation of the document, containing title,
            file_path, description and keywords.

        Returns
        -------
        None
            The Document node is MERGE'd by file_path and its properties
            are updated according to the provided DocumentRecord.
        """
        self._execute_write(
            """
            MERGE (d:Document {file_path: $file_path})
            SET d.title       = $title,
                d.description = $description,
                d.file_name   = $file_name,
                d.ingested_at = datetime()
            """,
            file_path=doc.file_path,
            title=doc.title,
            description=doc.description,
            file_name=doc.file_name,
        )

    def attach_keywords(self, doc: DocumentRecord) -> None:
        """
        Ensure :Keyword nodes exist and attach them to the :Document node.

        Parameters
        ----------
        doc : DocumentRecord
            DocumentRecord whose keywords should be linked to the
            corresponding Document node via HAS_KEYWORD.

        Returns
        -------
        None
            For each keyword in doc.keywords, a :Keyword(name=...) node
            is MERGE'd and a (Document)-[:HAS_KEYWORD]->(Keyword)
            relationship is MERGE'd.
        """
        if not doc.keywords:
            return

        self._execute_write(
            """
            MATCH (d:Document {file_path: $file_path})
            UNWIND $keywords AS kw_name
            MERGE (k:Keyword {name: kw_name})
            MERGE (d)-[:HAS_KEYWORD]->(k)
            """,
            file_path=doc.file_path,
            keywords=doc.keywords,
        )

    def build_similarity_edges(self, min_common_keywords: int = 1) -> None:
        """
        Create SIMILAR_TO relationships between documents that share keywords.

        Parameters
        ----------
        min_common_keywords : int, default 1
            Minimum number of common keywords required to create a
            SIMILAR_TO edge between two Document nodes.

        Returns
        -------
        None
            For each pair of Document nodes with at least the specified
            number of common keywords, a SIMILAR_TO relationship is
            MERGE'd with property r.common_keywords.
        """
        self._execute_write(
            """
            MATCH (d1:Document)-[:HAS_KEYWORD]->(k:Keyword)<-[:HAS_KEYWORD]-(d2:Document)
            WHERE id(d1) < id(d2)
            WITH d1, d2, count(DISTINCT k) AS commonKeywords
            WHERE commonKeywords >= $min_common_keywords
            MERGE (d1)-[r:SIMILAR_TO]-(d2)
            SET r.common_keywords = commonKeywords,
                r.created_at      = datetime()
            """,
            min_common_keywords=min_common_keywords,
        )

    # -------------------------------------------------------------------------
    # Document / keyword read & search operations
    # -------------------------------------------------------------------------

    def list_documents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Return a list of documents with their associated keywords.

        Parameters
        ----------
        limit : int, default 50
            Maximum number of documents to return.

        Returns
        -------
        list[dict]
            Each dict contains:
            - 'file_path': str
            - 'title': str
            - 'keywords': list[str]
        """
        records = self._execute_read(
            """
            MATCH (d:Document)
            OPTIONAL MATCH (d)-[:HAS_KEYWORD]->(k:Keyword)
            RETURN d.file_path AS file_path,
                   d.title     AS title,
                   collect(DISTINCT k.name) AS keywords
            ORDER BY title
            LIMIT $limit
            """,
            limit=limit,
        )
        return self._records_to_dicts(records)

    def get_document_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single Document node by file_path with its keywords.

        Parameters
        ----------
        file_path : str
            Exact file_path value identifying the Document node.

        Returns
        -------
        dict or None
            If found, returns a dict:
            - 'file_path': str
            - 'title': str
            - 'description': str
            - 'file_name': str
            - 'keywords': list[str]
            If no matching Document is found, returns None.
        """
        records = self._execute_read(
            """
            MATCH (d:Document {file_path: $file_path})
            OPTIONAL MATCH (d)-[:HAS_KEYWORD]->(k:Keyword)
            RETURN d.file_path   AS file_path,
                   d.title       AS title,
                   d.description AS description,
                   d.file_name   AS file_name,
                   collect(DISTINCT k.name) AS keywords
            """,
            file_path=file_path,
        )
        rows = self._records_to_dicts(records)
        return rows[0] if rows else None

    def search_documents_by_keyword(
        self,
        keyword: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search documents that are linked to a specific keyword.

        Parameters
        ----------
        keyword : str
            Keyword text to search for (case-insensitive).
        limit : int, default 50
            Maximum number of matching documents to return.

        Returns
        -------
        list[dict]
            Each dict contains:
            - 'file_path': str
            - 'title': str
            - 'description': str
            - 'keywords': list[str]
        """
        kw = keyword.strip().lower()
        records = self._execute_read(
            """
            MATCH (k:Keyword {name: $kw})<-[:HAS_KEYWORD]-(d:Document)
            OPTIONAL MATCH (d)-[:HAS_KEYWORD]->(k2:Keyword)
            RETURN d.file_path   AS file_path,
                   d.title       AS title,
                   d.description AS description,
                   collect(DISTINCT k2.name) AS keywords
            ORDER BY title
            LIMIT $limit
            """,
            kw=kw,
            limit=limit,
        )
        return self._records_to_dicts(records)

    def search_documents_by_keywords(
        self,
        keywords: List[str],
        mode: str = "any",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search documents matching one or all of the given keywords.

        Parameters
        ----------
        keywords : list[str]
            List of keyword strings to search for (case-insensitive).
        mode : str, default 'any'
            Matching mode:
            - 'any': Document must contain at least one of the keywords.
            - 'all': Document must contain all of the keywords.
        limit : int, default 50
            Maximum number of matching documents to return.

        Returns
        -------
        list[dict]
            Each dict contains:
            - 'file_path': str
            - 'title': str
            - 'description': str
            - 'keywords': list[str]

        Raises
        ------
        ValueError
            If keywords list is empty or mode is not 'any' or 'all'.
        """
        if not keywords:
            raise ValueError("keywords list must not be empty")

        kws = sorted({k.strip().lower() for k in keywords if k and k.strip()})
        if not kws:
            raise ValueError("keywords list must contain at least one non-empty keyword")

        if mode not in {"any", "all"}:
            raise ValueError("mode must be 'any' or 'all'")

        if mode == "any":
            query = """
                MATCH (d:Document)-[:HAS_KEYWORD]->(k:Keyword)
                WHERE k.name IN $keywords
                OPTIONAL MATCH (d)-[:HAS_KEYWORD]->(k2:Keyword)
                RETURN d.file_path   AS file_path,
                       d.title       AS title,
                       d.description AS description,
                       collect(DISTINCT k2.name) AS keywords
                ORDER BY title
                LIMIT $limit
            """
        else:  # mode == "all"
            query = """
                MATCH (d:Document)-[:HAS_KEYWORD]->(k:Keyword)
                WHERE k.name IN $keywords
                WITH d, count(DISTINCT k) AS matchedCount
                WHERE matchedCount = $keywords_count
                OPTIONAL MATCH (d)-[:HAS_KEYWORD]->(k2:Keyword)
                RETURN d.file_path   AS file_path,
                       d.title       AS title,
                       d.description AS description,
                       collect(DISTINCT k2.name) AS keywords
                ORDER BY title
                LIMIT $limit
            """

        records = self._execute_read(
            query,
            keywords=kws,
            keywords_count=len(kws),
            limit=limit,
        )
        return self._records_to_dicts(records)

    def search_documents_by_title(
        self,
        query_text: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search documents by a case-insensitive substring of the title.

        Parameters
        ----------
        query_text : str
            Text fragment to search for in the Document title.
        limit : int, default 50
            Maximum number of matching documents to return.

        Returns
        -------
        list[dict]
            Each dict contains:
            - 'file_path': str
            - 'title': str
            - 'description': str
            - 'keywords': list[str]
        """
        q = query_text.strip().lower()
        records = self._execute_read(
            """
            MATCH (d:Document)
            WHERE toLower(d.title) CONTAINS $q
            OPTIONAL MATCH (d)-[:HAS_KEYWORD]->(k:Keyword)
            RETURN d.file_path   AS file_path,
                   d.title       AS title,
                   d.description AS description,
                   collect(DISTINCT k.name) AS keywords
            ORDER BY d.title
            LIMIT $limit
            """,
            q=q,
            limit=limit,
        )
        return self._records_to_dicts(records)

    def similar_documents(
        self,
        file_path: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Return documents connected via a SIMILAR_TO relationship.

        Parameters
        ----------
        file_path : str
            Identifier of the source Document (its file_path).
        limit : int, default 20
            Maximum number of similar documents to return.

        Returns
        -------
        list[dict]
            Each dict contains:
            - 'other_file_path': str
            - 'title': str
            - 'common_keywords': int
        """
        records = self._execute_read(
            """
            MATCH (d:Document {file_path: $file_path})-[r:SIMILAR_TO]-(other:Document)
            RETURN other.file_path        AS other_file_path,
                   other.title            AS title,
                   r.common_keywords      AS common_keywords
            ORDER BY r.common_keywords DESC, title
            LIMIT $limit
            """,
            file_path=file_path,
        )
        return self._records_to_dicts(records)

    def find_related_documents(
        self,
        file_path: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Find documents related to the given document by similarity and shared keywords.

        This combines SIMILAR_TO edges (if they exist) with raw shared keyword
        counts to provide a richer "related documents" signal.

        Parameters
        ----------
        file_path : str
            Identifier of the source Document (its file_path).
        limit : int, default 20
            Maximum number of related documents to return.

        Returns
        -------
        list[dict]
            Each dict contains:
            - 'file_path': str
            - 'title': str
            - 'relevance_score': int
            - 'shared_keywords': int
            - 'similar_edge_keywords': int

            relevance_score is a combined score based on shared_keywords
            and similar_edge_keywords; higher means more strongly related.
        """
        records = self._execute_read(
            """
            MATCH (d:Document {file_path: $file_path})
            OPTIONAL MATCH (d)-[r:SIMILAR_TO]-(other:Document)
            WITH d, other, r
            OPTIONAL MATCH (d)-[:HAS_KEYWORD]->(k:Keyword)<-[:HAS_KEYWORD]-(other)
            WHERE other IS NOT NULL
            WITH other,
                 coalesce(max(r.common_keywords), 0) AS sim_kw,
                 count(DISTINCT k) AS shared_kw
            WITH other,
                 sim_kw,
                 shared_kw,
                 (sim_kw * 10 + shared_kw) AS score
            RETURN other.file_path AS file_path,
                   other.title     AS title,
                   score           AS relevance_score,
                   shared_kw       AS shared_keywords,
                   sim_kw          AS similar_edge_keywords
            ORDER BY relevance_score DESC, title
            LIMIT $limit
            """,
            file_path=file_path,
        )
        return self._records_to_dicts(records)

    # -------------------------------------------------------------------------
    # Visualization helpers (for your own UI or export)
    # -------------------------------------------------------------------------

    def get_document_neighborhood(
        self,
        file_path: str,
        depth: int = 1,
        max_nodes: int = 200,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Export a local neighborhood subgraph around a single document.

        This is useful when you want to render a graph for one document
        in a custom UI (e.g. force-directed graph). Neo4j Browser / Bloom
        can already visualize this, but this function provides the data
        in a generic JSON-friendly structure.

        Parameters
        ----------
        file_path : str
            Identifier of the center Document (its file_path).
        depth : int, default 1
            Maximum number of relationship hops away from the Document
            to include in the neighborhood (1 means direct neighbors only).
        max_nodes : int, default 200
            Maximum number of nodes to include in the returned subgraph.

        Returns
        -------
        dict
            Dictionary with keys:
            - 'nodes': list[dict] where each dict has:
                - 'id': int (Neo4j internal id of the node)
                - 'labels': list[str] (labels of the node, e.g. ['Document'])
                - 'properties': dict (property map of the node)
            - 'relationships': list[dict] where each dict has:
                - 'id': int (Neo4j internal id of the relationship)
                - 'type': str (relationship type, e.g. 'HAS_KEYWORD')
                - 'start': int (id of the start node)
                - 'end': int (id of the end node)
                - 'properties': dict (property map of the relationship)
        """
        records = self._execute_read(
            """
            MATCH (center:Document {file_path: $file_path})
            OPTIONAL MATCH p = (center)-[*1..$depth]-(n)
            WITH center, collect(DISTINCT p) AS paths
            WITH center,
                 [n IN collect(DISTINCT center) + reduce(acc = [], p IN paths |
                     acc + nodes(p)
                 ) | n][0..$max_nodes] AS nodes,
                 paths
            WITH nodes,
                 reduce(relAcc = [], p IN paths | relAcc + relationships(p)) AS rels
            WITH nodes, [r IN rels | r] AS relationships
            RETURN nodes, relationships
            """,
            file_path=file_path,
            depth=depth,
            max_nodes=max_nodes,
        )

        if not records:
            return {"nodes": [], "relationships": []}

        record = records[0]
        nodes: List[Node] = record.get("nodes") or []
        relationships: List[Relationship] = record.get("relationships") or []

        node_dicts: List[Dict[str, Any]] = []
        for n in nodes:
            node_dicts.append(
                {
                    "id": n.id,
                    "labels": list(n.labels),
                    "properties": dict(n),
                }
            )

        # Build a set of node ids to filter out relationships whose endpoints
        # are not in the selected node set (defensive programming).
        node_ids = {n["id"] for n in node_dicts}

        rel_dicts: List[Dict[str, Any]] = []
        for r in relationships:
            start_id = r.start_node.id
            end_id = r.end_node.id
            if start_id in node_ids and end_id in node_ids:
                rel_dicts.append(
                    {
                        "id": r.id,
                        "type": r.type,
                        "start": start_id,
                        "end": end_id,
                        "properties": dict(r),
                    }
                )

        return {"nodes": node_dicts, "relationships": rel_dicts}

    def export_subgraph_for_visualization(
        self,
        center_file_paths: List[str],
        radius: int = 2,
        max_nodes: int = 300,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Export a larger subgraph around multiple center documents.

        This is a generalized version of get_document_neighborhood()
        that starts from several documents at once and expands outwards.

        Parameters
        ----------
        center_file_paths : list[str]
            List of file_path values representing the center Document nodes
            to expand from.
        radius : int, default 2
            Maximum relationship distance (number of hops) from the centers
            to include in the subgraph.
        max_nodes : int, default 300
            Maximum number of nodes to include in the returned subgraph.

        Returns
        -------
        dict
            Dictionary with the same structure as get_document_neighborhood():
            - 'nodes': list[dict] describing nodes.
            - 'relationships': list[dict] describing relationships.
        """
        if not center_file_paths:
            return {"nodes": [], "relationships": []}

        records = self._execute_read(
            """
            MATCH (center:Document)
            WHERE center.file_path IN $file_paths
            OPTIONAL MATCH p = (center)-[*1..$radius]-(n)
            WITH collect(DISTINCT p) AS paths
            WITH [n IN reduce(acc = [], p IN paths | acc + nodes(p)) | n][0..$max_nodes] AS nodes,
                 paths
            WITH nodes,
                 reduce(relAcc = [], p IN paths | relAcc + relationships(p)) AS rels
            WITH nodes, [r IN rels | r] AS relationships
            RETURN nodes, relationships
            """,
            file_paths=center_file_paths,
            radius=radius,
            max_nodes=max_nodes,
        )

        if not records:
            return {"nodes": [], "relationships": []}

        record = records[0]
        nodes: List[Node] = record.get("nodes") or []
        relationships: List[Relationship] = record.get("relationships") or []

        node_dicts: List[Dict[str, Any]] = []
        for n in nodes:
            node_dicts.append(
                {
                    "id": n.id,
                    "labels": list(n.labels),
                    "properties": dict(n),
                }
            )

        node_ids = {n["id"] for n in node_dicts}

        rel_dicts: List[Dict[str, Any]] = []
        for r in relationships:
            start_id = r.start_node.id
            end_id = r.end_node.id
            if start_id in node_ids and end_id in node_ids:
                rel_dicts.append(
                    {
                        "id": r.id,
                        "type": r.type,
                        "start": start_id,
                        "end": end_id,
                        "properties": dict(r),
                    }
                )

        return {"nodes": node_dicts, "relationships": rel_dicts}

    # -------------------------------------------------------------------------
    # Future GraphRAG: Chunk / Entity / Vector scaffolding
    # -------------------------------------------------------------------------

    def setup_vector_index_for_chunks(self) -> None:
        """
        Placeholder for creating a vector index on :Chunk(embedding).

        This method is intentionally left unimplemented for the current
        phase, because you are not yet storing embeddings. When you
        introduce text chunks and embeddings, you can implement this
        to run a Cypher command similar to:

            CREATE VECTOR INDEX chunk_embedding_index IF NOT EXISTS
            FOR (c:Chunk) ON (c.embedding)
            OPTIONS {
              indexConfig: {
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
              }
            };

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        NotImplementedError
            Always raised until you implement index creation for your
            specific Neo4j version and embedding dimensions.
        """
        raise NotImplementedError(
            "setup_vector_index_for_chunks must be implemented when you add embeddings."
        )

    def upsert_chunk(
        self,
        file_path: str,
        chunk_id: str,
        text: str,
        embedding: Optional[List[float]] = None,
    ) -> None:
        """
        Create or update a :Chunk node and link it to its :Document.

        Parameters
        ----------
        file_path : str
            file_path of the parent Document node.
        chunk_id : str
            Unique identifier of the chunk within the document
            (e.g., 'chunk-001').
        text : str
            Text content of the chunk.
        embedding : list[float] or None, default None
            Optional embedding vector to store as a 'embedding' property
            on the :Chunk node.

        Returns
        -------
        None
            A :Chunk node is MERGE'd and linked to the corresponding
            :Document via a CONTAINS relationship.
        """
        self._execute_write(
            """
            MATCH (d:Document {file_path: $file_path})
            MERGE (c:Chunk {chunk_id: $chunk_id, file_path: $file_path})
            SET c.text = $text,
                c.updated_at = datetime()
            MERGE (d)-[:CONTAINS]->(c)
            """,
            file_path=file_path,
            chunk_id=chunk_id,
            text=text,
        )

        # Embedding is stored in a separate query to avoid issues with
        # parameter size and to keep this optional.
        if embedding is not None:
            self._execute_write(
                """
                MATCH (c:Chunk {chunk_id: $chunk_id, file_path: $file_path})
                SET c.embedding = $embedding
                """,
                file_path=file_path,
                chunk_id=chunk_id,
                embedding=embedding,
            )

    def attach_chunk_keywords(
        self,
        file_path: str,
        chunk_id: str,
        keywords: List[str],
    ) -> None:
        """
        Attach Keyword nodes to a Chunk node rather than to the whole Document.

        Parameters
        ----------
        file_path : str
            file_path of the parent Document node.
        chunk_id : str
            Identifier of the Chunk node within that document.
        keywords : list[str]
            List of keyword strings to attach to this Chunk.

        Returns
        -------
        None
            For each keyword, a :Keyword node is MERGE'd and a
            (Chunk)-[:HAS_KEYWORD]->(Keyword) relationship is MERGE'd.
        """
        if not keywords:
            return

        kws = sorted({k.strip().lower() for k in keywords if k and k.strip()})
        if not kws:
            return

        self._execute_write(
            """
            MATCH (c:Chunk {chunk_id: $chunk_id, file_path: $file_path})
            UNWIND $keywords AS kw_name
            MERGE (k:Keyword {name: kw_name})
            MERGE (c)-[:HAS_KEYWORD]->(k)
            """,
            file_path=file_path,
            chunk_id=chunk_id,
            keywords=kws,
        )

    def upsert_entity(
        self,
        name: str,
        type_: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Create or update an :Entity node representing a logical concept.

        Parameters
        ----------
        name : str
            Human-readable entity name (e.g., 'BAM 2.0', 'JFrog', 'Terraform').
        type_ : str
            Entity type label (e.g., 'System', 'Service', 'Person').
        properties : dict or None, default None
            Additional properties to set on the Entity (e.g., {'env': 'prod'}).

        Returns
        -------
        None
            An :Entity node is MERGE'd by name and type and the provided
            properties are applied.
        """
        props = properties or {}
        self._execute_write(
            """
            MERGE (e:Entity {name: $name, type: $type})
            SET e += $props,
                e.updated_at = datetime()
            """,
            name=name,
            type=type_,
            props=props,
        )

    def link_chunk_entity(
        self,
        file_path: str,
        chunk_id: str,
        entity_name: str,
    ) -> None:
        """
        Link a Chunk node to an existing Entity via a MENTIONS relationship.

        Parameters
        ----------
        file_path : str
            file_path of the parent Document node.
        chunk_id : str
            Identifier of the Chunk node.
        entity_name : str
            Name of the Entity node that the chunk mentions. The entity
            is matched only by name; for more strict matching you can
            extend this to also use entity type.

        Returns
        -------
        None
            A (Chunk)-[:MENTIONS]->(Entity) relationship is MERGE'd.
        """
        self._execute_write(
            """
            MATCH (c:Chunk {chunk_id: $chunk_id, file_path: $file_path})
            MATCH (e:Entity {name: $entity_name})
            MERGE (c)-[:MENTIONS]->(e)
            """,
            file_path=file_path,
            chunk_id=chunk_id,
            entity_name=entity_name,
        )

    def search_documents_by_entity(
        self,
        entity_name: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search for documents that are linked to a given Entity via chunks.

        This is a future-looking utility that expects you to have already
        created :Entity nodes and linked them from :Chunk via MENTIONS.

        Parameters
        ----------
        entity_name : str
            Name of the Entity node to search for (case-sensitive or
            case-insensitive depending on your upsert strategy).
        limit : int, default 50
            Maximum number of documents to return.

        Returns
        -------
        list[dict]
            Each dict contains:
            - 'file_path': str
            - 'title': str
            - 'description': str
            - 'entity_name': str
            - 'chunks_count': int (how many chunks mention the entity)
        """
        records = self._execute_read(
            """
            MATCH (e:Entity {name: $name})<-[:MENTIONS]-(c:Chunk)<-[:CONTAINS]-(d:Document)
            WITH d, e, count(DISTINCT c) AS chunksCount
            OPTIONAL MATCH (d)-[:HAS_KEYWORD]->(k:Keyword)
            RETURN d.file_path   AS file_path,
                   d.title       AS title,
                   d.description AS description,
                   e.name        AS entity_name,
                   chunksCount   AS chunks_count,
                   collect(DISTINCT k.name) AS keywords
            ORDER BY chunksCount DESC, title
            LIMIT $limit
            """,
            name=entity_name,
            limit=limit,
        )
        return self._records_to_dicts(records)

    def vector_search_chunks(
        self,
        embedding: List[float],
        top_k: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Placeholder for performing vector search over Chunk embeddings.

        Once you have:
        - Stored embeddings on :Chunk(embedding), and
        - Created a vector index (e.g. 'chunk_embedding_index'),

        you can implement this method to run a Cypher call similar to:

            CALL db.index.vector.queryNodes(
                'chunk_embedding_index',
                $top_k,
                $embedding
            ) YIELD node, score
            MATCH (d:Document)-[:CONTAINS]->(node)
            RETURN d.file_path AS file_path,
                   d.title     AS title,
                   node.chunk_id AS chunk_id,
                   node.text     AS text,
                   score         AS similarity
            ORDER BY score DESC
            LIMIT $top_k;

        Parameters
        ----------
        embedding : list[float]
            Query embedding vector to search for nearest chunks.
        top_k : int, default 20
            Maximum number of nearest chunks to return.

        Returns
        -------
        list[dict]
            Intended to contain information about matching chunks and
            their parent documents once implemented.

        Raises
        ------
        NotImplementedError
            Always raised until vector index and appropriate Cypher
            query are implemented.
        """
        raise NotImplementedError(
            "vector_search_chunks must be implemented after you create a vector index."
        )
