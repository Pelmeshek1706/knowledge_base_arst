from __future__ import annotations

from collections.abc import Sequence

from personal_kb.models.embedding_client import EmbeddingClient
from personal_kb.schemas.chunk import ChunkRecord

DEFAULT_CHUNK_EMBEDDING_INSTRUCTION = (
    "Represent this document chunk for semantic retrieval in a personal knowledge base."
)


class EmbeddingService:
    """Attach chunk embeddings using the configured embedding client."""

    def __init__(
        self,
        embedding_client: EmbeddingClient,
        *,
        instruction: str = DEFAULT_CHUNK_EMBEDDING_INSTRUCTION,
    ) -> None:
        self._embedding_client = embedding_client
        self._instruction = instruction

    def embed_chunks(self, chunks: Sequence[ChunkRecord]) -> list[ChunkRecord]:
        if not chunks:
            return []
        vectors = self._embedding_client.embed_batch(
            [chunk.text for chunk in chunks],
            instruction=self._instruction,
        )
        return [
            chunk.model_copy(
                update={
                    "embedding": vector,
                    "embedding_model": self._embedding_client.config.model_name,
                    "embedding_dimension": self._embedding_client.dimension,
                }
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
