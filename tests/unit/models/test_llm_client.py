from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from pydantic import BaseModel

from personal_kb.core.errors import StructuredOutputError
from personal_kb.models.llm_client import (
    LLMClient,
    LLMResponseMetadata,
    LLMTextResponse,
)
from personal_kb.schemas.config import LLMConfig


@dataclass
class FakeCompletion:
    payload: dict[str, Any]

    def model_dump(self, mode: str = "json") -> dict[str, Any]:
        assert mode == "json"
        return self.payload


class FakeCompletions:
    def __init__(self, payloads: list[dict[str, Any]]) -> None:
        self.payloads = [FakeCompletion(payload) for payload in payloads]
        self.requests: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> FakeCompletion:
        self.requests.append(kwargs)
        return self.payloads.pop(0)


class FakeChatAPI:
    def __init__(self, payloads: list[dict[str, Any]]) -> None:
        self.completions = FakeCompletions(payloads)


class FakeClient:
    def __init__(self, payloads: list[dict[str, Any]]) -> None:
        self.chat = FakeChatAPI(payloads)


class AnswerPayload(BaseModel):
    answer: str


def _response_payload(
    *,
    content: str,
    reasoning_content: str | None = None,
    finish_reason: str = "stop",
    reasoning_tokens: int | None = None,
) -> dict[str, Any]:
    usage: dict[str, Any] = {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
    }
    if reasoning_tokens is not None:
        usage["completion_tokens_details"] = {"reasoning_tokens": reasoning_tokens}

    return {
        "choices": [
            {
                "finish_reason": finish_reason,
                "message": {
                    "content": content,
                    "reasoning_content": reasoning_content,
                },
            }
        ],
        "usage": usage,
    }


def _text_response(
    *,
    content: str,
    reasoning_content: str | None = None,
) -> LLMTextResponse:
    return LLMTextResponse(
        content=content,
        reasoning_content=reasoning_content,
        metadata=LLMResponseMetadata(
            provider="lmstudio_openai_compatible",
            model_name="stub-model",
            thinking_mode_requested="non_thinking",
        ),
    )


def test_generate_text_defaults_to_non_thinking_and_surfaces_reasoning() -> None:
    fake_client = FakeClient(
        [
            _response_payload(
                content="Final answer",
                reasoning_content="Hidden chain",
                reasoning_tokens=11,
            )
        ]
    )
    client = LLMClient(
        LLMConfig(),
        client_factory=lambda config: fake_client,
    )

    response = client.generate_text("Explain the result")

    request = fake_client.chat.completions.requests[0]
    assert request["extra_body"]["chat_template_kwargs"]["enable_thinking"] is False
    assert response.content == "Final answer"
    assert response.reasoning_content == "Hidden chain"
    assert response.metadata.thinking_mode_requested == "non_thinking"
    assert response.metadata.thinking_mode_defaulted is True
    assert response.metadata.provider_honored_non_thinking_request is False
    assert response.metadata.reasoning_content_present is True
    assert response.metadata.usage.reasoning_tokens == 11
    assert "non-thinking request" in response.metadata.warnings[0]


def test_generate_text_supports_explicit_thinking_mode() -> None:
    fake_client = FakeClient([_response_payload(content="Done")])
    client = LLMClient(
        LLMConfig(),
        client_factory=lambda config: fake_client,
    )

    response = client.generate_text("Think harder", thinking_mode="thinking")

    request = fake_client.chat.completions.requests[0]
    assert request["extra_body"]["chat_template_kwargs"]["enable_thinking"] is True
    assert response.metadata.thinking_mode_requested == "thinking"
    assert response.metadata.thinking_mode_defaulted is False
    assert response.metadata.provider_honored_non_thinking_request is None


def test_llm_text_response_transcript_includes_reasoning_before_answer() -> None:
    response = _text_response(
        content="Final answer",
        reasoning_content="Reasoning trace",
    )

    assert response.transcript == "Reasoning trace\n\nFinal answer"


def test_llm_text_response_transcript_returns_only_final_answer_when_present() -> None:
    response = _text_response(content="Final answer only")

    assert response.transcript == "Final answer only"


def test_llm_text_response_transcript_returns_only_reasoning_when_present() -> None:
    response = _text_response(content="", reasoning_content="Reasoning only")

    assert response.transcript == "Reasoning only"


def test_generate_text_keeps_content_and_reasoning_fields_separate() -> None:
    fake_client = FakeClient(
        [
            _response_payload(
                content="Final answer",
                reasoning_content="Hidden chain",
            )
        ]
    )
    client = LLMClient(
        LLMConfig(),
        client_factory=lambda config: fake_client,
    )

    response = client.generate_text("Explain the result")

    assert response.content == "Final answer"
    assert response.reasoning_content == "Hidden chain"
    assert response.transcript == "Hidden chain\n\nFinal answer"


