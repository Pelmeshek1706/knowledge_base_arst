from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from personal_kb.chunking import TxtChunker
from personal_kb.extraction.structured_extractor import StructuredExtractor
from personal_kb.ingestion.document_aggregation_service import DocumentAggregationService
from personal_kb.ingestion.embedding_service import EmbeddingService
from personal_kb.ingestion.extraction_service import ExtractionService
from personal_kb.models.embedding_client import EmbeddingClient
from personal_kb.models.structured_extraction_client import StructuredExtractionResult
from personal_kb.parsers import TxtParser
from personal_kb.schemas.config import EmbeddingConfig
from personal_kb.schemas.document import DocumentRecord

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class FakeStructuredExtractionClient:
    payloads: list[dict[str, Any]]

    def __post_init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def extract(self, prompt: str, **kwargs: Any) -> StructuredExtractionResult[Any]:
        self.calls.append({"prompt": prompt, **kwargs})
        payload = self.payloads.pop(0)
        response_schema = kwargs["response_schema"]
        validator = kwargs.get("validator")
        value = response_schema.model_validate(payload)
        if validator is not None:
            value = validator(value)
        return StructuredExtractionResult(
            value=value,
            response=None,  # type: ignore[arg-type]
            attempts=1,
            validator_notes=[],
        )


class FakeEmbeddingBackend:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def encode(self, sentences: list[str], **kwargs: Any) -> list[list[float]]:
        self.calls.append({"sentences": sentences, **kwargs})
        return [[1.0, 0.0, 0.0] for _ in sentences]


def test_chunk_extraction_embedding_and_document_aggregation_end_to_end() -> None:
    file_path = PROJECT_ROOT / "tests" / "fixtures" / "sample_notes.txt"
    parsed = TxtParser().parse(file_path, source_id="tests/fixtures/sample_notes.txt")
    chunks = TxtChunker(chunk_size=120, chunk_overlap=0).chunk(parsed, document_id="doc-1")

    fake_extraction_client = FakeStructuredExtractionClient(
        payloads=[
            {
                "summary": "Alpha beta gamma delta outline the budget and roadmap topics.",
                "tags": [
                    "Budget Review",
                    "Roadmap",
                    "budget   review",
                    "",
                ],
            },
            {
                "summary": "The note focuses on a budget review and roadmap planning sequence.",
            },
        ]
    )
    extraction_service = ExtractionService(
        StructuredExtractor(fake_extraction_client)  # type: ignore[arg-type]
    )
    backend = FakeEmbeddingBackend()
    embedding_service = EmbeddingService(
        EmbeddingClient(
            EmbeddingConfig(model_name="test-embedding", dimension=3),
            backend_factory=lambda config: backend,
        )
    )
    document_service = DocumentAggregationService(
        StructuredExtractor(fake_extraction_client)  # type: ignore[arg-type]
    )

    enriched_chunks = extraction_service.enrich_chunks(chunks)
    embedded_chunks = embedding_service.embed_chunks(enriched_chunks)
    document = DocumentRecord(
        document_id="doc-1",
        source_id="tests/fixtures/sample_notes.txt",
        file_path="tests/fixtures/sample_notes.txt",
        file_name="sample_notes.txt",
        file_extension="txt",
        document_type="text",
        title="sample_notes",
        ingested_at="2026-05-09T12:00:00Z",
        raw_bytes_hash="raw",
        extracted_text_hash="text",
        content_hash="content",
    )
    aggregated_document = document_service.aggregate_document(document, embedded_chunks)

    assert enriched_chunks[0].summary is not None
    assert enriched_chunks[0].tag_names == ["budget review", "roadmap"]
    assert enriched_chunks[0].entity_names == []
    assert embedded_chunks[0].embedding == [1.0, 0.0, 0.0]
    assert embedded_chunks[0].embedding_model == "test-embedding"
    assert embedded_chunks[0].embedding_dimension == 3
    assert aggregated_document.summary == (
        "The note focuses on a budget review and roadmap planning sequence."
    )
    assert [tag.normalized_name for tag in aggregated_document.tags] == [
        "budget review",
        "roadmap",
    ]
    assert aggregated_document.entities == []
    assert fake_extraction_client.calls[0]["thinking_mode"] == "non_thinking"
    assert fake_extraction_client.calls[1]["thinking_mode"] == "non_thinking"
    assert backend.calls[0]["normalize_embeddings"] is False
