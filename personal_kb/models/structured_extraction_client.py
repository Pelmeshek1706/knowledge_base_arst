from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from pydantic import BaseModel

from personal_kb.core.errors import StructuredOutputError
from personal_kb.models.llm_client import LLMClient, LLMTextResponse, StructuredLLMResult
from personal_kb.schemas.config import LLMThinkingMode

SchemaT = TypeVar("SchemaT", bound=BaseModel)
StructuredValidator = Callable[[SchemaT], SchemaT]


@dataclass(slots=True)
class StructuredExtractionResult(Generic[SchemaT]):
    value: SchemaT
    response: LLMTextResponse
    attempts: int
    validator_notes: list[str] = field(default_factory=list)


class StructuredExtractionClient:
    """Compose the LLM client with schema-aware extraction retries."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def extract(
        self,
        prompt: str,
        *,
        response_schema: type[SchemaT],
        system_prompt: str | None = None,
        validator: StructuredValidator[SchemaT] | None = None,
        thinking_mode: LLMThinkingMode | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        max_retries: int | None = None,
    ) -> StructuredExtractionResult[SchemaT]:
        retries = (
            self.llm_client.config.structured_output_retries
            if max_retries is None
            else max_retries
        )
        total_attempts = retries + 1
        validator_notes: list[str] = []
        active_prompt = prompt

        for attempt_index in range(total_attempts):
            result = self.llm_client.generate_json(
                active_prompt,
                response_schema=response_schema,
                system_prompt=system_prompt,
                thinking_mode=thinking_mode,
                temperature=temperature,
                max_tokens=max_tokens,
                max_retries=0,
            )
            typed_value = result.value

            if validator is None:
                return StructuredExtractionResult(
                    value=typed_value,
                    response=result.response,
                    attempts=attempt_index + 1,
                    validator_notes=validator_notes,
                )

            try:
                validated = validator(typed_value)
            except Exception as exc:
                validator_notes.append(str(exc))
                if attempt_index + 1 >= total_attempts:
                    raise StructuredOutputError(
                        "structured extraction validator failed after "
                        f"{total_attempts} attempts: {exc}"
                    ) from exc
                active_prompt = self._repair_prompt(
                    original_prompt=prompt,
                    prior_result=result,
                    error=exc,
                )
                continue

            return StructuredExtractionResult(
                value=validated,
                response=result.response,
                attempts=attempt_index + 1,
                validator_notes=validator_notes,
            )

        raise StructuredOutputError("structured extraction failed without a valid result")

    def _repair_prompt(
        self,
        *,
        original_prompt: str,
        prior_result: StructuredLLMResult,
        error: Exception,
    ) -> str:
        return (
            f"{original_prompt}\n\n"
            f"Previous validated JSON candidate: {prior_result.value.model_dump_json()}\n"
            f"Additional validator feedback: {error}\n"
            "Return a corrected JSON object that satisfies every requirement."
        )
