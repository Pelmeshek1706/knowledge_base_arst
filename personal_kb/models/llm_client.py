from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
import re
from typing import Any, Generic, Literal, Protocol, TypeVar, cast

from pydantic import BaseModel, Field, ValidationError

from personal_kb.core.errors import (
    LLMError,
    ModelProviderUnavailableError,
    StructuredOutputError,
)
from personal_kb.schemas.common import SchemaBaseModel
from personal_kb.schemas.config import LLMConfig, LLMThinkingMode

LLMRole = Literal["system", "user", "assistant"]
StructuredOutputSource = Literal["visible_content", "reasoning_content_fallback"]
SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMMessage(SchemaBaseModel):
    role: LLMRole
    content: str


class LLMUsage(SchemaBaseModel):
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    reasoning_tokens: int | None = Field(default=None, ge=0)


class LLMResponseMetadata(SchemaBaseModel):
    provider: str
    model_name: str
    finish_reason: str | None = None
    thinking_mode_requested: LLMThinkingMode
    thinking_mode_defaulted: bool = False
    reasoning_content_present: bool = False
    provider_honored_non_thinking_request: bool | None = None
    structured_output_source: StructuredOutputSource | None = None
    retry_count: int = Field(default=0, ge=0)
    usage: LLMUsage = Field(default_factory=LLMUsage)
    warnings: list[str] = Field(default_factory=list)
    raw_provider_response: dict[str, Any] = Field(default_factory=dict)


class LLMTextResponse(SchemaBaseModel):
    content: str
    reasoning_content: str | None = None
    metadata: LLMResponseMetadata

    @property
    def transcript(self) -> str:
        parts: list[str] = []
        for part in (self.reasoning_content, self.content):
            if part is None:
                continue
            stripped = part.strip()
            if stripped:
                parts.append(stripped)
        return "\n\n".join(parts)


@dataclass(slots=True)
class StructuredLLMResult(Generic[SchemaT]):
    value: SchemaT
    response: LLMTextResponse
    attempts: int


class OpenAICompatibleChatCompletions(Protocol):
    def create(self, **kwargs: Any) -> Any: ...


class OpenAICompatibleChatAPI(Protocol):
    completions: OpenAICompatibleChatCompletions


class OpenAICompatibleClient(Protocol):
    chat: OpenAICompatibleChatAPI


OpenAICompatibleClientFactory = Callable[[LLMConfig], OpenAICompatibleClient]


