from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple, TypedDict, Union

from graphrag.types.models import Chunk, ChunkAnnotation


class ChatMessage(TypedDict):
    """OpenAI-style chat message."""
    role: str
    content: str


class LLMClient(Protocol):
    """
    Provider-agnostic LLM client interface for GraphRAG inference.

    Implementations must support:
      - raw chat() calls (OpenAI-compatible message format)
      - extracting query entities/topics (for seeding retrieval)
      - annotating chunks (for ingestion / graph markup)
      - generating final answers from assembled context
    """

    def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 1500,
        timeout_s: int = 60,
    ) -> str:
        """
        Send a chat completion request.

        Parameters
        ----------
        messages:
            OpenAI-compatible list of {role, content}.
        temperature:
            Sampling temperature.
        max_tokens:
            Max tokens in the response.
        timeout_s:
            Request timeout.

        Returns
        -------
        str
            Model response text.
        """
        raise NotImplementedError

    def extract_query_entities(self, question: str, max_entities: int = 3) -> List[str]:
        """
        Extract 1..N entity/topic strings from a user question.

        Output must be stable and parseable (JSON array preferred).

        Parameters
        ----------
        question:
            User query.
        max_entities:
            Maximum entities to return.

        Returns
        -------
        list[str]
            Entity/topic strings to seed graph retrieval.
        """
        raise NotImplementedError

    def annotate_chunk(self, chunk: Chunk) -> ChunkAnnotation:
        """
        Produce structured markup for a chunk:
          - chunk_type
          - summary
          - entities (name, type)
          - relationships (source, target, type)
          - tags
          - candidate_qas

        Parameters
        ----------
        chunk:
            Chunk to analyze.

        Returns
        -------
        ChunkAnnotation
            Parsed structured annotation.
        """
        raise NotImplementedError

    def generate_answer(self, question: str, context: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a final answer from question + retrieved context.

        Parameters
        ----------
        question:
            User question.
        context:
            Assembled context (graph neighborhood + chunk excerpts + doc titles).
        system_prompt:
            Optional system instruction.

        Returns
        -------
        str
            Answer text.
        """
        raise NotImplementedError


# ----------------------------
# JSON extraction helpers
# ----------------------------

class StructuredOutputError(ValueError):
    """Raised when the LLM output cannot be parsed into the required JSON structure."""


def _find_json_span(text: str) -> Optional[Tuple[int, int]]:
    """
    Find a top-level JSON object/array span inside arbitrary text.

    Returns
    -------
    (start, end) indices if found, else None.

    Notes
    -----
    This is intentionally conservative: it finds the first '{' or '[' and then scans
    until braces/brackets are balanced. It helps when the model wraps JSON in prose
    or markdown fences.
    """
    if not text:
        return None

    # Prefer object, then array (either is valid depending on prompt)
    candidates: List[int] = []
    for ch in ("{", "["):
        i = text.find(ch)
        if i != -1:
            candidates.append(i)
    if not candidates:
        return None

    start = min(candidates)
    opener = text[start]
    closer = "}" if opener == "{" else "]"

    depth = 0
    in_str = False
    esc = False

    for i in range(start, len(text)):
        c = text[i]

        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue

        if c == '"':
            in_str = True
            continue

        if c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                return start, i + 1

    return None


def loads_json_from_text(text: str) -> Union[Dict[str, Any], List[Any]]:
    """
    Parse JSON object/array from an LLM response that may contain extra text.

    Raises
    ------
    StructuredOutputError
        If JSON cannot be found or parsed.
    """
    span = _find_json_span(text)
    if not span:
        raise StructuredOutputError("No JSON object/array found in LLM response.")

    js = text[span[0] : span[1]]
    try:
        return json.loads(js)
    except json.JSONDecodeError as e:
        raise StructuredOutputError(f"Failed to parse JSON: {e}") from e


def expect_json_array(text: str) -> List[Any]:
    """Parse LLM output and assert it is a JSON array."""
    obj = loads_json_from_text(text)
    if not isinstance(obj, list):
        raise StructuredOutputError("Expected JSON array.")
    return obj


def expect_json_object(text: str) -> Dict[str, Any]:
    """Parse LLM output and assert it is a JSON object."""
    obj = loads_json_from_text(text)
    if not isinstance(obj, dict):
        raise StructuredOutputError("Expected JSON object.")
    return obj
