from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Neo4jConfig:
    """
    Neo4j connection configuration.

    Notes
    -----
    - This config is intentionally minimal.
    - Keep secrets out of code; load them via env vars in your real app.
    """

    uri: str
    username: str
    password: str


@dataclass(frozen=True)
class VectorIndexConfig:
    """
    Configuration for vector indexing and similarity search.

    Attributes
    ----------
    index_name:
        Name of the vector index in Neo4j.
    node_label:
        Label of nodes indexed (e.g., Chunk, FAQ).
    embedding_property:
        Property name holding the embedding vector.
    dimensions:
        Dimensionality of the embedding vectors.
    similarity_function:
        Similarity function name (e.g., cosine or euclidean).
    """

    index_name: str
    node_label: str
    embedding_property: str
    dimensions: int
    similarity_function: str = "cosine"


@dataclass(frozen=True)
class ChunkingConfig:
    """
    Chunking configuration (token-based or character-based depending on your implementation).

    Attributes
    ----------
    max_chars:
        Target size of each chunk. Use token-based splitting if you want tighter control.
    overlap:
        Overlap between chunks (chars/tokens) to reduce boundary loss.
    """

    max_chars: int = 2000
    overlap: int = 200


@dataclass(frozen=True)
class GraphRagConfig:
    """
    High-level toggles for GraphRAG behavior.

    Attributes
    ----------
    max_hops:
        Default expansion hops for graph neighborhood expansion.
    max_seed_chunks:
        How many seed chunks to use from vector kNN before graph expansion.
    """

    max_hops: int = 2
    max_seed_chunks: int = 12