class LLMClient:
    """Lazy LM Studio OpenAI-compatible client."""

    def __init__(
        self,
        config: LLMConfig,
        *,
        client_factory: OpenAICompatibleClientFactory | None = None,
    ) -> None:
        self.config = config
        self._client_factory = client_factory or self._default_client_factory
        self._client: OpenAICompatibleClient | None = None

    def generate_text(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        thinking_mode: LLMThinkingMode | None = None,
        max_tokens: int | None = None,
    ) -> LLMTextResponse:
        resolved_mode, defaulted = self._resolve_thinking_mode(thinking_mode)
        completion = self._request_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            thinking_mode=resolved_mode,
            max_tokens=max_tokens,
            response_format=None,
        )
        raw_response = self._coerce_response_dict(completion)
        message = self._extract_message(raw_response)
        content = self._stringify_message_field(message.get("content"))
        reasoning_content = self._extract_reasoning_content(message, raw_response)
        return self._build_text_response(
            content=content,
            reasoning_content=reasoning_content,
            raw_response=raw_response,
            thinking_mode=resolved_mode,
            defaulted=defaulted,
        )

    def generate_json(
        self,
        prompt: str,
        *,
        response_schema: type[SchemaT],
        system_prompt: str | None = None,
        temperature: float = 0.0,
        thinking_mode: LLMThinkingMode | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
    ) -> StructuredLLMResult[SchemaT]:
        retries = (
            self.config.structured_output_retries
            if max_retries is None
            else max_retries
        )
        total_attempts = retries + 1
        last_error: Exception | None = None
        active_system_prompt = system_prompt
        active_prompt = prompt
        resolved_mode, defaulted = self._resolve_thinking_mode(thinking_mode)

        for attempt_index in range(total_attempts):
            completion = self._request_completion(
                prompt=active_prompt,
                system_prompt=active_system_prompt,
                temperature=temperature,
                thinking_mode=resolved_mode,
                max_tokens=max_tokens,
                response_format=self._build_json_schema_payload(response_schema),
            )
            raw_response = self._coerce_response_dict(completion)
            message = self._extract_message(raw_response)
            content = self._stringify_message_field(message.get("content"))
            reasoning_content = self._extract_reasoning_content(message, raw_response)
            parsed_response = self._build_text_response(
                content=content,
                reasoning_content=reasoning_content,
                raw_response=raw_response,
                thinking_mode=resolved_mode,
                defaulted=defaulted,
                retry_count=attempt_index,
            )

            try:
                parsed_value = self._parse_structured_response(
                    response_schema=response_schema,
                    response=parsed_response,
                )
            except (StructuredOutputError, json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                if attempt_index + 1 >= total_attempts:
                    break
                active_system_prompt = self._repair_system_prompt(
                    base_system_prompt=system_prompt,
                    response_schema=response_schema,
                )
                active_prompt = self._repair_user_prompt(
                    original_prompt=prompt,
                    invalid_content=content,
                    error=exc,
                )
                continue

            return StructuredLLMResult(
                value=parsed_value,
                response=parsed_response,
                attempts=attempt_index + 1,
            )

        final_error = StructuredOutputError(
            "structured output validation failed after "
            f"{total_attempts} attempts: {last_error}"
        )
        self._copy_structured_output_diagnostics(final_error, last_error)
        raise final_error from last_error

    def _get_client(self) -> OpenAICompatibleClient:
        if self._client is None:
            try:
                self._client = self._client_factory(self.config)
            except ImportError as exc:
                raise ModelProviderUnavailableError(
                    "openai client dependency is unavailable for the configured LLM"
                ) from exc
            except Exception as exc:  # pragma: no cover - defensive wrapper
                raise ModelProviderUnavailableError(
                    f"failed to initialize LLM client for {self.config.base_url}: {exc}"
                ) from exc
        return self._client

    def _request_completion(
        self,
        *,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        thinking_mode: LLMThinkingMode,
        max_tokens: int | None,
        response_format: dict[str, Any] | None,
    ) -> Any:
        messages = self._build_messages(prompt=prompt, system_prompt=system_prompt)
        extra_body = self._build_extra_body(thinking_mode)
        request_kwargs: dict[str, Any] = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens
        if extra_body:
            request_kwargs["extra_body"] = extra_body
        if response_format is not None:
            request_kwargs["response_format"] = response_format

        try:
            return self._get_client().chat.completions.create(**request_kwargs)
        except Exception as exc:
            raise LLMError(
                f"LLM request to {self.config.base_url} failed for model "
                f"{self.config.model_name}: {exc}"
            ) from exc

    def _build_messages(
        self, *, prompt: str, system_prompt: str | None
    ) -> list[dict[str, str]]:
        messages: list[LLMMessage] = []
        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))
        messages.append(LLMMessage(role="user", content=prompt))
        return [message.model_dump(mode="json") for message in messages]

    def _resolve_thinking_mode(
        self, thinking_mode: LLMThinkingMode | None
    ) -> tuple[LLMThinkingMode, bool]:
        if thinking_mode is None:
            return self.config.default_thinking_mode, True
        return thinking_mode, False

    def _build_extra_body(self, thinking_mode: LLMThinkingMode) -> dict[str, Any]:
        if thinking_mode == "default":
            return {}
        return {
            "chat_template_kwargs": {
                "enable_thinking": thinking_mode == "thinking",
            }
        }

    def _build_json_schema_payload(
        self, response_schema: type[BaseModel]
    ) -> dict[str, Any]:
        schema_name = re.sub(r"(?<!^)(?=[A-Z])", "_", response_schema.__name__).lower()
        return {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name or "structured_response",
                "strict": True,
                "schema": response_schema.model_json_schema(),
            },
        }

    def _repair_system_prompt(
        self,
        *,
        base_system_prompt: str | None,
        response_schema: type[BaseModel],
    ) -> str:
        required = (
            "Return only valid JSON that matches the provided schema exactly. "
            "Do not add markdown fences or prose."
        )
        if base_system_prompt:
            return f"{base_system_prompt}\n\n{required}"
        return (
            "You are a strict JSON generator. "
            f"{required} Schema: {response_schema.__name__}."
        )

    def _repair_user_prompt(
        self,
        *,
        original_prompt: str,
        invalid_content: str,
        error: Exception,
    ) -> str:
        preview = invalid_content[:500] if invalid_content else "<empty>"
        return (
            f"{original_prompt}\n\n"
            "Your previous response was invalid. "
            f"Validation error: {error}\n"
            f"Previous response preview: {preview}\n"
            "Try again and return only valid JSON."
        )

    def _parse_structured_response(
        self,
        *,
        response_schema: type[SchemaT],
        response: LLMTextResponse,
    ) -> SchemaT:
        content = response.content.strip()
        if content:
            parsed_payload = json.loads(content)
            parsed_value = response_schema.model_validate(parsed_payload)
            response.metadata.structured_output_source = "visible_content"
            return parsed_value

        if self.config.allow_structured_output_reasoning_fallback:
            reasoning_content = (response.reasoning_content or "").strip()
            if reasoning_content:
                try:
                    parsed_payload = json.loads(reasoning_content)
                    parsed_value = response_schema.model_validate(parsed_payload)
                except (json.JSONDecodeError, ValidationError):
                    raise self._build_empty_structured_output_error(
                        response_schema=response_schema,
                        response=response,
                    )

                response.metadata.structured_output_source = (
                    "reasoning_content_fallback"
                )
                response.metadata.warnings.append(
                    "Accepted structured JSON from reasoning_content because visible "
                    "assistant content was empty and the reasoning payload validated "
                    f"against {response_schema.__name__}."
                )
                return parsed_value

        raise self._build_empty_structured_output_error(
            response_schema=response_schema,
            response=response,
        )

    def _build_text_response(
        self,
        *,
        content: str,
        reasoning_content: str | None,
        raw_response: dict[str, Any],
        thinking_mode: LLMThinkingMode,
        defaulted: bool,
        retry_count: int = 0,
    ) -> LLMTextResponse:
        warnings: list[str] = []
        honored: bool | None = None
        if thinking_mode == "non_thinking" and reasoning_content:
            honored = False
            warnings.append(
                "Provider returned reasoning content for a non-thinking request."
            )
        if not content and reasoning_content:
            warnings.append(
                "The provider returned reasoning content without visible assistant text. "
                "Increase max_tokens if you need a final answer."
            )

        return LLMTextResponse(
            content=content,
            reasoning_content=reasoning_content,
            metadata=LLMResponseMetadata(
                provider=self.config.provider,
                model_name=self.config.model_name,
                finish_reason=self._extract_finish_reason(raw_response),
                thinking_mode_requested=thinking_mode,
                thinking_mode_defaulted=defaulted,
                reasoning_content_present=reasoning_content is not None,
                provider_honored_non_thinking_request=honored,
                retry_count=retry_count,
                usage=self._extract_usage(raw_response),
                warnings=warnings,
                raw_provider_response=raw_response,
            ),
        )

    def _build_empty_structured_output_error(
        self,
        *,
        response_schema: type[BaseModel],
        response: LLMTextResponse,
    ) -> StructuredOutputError:
        if response.reasoning_content and response.reasoning_content.strip():
            detail = "provider returned reasoning-only output without visible assistant JSON content"
        else:
            detail = "provider returned no visible assistant JSON content"
        finish_reason = response.metadata.finish_reason or "unknown"
        reason_preview = self._preview_text(response.reasoning_content)
        message = (
            f"{detail} for structured output schema {response_schema.__name__}; "
            f"finish_reason={finish_reason}"
        )
        if reason_preview is not None:
            message += f"; reasoning_preview={reason_preview!r}"
        if response.metadata.warnings:
            message += f"; warnings={response.metadata.warnings}"

        error = StructuredOutputError(message)
        self._attach_structured_output_diagnostics(
            error,
            response=response,
            response_schema=response_schema,
            failure_kind="empty_content",
        )
        return error

    def _attach_structured_output_diagnostics(
        self,
        error: StructuredOutputError,
        *,
        response: LLMTextResponse,
        response_schema: type[BaseModel],
        failure_kind: str,
    ) -> None:
        error.response = response  # type: ignore[attr-defined]
        error.response_metadata = response.metadata  # type: ignore[attr-defined]
        error.raw_provider_response = response.metadata.raw_provider_response  # type: ignore[attr-defined]
        error.response_schema = response_schema.__name__  # type: ignore[attr-defined]
        error.failure_kind = failure_kind  # type: ignore[attr-defined]

    def _copy_structured_output_diagnostics(
        self, target: StructuredOutputError, source: Exception | None
    ) -> None:
        if source is None:
            return
        for attr_name in (
            "response",
            "response_metadata",
            "raw_provider_response",
            "response_schema",
            "failure_kind",
        ):
            if hasattr(source, attr_name):
                setattr(target, attr_name, getattr(source, attr_name))

    def _preview_text(self, value: str | None, *, limit: int = 160) -> str | None:
        if value is None:
            return None
        compact = " ".join(value.split())
        if not compact:
            return None
        return compact[:limit]

    def _coerce_response_dict(self, response: Any) -> dict[str, Any]:
        if hasattr(response, "model_dump"):
            dumped = response.model_dump(mode="json")
            if isinstance(dumped, dict):
                return cast(dict[str, Any], dumped)
        if isinstance(response, dict):
            return cast(dict[str, Any], response)
        raise LLMError("provider response could not be converted into a mapping")

    def _extract_message(self, raw_response: dict[str, Any]) -> dict[str, Any]:
        choices = raw_response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMError("provider response did not include any choices")
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise LLMError("provider response choice was not a mapping")
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise LLMError("provider response choice did not include a message")
        return cast(dict[str, Any], message)

    def _extract_finish_reason(self, raw_response: dict[str, Any]) -> str | None:
        choices = raw_response.get("choices")
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                finish_reason = first_choice.get("finish_reason")
                if isinstance(finish_reason, str):
                    return finish_reason
        return None

    def _extract_usage(self, raw_response: dict[str, Any]) -> LLMUsage:
        usage = raw_response.get("usage")
        if not isinstance(usage, dict):
            return LLMUsage()

        prompt_tokens = self._coerce_int(usage.get("prompt_tokens"))
        completion_tokens = self._coerce_int(usage.get("completion_tokens"))
        total_tokens = self._coerce_int(usage.get("total_tokens"))
        reasoning_tokens = self._coerce_int(usage.get("reasoning_tokens"))

        if reasoning_tokens is None:
            completion_details = usage.get("completion_tokens_details")
            if isinstance(completion_details, dict):
                reasoning_tokens = self._coerce_int(
                    completion_details.get("reasoning_tokens")
                )

        return LLMUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            reasoning_tokens=reasoning_tokens,
        )

    def _extract_reasoning_content(
        self, message: dict[str, Any], raw_response: dict[str, Any]
    ) -> str | None:
        direct_reasoning = self._stringify_message_field(message.get("reasoning_content"))
        if direct_reasoning:
            return direct_reasoning
        nested_reasoning = self._stringify_message_field(message.get("reasoning"))
        if nested_reasoning:
            return nested_reasoning

        choices = raw_response.get("choices")
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                delta_reasoning = self._stringify_message_field(
                    first_choice.get("reasoning_content")
                )
                if delta_reasoning:
                    return delta_reasoning
        return None

    def _stringify_message_field(self, value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            parts: list[str] = []
            for item in value:
                if isinstance(item, str):
                    parts.append(item)
                    continue
                if not isinstance(item, dict):
                    continue
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                    continue
                content = item.get("content")
                if isinstance(content, str):
                    parts.append(content)
            return "\n".join(part for part in parts if part)
        return str(value)

    def _coerce_int(self, value: object) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        return None

    def _default_client_factory(self, config: LLMConfig) -> OpenAICompatibleClient:
        from openai import OpenAI

        return cast(
            OpenAICompatibleClient,
            OpenAI(
                base_url=config.base_url,
                api_key=config.api_key,
                timeout=config.timeout_seconds,
            ),
        )
