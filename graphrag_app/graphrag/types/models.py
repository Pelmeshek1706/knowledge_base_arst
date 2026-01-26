from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


SourceType = Literal["pdf", "google_docs", "notion", "unknown"]


@dataclass(frozen=True)
class RawDocument:
    """
    Connector output: raw content + metadata.

    This is the canonical payload shape returned by any Connector implementation.
    """

    source_type: SourceType
    source_id: str
    title: str
    text: str
    url: Optional[str] = None
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CanonicalDocument:
    """
    Normalized document representation used by chunking/embedding/graph builders.

    Notes
    -----
    - doc_id should be stable across updates (derived from source_type+source_id).
    """

    doc_id: str
    source_type: SourceType
    source_id: str
    title: str
    text: str
    url: Optional[str] = None
    file_path: Optional[str] = None
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Chunk:
    """
    A chunk of text from a document.

    Notes
    -----
    - chunk_id must be stable and used consistently by both VectorSearchClass and GraphRag.
    - It is recommended to derive chunk_id from (doc_id, chunk_index, checksum).
    """

    chunk_id: str
    doc_id: str
    chunk_index: int
    text: str
    heading_path: Optional[str] = None
    page: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Entity:
    """
    A typed entity extracted from text.

    Examples
    --------
    - TECHNOLOGY: "Neo4j"
    - CONCEPT: "GraphRAG"
    - ORGANIZATION: "FUIB"
    """

    name: str
    type: str


@dataclass(frozen=True)
class ChunkAnnotation:
    """
    Structured markup for a chunk.

    Fields are aligned with a typical workflow:
    - mark chunk type
    - extract entities and relationships
    - produce tags/keywords
    - optionally propose candidate Q/A pairs
    """

    chunk_type: str
    summary: Optional[str]
    entities: List[Entity]
    relationships: List[Dict[str, str]]
    tags: List[str]
    candidate_qas: List[Dict[str, str]]  # [{"question": "...", "answer": "..."}]


@dataclass(frozen=True)
class FAQEntry:
    """
    A single FAQ item to persist and link in the graph.

    Notes
    -----
    - Store provenance: which chunks/docs supported this answer.
    - Dedupe is typically vector-based (question/answer embedding similarity).
    """

    faq_id: str
    question: str
    answer: str
    doc_ids: List[str] = field(default_factory=list)
    chunk_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Citation:
    """
    A machine-readable citation for UI and auditing.

    The orchestrator should attach citations to answers.
    """

    doc_id: str
    chunk_id: str
    title: str
    url: Optional[str]
    score: Optional[float] = None


@dataclass(frozen=True)
class AnswerWithCitations:
    """
    Final answer output format.

    Designed for agent tool return or MCP tool output.
    """

    answer: str
    citations: List[Citation]
    debug: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScoredRef:
    """
    A scored reference returned by vector kNN.

    Attributes
    ----------
    node_id:
        Neo4j internal ID or application-level ID depending on your storage choice.
    ref_id:
        Application-level stable ID (e.g., chunk_id or faq_id).
    score:
        Similarity score (higher is more similar for cosine similarity).
    """

    node_id: Optional[int]
    ref_id: str
    score: float
