from __future__ import annotations

from collections.abc import Sequence

from personal_kb.extraction.structured_extractor import StructuredExtractor
from personal_kb.schemas.chunk import ChunkRecord
from personal_kb.schemas.document import DocumentRecord


class DocumentAggregationService:
    """Thin ingestion-facing wrapper around document metadata aggregation."""

    def __init__(self, extractor: StructuredExtractor) -> None:
        self._extractor = extractor

    def aggregate_document(
        self, document: DocumentRecord, chunks: Sequence[ChunkRecord]
    ) -> DocumentRecord:
        extracted = self._extractor.aggregate_document_metadata(document, chunks)
        return document.model_copy(
            update={
                "summary": extracted.summary,
                "tags": extracted.tags,
                "entities": extracted.entities,
            }
        )
