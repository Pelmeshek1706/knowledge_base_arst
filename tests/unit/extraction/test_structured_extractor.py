from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from personal_kb.core.errors import ExtractionError, StructuredOutputError
from personal_kb.extraction.structured_extractor import (
    ChunkExtractionPayload,
    DocumentSummaryPayload,
    StructuredExtractor,
)
from personal_kb.models.llm_client import (
    LLMClient,
    LLMResponseMetadata,
    LLMTextResponse,
    StructuredLLMResult,
)
from personal_kb.models.structured_extraction_client import StructuredExtractionClient
from personal_kb.schemas.chunk import ChunkRecord
from personal_kb.schemas.common import SourceRef
from personal_kb.schemas.config import LLMConfig
from personal_kb.schemas.document import DocumentRecord
from personal_kb.schemas.entity import EntityRecord
from personal_kb.schemas.tag import TagRecord


@dataclass
class FakeLLMClient:
    results: list[StructuredLLMResult[Any]]
    config: LLMConfig = field(
        default_factory=lambda: LLMConfig(structured_output_retries=1)
    )

    def __post_init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate_json(self, prompt: str, **kwargs: Any) -> StructuredLLMResult[Any]:
        self.calls.append({"prompt": prompt, **kwargs})
        return self.results.pop(0)


@dataclass
class FakeProviderCompletion:
    payload: dict[str, Any]

    def model_dump(self, mode: str = "json") -> dict[str, Any]:
        assert mode == "json"
        return self.payload


class FakeProviderCompletions:
    def __init__(self, payloads: list[dict[str, Any]]) -> None:
        self.payloads = [FakeProviderCompletion(payload) for payload in payloads]
        self.requests: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> FakeProviderCompletion:
        self.requests.append(kwargs)
        return self.payloads.pop(0)


class FakeProviderChatAPI:
    def __init__(self, payloads: list[dict[str, Any]]) -> None:
        self.completions = FakeProviderCompletions(payloads)


class FakeProviderClient:
    def __init__(self, payloads: list[dict[str, Any]]) -> None:
        self.chat = FakeProviderChatAPI(payloads)


def _result(value: Any) -> StructuredLLMResult[Any]:
    return StructuredLLMResult(
        value=value,
        response=LLMTextResponse(
            content=value.model_dump_json(),
            metadata=LLMResponseMetadata(
                provider="lmstudio_openai_compatible",
                model_name="test-model",
                thinking_mode_requested="non_thinking",
            ),
        ),
        attempts=1,
    )


def _chunk() -> ChunkRecord:
    return ChunkRecord(
        document_id="doc-1",
        chunk_index=0,
        text="Alice reviews the roadmap budget in Prague.",
        source_ref=SourceRef(file_path="data/doc-1.txt", section="full_text"),
    )


def _document() -> DocumentRecord:
    return DocumentRecord(
        document_id="doc-1",
        source_id="data/doc-1.txt",
        file_path="data/doc-1.txt",
        file_name="doc-1.txt",
        file_extension="txt",
        document_type="text",
        title="Roadmap Notes",
        ingested_at="2026-05-09T12:00:00Z",
        raw_bytes_hash="raw",
        extracted_text_hash="text",
        content_hash="content",
    )


def _provider_response_payload(*, content: str, reasoning_content: str) -> dict[str, Any]:
    return {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": content,
                    "reasoning_content": reasoning_content,
                },
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        },
    }


