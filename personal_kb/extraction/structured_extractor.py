from __future__ import annotations

from collections.abc import Sequence

from pydantic import Field

from personal_kb.core.errors import ExtractionError, StructuredOutputError
from personal_kb.core.normalization import normalize_entity_name, normalize_tag_name
from personal_kb.models.structured_extraction_client import StructuredExtractionClient
from personal_kb.schemas.chunk import ChunkRecord
from personal_kb.schemas.common import SchemaBaseModel
from personal_kb.schemas.config import LLMThinkingMode
from personal_kb.schemas.document import DocumentRecord
from personal_kb.schemas.entity import EntityRecord, EntityType
from personal_kb.schemas.tag import TagRecord

from personal_kb.extraction.aggregation import DocumentMetadataAggregator
from personal_kb.extraction.prompts import (
    STRICT_JSON_SYSTEM_PROMPT,
    build_chunk_extraction_prompt,
    build_document_aggregation_prompt,
)


class ChunkExtractionPayload(SchemaBaseModel):
    summary: str = Field(
        ...,
        description=(
            "One to three concise sentences summarizing only the provided chunk text."
        ),
    )
    tags: list[str] = Field(
        ...,
        max_length=10,
        description=(
            "Free-form retrieval tag strings grounded in the chunk. Include names, "
            "organizations, projects, systems, tools, models, libraries, "
            "technologies, documents, concepts, and domain terms when present."
        ),
    )
    entities: list["ExtractedEntityPayload"] = Field(
        ...,
        max_length=12,
        description=(
            "Typed grounded entities from the chunk. Use exact or near-exact phrases "
            "from the text and assign the closest supported entity type."
        ),
    )


class ExtractedEntityPayload(SchemaBaseModel):
    name: str = Field(
        ...,
        description="Exact or near-exact entity phrase copied from the chunk text.",
    )
    type: EntityType
    confidence: float | None = Field(default=None, ge=0, le=1)


class DocumentSummaryPayload(SchemaBaseModel):
    summary: str = Field(
        ...,
        description=(
            "Two to four concise sentences summarizing only the provided chunk metadata."
        ),
    )


class ChunkExtractionResult(SchemaBaseModel):
    summary: str
    tags: list[TagRecord] = Field(default_factory=list)
    entities: list[EntityRecord] = Field(default_factory=list)
    attempts: int = Field(ge=1)
    validator_notes: list[str] = Field(default_factory=list)


class DocumentExtractionResult(SchemaBaseModel):
    summary: str
    tags: list[TagRecord] = Field(default_factory=list)
    entities: list[EntityRecord] = Field(default_factory=list)
    attempts: int = Field(ge=1)
    validator_notes: list[str] = Field(default_factory=list)


class StructuredExtractor:
    """Typed semantic extraction over chunks and document metadata."""

    def __init__(
        self,
        extraction_client: StructuredExtractionClient,
        *,
        aggregator: DocumentMetadataAggregator | None = None,
        extraction_thinking_mode: LLMThinkingMode = "non_thinking",
    ) -> None:
        self._extraction_client = extraction_client
        self._aggregator = aggregator or DocumentMetadataAggregator()
        self._extraction_thinking_mode = extraction_thinking_mode

    def extract_chunk_metadata(self, chunk: ChunkRecord) -> ChunkExtractionResult:
        prompt = build_chunk_extraction_prompt(chunk)
        try:
            result = self._extraction_client.extract(
                prompt,
                response_schema=ChunkExtractionPayload,
                system_prompt=STRICT_JSON_SYSTEM_PROMPT,
                validator=self._validate_chunk_payload,
                thinking_mode=self._extraction_thinking_mode,
                temperature=0.0,
            )
        except StructuredOutputError as exc:
            raise ExtractionError(
                f"chunk metadata extraction failed for {chunk.chunk_id}: {exc}"
            ) from exc

        return ChunkExtractionResult(
            summary=result.value.summary.strip(),
            tags=[
                self._build_tag_record(tag, source_chunk_id=chunk.chunk_id)
                for tag in result.value.tags
            ],
            entities=[
                self._build_entity_record(entity, source_chunk_id=chunk.chunk_id)
                for entity in result.value.entities
            ],
            attempts=result.attempts,
            validator_notes=result.validator_notes,
        )

    def aggregate_document_metadata(
        self,
        document: DocumentRecord,
        chunks: Sequence[ChunkRecord],
    ) -> DocumentExtractionResult:
        prompt = build_document_aggregation_prompt(document, chunks)
        try:
            result = self._extraction_client.extract(
                prompt,
                response_schema=DocumentSummaryPayload,
                system_prompt=STRICT_JSON_SYSTEM_PROMPT,
                validator=self._validate_document_summary_payload,
                thinking_mode=self._extraction_thinking_mode,
                temperature=0.0,
            )
        except StructuredOutputError as exc:
            raise ExtractionError(
                f"document metadata aggregation failed for {document.document_id}: {exc}"
            ) from exc

        aggregated_chunks = list(chunks)
        return DocumentExtractionResult(
            summary=result.value.summary.strip(),
            tags=self._aggregator.aggregate_tags(aggregated_chunks),
            entities=self._aggregator.aggregate_entities(aggregated_chunks),
            attempts=result.attempts,
            validator_notes=result.validator_notes,
        )

    def _validate_chunk_payload(
        self, payload: ChunkExtractionPayload
    ) -> ChunkExtractionPayload:
        if not payload.summary.strip():
            raise ValueError("summary must not be blank")

        return payload.model_copy(
            update={
                "tags": self._clean_tag_strings(payload.tags),
                "entities": self._clean_entities(payload.entities),
            }
        )

    def _validate_document_summary_payload(
        self, payload: DocumentSummaryPayload
    ) -> DocumentSummaryPayload:
        if not payload.summary.strip():
            raise ValueError("document summary must not be blank")
        return payload

    def _build_tag_record(
        self, tag_name: str, *, source_chunk_id: str
    ) -> TagRecord:
        name = tag_name.strip()
        normalized_name = normalize_tag_name(name)
        return TagRecord(
            name=name,
            normalized_name=normalized_name,
            confidence=None,
            source="llm_extraction",
            source_chunks=[source_chunk_id],
        )

    def _build_entity_record(
        self, entity: ExtractedEntityPayload, *, source_chunk_id: str
    ) -> EntityRecord:
        name = entity.name.strip()
        normalized_name = normalize_entity_name(name)
        return EntityRecord(
            name=name,
            normalized_name=normalized_name,
            type=entity.type,
            confidence=entity.confidence,
            source="llm_extraction",
            source_chunks=[source_chunk_id],
        )

    def _clean_tag_strings(self, tags: Sequence[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for tag in tags:
            name = tag.strip()
            normalized = normalize_tag_name(name)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            cleaned.append(name)
        return cleaned

    def _clean_entities(
        self, entities: Sequence[ExtractedEntityPayload]
    ) -> list[ExtractedEntityPayload]:
        cleaned: list[ExtractedEntityPayload] = []
        seen: set[tuple[EntityType, str]] = set()
        for entity in entities:
            name = entity.name.strip()
            normalized = normalize_entity_name(name)
            if not normalized:
                continue
            key = (entity.type, normalized)
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(entity.model_copy(update={"name": name}))
        return cleaned