def test_generate_json_retries_invalid_structured_output() -> None:
    fake_client = FakeClient(
        [
            _response_payload(content='{"answer": 123}'),
            _response_payload(content='{"answer": "fixed"}'),
        ]
    )
    client = LLMClient(
        LLMConfig(structured_output_retries=1),
        client_factory=lambda config: fake_client,
    )

    result = client.generate_json("Return JSON", response_schema=AnswerPayload)

    assert result.attempts == 2
    assert result.value.answer == "fixed"
    assert result.response.metadata.retry_count == 1
    assert (
        fake_client.chat.completions.requests[0]["response_format"]["type"]
        == "json_schema"
    )
    repaired_user_prompt = (
        fake_client.chat.completions.requests[1]["messages"][-1]["content"]
    )
    assert "Your previous response was invalid." in repaired_user_prompt


def test_generate_json_retries_reasoning_only_structured_output() -> None:
    fake_client = FakeClient(
        [
            _response_payload(
                content="",
                reasoning_content="I identified the fields but did not emit the JSON object.",
            ),
            _response_payload(content='{"answer": "fixed"}'),
        ]
    )
    client = LLMClient(
        LLMConfig(structured_output_retries=1),
        client_factory=lambda config: fake_client,
    )

    result = client.generate_json("Return JSON", response_schema=AnswerPayload)

    assert result.attempts == 2
    assert result.value.answer == "fixed"
    repaired_user_prompt = (
        fake_client.chat.completions.requests[1]["messages"][-1]["content"]
    )
    assert "Previous response preview: <empty>" in repaired_user_prompt


def test_generate_json_accepts_valid_reasoning_content_fallback() -> None:
    fake_client = FakeClient(
        [
            _response_payload(
                content="",
                reasoning_content='{"answer": "from reasoning"}',
            )
        ]
    )
    client = LLMClient(
        LLMConfig(structured_output_retries=0),
        client_factory=lambda config: fake_client,
    )

    result = client.generate_json("Return JSON", response_schema=AnswerPayload)

    assert result.value.answer == "from reasoning"
    assert result.attempts == 1
    assert result.response.content == ""
    assert result.response.metadata.structured_output_source == (
        "reasoning_content_fallback"
    )
    assert any(
        "Accepted structured JSON from reasoning_content" in warning
        for warning in result.response.metadata.warnings
    )


def test_generate_json_does_not_use_reasoning_fallback_when_visible_content_exists() -> None:
    fake_client = FakeClient(
        [
            _response_payload(
                content="not-json",
                reasoning_content='{"answer": "valid but ignored"}',
            )
        ]
    )
    client = LLMClient(
        LLMConfig(structured_output_retries=0),
        client_factory=lambda config: fake_client,
    )

    with pytest.raises(StructuredOutputError):
        client.generate_json("Return JSON", response_schema=AnswerPayload)


def test_generate_json_raises_clear_error_for_empty_structured_content() -> None:
    fake_client = FakeClient(
        [
            _response_payload(
                content="",
                reasoning_content="I can explain the answer but did not emit JSON.",
            )
        ]
    )
    client = LLMClient(
        LLMConfig(structured_output_retries=0),
        client_factory=lambda config: fake_client,
    )

    with pytest.raises(StructuredOutputError) as exc_info:
        client.generate_json("Return JSON", response_schema=AnswerPayload)

    message = str(exc_info.value)
    assert "structured output validation failed after 1 attempts" in message
    assert "reasoning-only output without visible assistant JSON content" in message
    assert "AnswerPayload" in message
    assert "finish_reason=stop" in message
    assert exc_info.value.failure_kind == "empty_content"  # type: ignore[attr-defined]
    assert (
        exc_info.value.response_metadata.raw_provider_response["choices"][0]["message"][
            "reasoning_content"
        ]
        == "I can explain the answer but did not emit JSON."
    )  # type: ignore[attr-defined]
    assert (
        exc_info.value.response_metadata.structured_output_source is None
    )  # type: ignore[attr-defined]


def test_generate_json_raises_for_invalid_reasoning_content_fallback() -> None:
    fake_client = FakeClient(
        [
            _response_payload(
                content="",
                reasoning_content="not-json",
            )
        ]
    )
    client = LLMClient(
        LLMConfig(structured_output_retries=0),
        client_factory=lambda config: fake_client,
    )

    with pytest.raises(StructuredOutputError) as exc_info:
        client.generate_json("Return JSON", response_schema=AnswerPayload)

    message = str(exc_info.value)
    assert "reasoning-only output without visible assistant JSON content" in message
    assert exc_info.value.failure_kind == "empty_content"  # type: ignore[attr-defined]


def test_generate_json_can_disable_reasoning_content_fallback() -> None:
    fake_client = FakeClient(
        [
            _response_payload(
                content="",
                reasoning_content='{"answer": "valid but disabled"}',
            )
        ]
    )
    client = LLMClient(
        LLMConfig(
            structured_output_retries=0,
            allow_structured_output_reasoning_fallback=False,
        ),
        client_factory=lambda config: fake_client,
    )

    with pytest.raises(StructuredOutputError):
        client.generate_json("Return JSON", response_schema=AnswerPayload)


def test_generate_json_raises_after_retry_budget_is_exhausted() -> None:
    fake_client = FakeClient(
        [
            _response_payload(content="not-json"),
            _response_payload(content="still not json"),
        ]
    )
    client = LLMClient(
        LLMConfig(structured_output_retries=1),
        client_factory=lambda config: fake_client,
    )

    with pytest.raises(StructuredOutputError):
        client.generate_json("Return JSON", response_schema=AnswerPayload)
