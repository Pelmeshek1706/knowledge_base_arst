from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from pydantic import BaseModel

from personal_kb.core.errors import StructuredOutputError
from personal_kb.models.llm_client import (
    LLMResponseMetadata,
    LLMTextResponse,
    StructuredLLMResult,
)
from personal_kb.models.structured_extraction_client import StructuredExtractionClient
from personal_kb.schemas.config import LLMConfig


class ExtractionPayload(BaseModel):
    label: str


@dataclass
class FakeLLMClient:
    results: list[StructuredLLMResult[ExtractionPayload]]
    config: LLMConfig = field(
        default_factory=lambda: LLMConfig(structured_output_retries=1)
    )

    def __post_init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate_json(
        self, prompt: str, **kwargs: Any
    ) -> StructuredLLMResult[ExtractionPayload]:
        self.calls.append({"prompt": prompt, **kwargs})
        return self.results.pop(0)


def _result(label: str) -> StructuredLLMResult[ExtractionPayload]:
    return StructuredLLMResult(
        value=ExtractionPayload(label=label),
        response=LLMTextResponse(
            content=f'{{"label": "{label}"}}',
            metadata=LLMResponseMetadata(
                provider="lmstudio_openai_compatible",
                model_name="test-model",
                thinking_mode_requested="non_thinking",
            ),
        ),
        attempts=1,
    )


def test_structured_extraction_retries_validator_failures() -> None:
    llm_client = FakeLLMClient(results=[_result("bad"), _result("good")])
    client = StructuredExtractionClient(llm_client)

    def validator(payload: ExtractionPayload) -> ExtractionPayload:
        if payload.label != "good":
            raise ValueError("label must be good")
        return payload

    result = client.extract(
        "Extract metadata",
        response_schema=ExtractionPayload,
        validator=validator,
        max_retries=1,
    )

    assert result.value.label == "good"
    assert result.attempts == 2
    assert result.validator_notes == ["label must be good"]
    assert "Additional validator feedback" in llm_client.calls[1]["prompt"]


def test_structured_extraction_raises_after_validator_retries() -> None:
    llm_client = FakeLLMClient(results=[_result("bad"), _result("still-bad")])
    client = StructuredExtractionClient(llm_client)

    def validator(payload: ExtractionPayload) -> ExtractionPayload:
        raise ValueError("nope")

    with pytest.raises(StructuredOutputError):
        client.extract(
            "Extract metadata",
            response_schema=ExtractionPayload,
            validator=validator,
            max_retries=1,
        )