def test_chunk_extraction_payload_schema_requires_summary_and_tags() -> None:
    schema = ChunkExtractionPayload.model_json_schema()

    assert schema["required"] == ["summary", "tags"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["summary"]["type"] == "string"
    assert schema["properties"]["tags"]["type"] == "array"
    assert schema["properties"]["tags"]["items"]["type"] == "string"
    assert "retrieval tag strings" in schema["properties"]["tags"]["description"]


def test_structured_extractor_retries_blank_summary_and_uses_non_thinking() -> None:
    llm_client = FakeLLMClient(
        results=[
            _result(
                ChunkExtractionPayload(
                    summary="   ",
                    tags=["Roadmap Budget"],
                )
            ),
            _result(
                ChunkExtractionPayload(
                    summary="Alice reviews the roadmap budget.",
                    tags=["Roadmap Budget"],
                )
            ),
        ]
    )
    extractor = StructuredExtractor(StructuredExtractionClient(llm_client))

    result = extractor.extract_chunk_metadata(_chunk())

    assert result.attempts == 2
    assert result.summary == "Alice reviews the roadmap budget."
    assert result.tags[0].name == "Roadmap Budget"
    assert result.tags[0].normalized_name == "roadmap budget"
    assert result.tags[0].confidence is None
    assert result.entities == []
    assert llm_client.calls[0]["thinking_mode"] == "non_thinking"
    assert "Return only valid JSON" in llm_client.calls[0]["system_prompt"]
    assert "Additional validator feedback" in llm_client.calls[1]["prompt"]


def test_structured_extractor_cleans_blank_and_duplicate_tag_strings() -> None:
    llm_client = FakeLLMClient(
        results=[
            _result(
                ChunkExtractionPayload(
                    summary="Alice reviews the roadmap budget.",
                    tags=[
                        " Roadmap Budget ",
                        "",
                        "roadmap   budget",
                        "Neo4j",
                        "   ",
                        "NEO4J",
                    ],
                )
            )
        ]
    )
    extractor = StructuredExtractor(StructuredExtractionClient(llm_client))

    result = extractor.extract_chunk_metadata(_chunk())

    assert [tag.name for tag in result.tags] == ["Roadmap Budget", "Neo4j"]
    assert [tag.normalized_name for tag in result.tags] == [
        "roadmap budget",
        "neo4j",
    ]
    assert [tag.source_chunks for tag in result.tags] == [
        [_chunk().chunk_id],
        [_chunk().chunk_id],
    ]


def test_structured_extractor_accepts_valid_reasoning_content_fallback() -> None:
    provider_client = FakeProviderClient(
        [
            _provider_response_payload(
                content="",
                reasoning_content=(
                    '{"summary": "Alice reviews the roadmap budget.", '
                    '"tags": ["Roadmap Budget", "Alice", "Prague"]}'
                ),
            )
        ]
    )
    extractor = StructuredExtractor(
        StructuredExtractionClient(
            LLMClient(
                LLMConfig(structured_output_retries=0),
                client_factory=lambda config: provider_client,
            )
        )
    )

    result = extractor.extract_chunk_metadata(_chunk())

    assert result.summary == "Alice reviews the roadmap budget."
    assert result.tags[0].normalized_name == "roadmap budget"
    assert result.entities == []
    assert (
        provider_client.chat.completions.requests[0]["extra_body"][
            "chat_template_kwargs"
        ]["enable_thinking"]
        is False
    )


def test_structured_extractor_raises_clear_error_after_validator_retries() -> None:
    llm_client = FakeLLMClient(
        results=[
                _result(
                    ChunkExtractionPayload(
                        summary="   ",
                        tags=[],
                    )
                ),
                _result(
                    ChunkExtractionPayload(
                        summary="   ",
                        tags=[],
                    )
                ),
        ]
    )
    extractor = StructuredExtractor(StructuredExtractionClient(llm_client))

    with pytest.raises(ExtractionError, match="chunk metadata extraction failed"):
        extractor.extract_chunk_metadata(_chunk())


def test_structured_extractor_surfaces_empty_content_provider_diagnostics() -> None:
    chunk = _chunk()
    llm_client = FakeLLMClient(
        results=[],
    )
    diagnostic_error = StructuredOutputError(
        "structured output validation failed after 1 attempts: "
        "provider returned reasoning-only output without visible assistant JSON content "
        "for structured output schema ChunkExtractionPayload; finish_reason=stop"
    )
    diagnostic_error.failure_kind = "empty_content"  # type: ignore[attr-defined]
    diagnostic_error.response_metadata = LLMResponseMetadata(  # type: ignore[attr-defined]
        provider="lmstudio_openai_compatible",
        model_name="test-model",
        finish_reason="stop",
        thinking_mode_requested="non_thinking",
        reasoning_content_present=True,
        warnings=[
            "Provider returned reasoning content for a non-thinking request.",
            "The provider returned reasoning content without visible assistant text. "
            "Increase max_tokens if you need a final answer.",
        ],
        raw_provider_response={
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": "",
                        "reasoning_content": "Reasoning but no JSON.",
                    },
                }
            ]
        },
    )

    def _raise_error(prompt: str, **kwargs: Any) -> StructuredLLMResult[Any]:
        llm_client.calls.append({"prompt": prompt, **kwargs})
        raise diagnostic_error

    llm_client.generate_json = _raise_error  # type: ignore[method-assign]
    extractor = StructuredExtractor(StructuredExtractionClient(llm_client))

    with pytest.raises(ExtractionError) as exc_info:
        extractor.extract_chunk_metadata(chunk)

    message = str(exc_info.value)
    assert f"chunk metadata extraction failed for {chunk.chunk_id}" in message
    assert "reasoning-only output without visible assistant JSON content" in message
    assert "finish_reason=stop" in message


def test_document_aggregation_returns_summary_and_merged_metadata() -> None:
    llm_client = FakeLLMClient(
        results=[
            _result(DocumentSummaryPayload(summary="Alice reviews the roadmap budget."))
        ]
    )
    extractor = StructuredExtractor(StructuredExtractionClient(llm_client))
    chunk = _chunk().model_copy(
        update={
            "summary": "Alice reviews the roadmap budget.",
            "tags": [
                TagRecord(
                    name="Budget Review",
                    normalized_name="budget review",
                    confidence=0.8,
                    source_chunks=["doc-1-0"],
                )
            ],
            "entities": [
                EntityRecord(
                    name="Alice",
                    normalized_name="alice",
                    type="Person",
                    confidence=0.92,
                    source_chunks=["doc-1-0"],
                )
            ],
        }
    )

    result = extractor.aggregate_document_metadata(_document(), [chunk])

    assert result.summary == "Alice reviews the roadmap budget."
    assert result.tags[0].normalized_name == "budget review"
    assert result.entities[0].normalized_name == "alice"
    assert llm_client.calls[0]["thinking_mode"] == "non_thinking"
