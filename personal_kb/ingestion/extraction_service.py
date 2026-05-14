from __future__ import annotations

from collections.abc import Sequence

from personal_kb.extraction.structured_extractor import StructuredExtractor
from personal_kb.schemas.chunk import ChunkRecord


class ExtractionService:
    """Thin ingestion-facing wrapper around chunk metadata extraction."""

    def __init__(self, extractor: StructuredExtractor) -> None:
        self._extractor = extractor

    def enrich_chunk(self, chunk: ChunkRecord) -> ChunkRecord:
        extracted = self._extractor.extract_chunk_metadata(chunk)
        return chunk.model_copy(
            update={
                "summary": extracted.summary,
                "tags": extracted.tags,
                "entities": extracted.entities,
                "tag_names": [tag.normalized_name for tag in extracted.tags],
                "entity_names": [entity.normalized_name for entity in extracted.entities],
            }
        )

    def enrich_chunks(self, chunks: Sequence[ChunkRecord]) -> list[ChunkRecord]:
        return [self.enrich_chunk(chunk) for chunk in chunks]
