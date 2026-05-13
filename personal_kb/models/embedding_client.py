from __future__ import annotations

from collections.abc import Callable, Sequence
from math import sqrt
from typing import Any, Protocol, cast

from personal_kb.core.errors import (
    EmbeddingError,
    ModelOutputContractError,
    ModelProviderUnavailableError,
)
from personal_kb.schemas.config import EmbeddingConfig


class EmbeddingBackend(Protocol):
    def encode(self, sentences: Sequence[str], **kwargs: Any) -> Any: ...


EmbeddingBackendFactory = Callable[[EmbeddingConfig], EmbeddingBackend]


class EmbeddingClient:
    """Lazy embedding boundary for local embedding models."""

    def __init__(
        self,
        config: EmbeddingConfig,
        *,
        backend_factory: EmbeddingBackendFactory | None = None,
    ) -> None:
        self.config = config
        self._backend_factory = backend_factory or self._default_backend_factory
        self._backend: EmbeddingBackend | None = None

    @property
    def dimension(self) -> int:
        return self.config.dimension

    def embed_text(self, text: str, *, instruction: str | None = None) -> list[float]:
        vectors = self.embed_batch([text], instruction=instruction)
        return vectors[0]

    def embed_batch(
        self, texts: Sequence[str], *, instruction: str | None = None
    ) -> list[list[float]]:
        if not texts:
            return []
        prepared = [self._prepare_text(text, instruction=instruction) for text in texts]
        try:
            encoded = self._get_backend().encode(
                prepared,
                normalize_embeddings=False,
                show_progress_bar=False,
            )
        except Exception as exc:
            raise EmbeddingError(
                f"embedding generation failed for model {self.config.model_name}: {exc}"
            ) from exc

        vectors = self._coerce_vectors(encoded)
        normalized: list[list[float]] = []
        for index, vector in enumerate(vectors):
            if len(vector) != self.config.dimension:
                raise ModelOutputContractError(
                    "embedding dimension mismatch for item "
                    f"{index}: expected {self.config.dimension}, got {len(vector)}"
                )
            normalized.append(
                self._normalize(vector) if self.config.normalize_embeddings else vector
            )
        return normalized

    def _get_backend(self) -> EmbeddingBackend:
        if self._backend is None:
            try:
                self._backend = self._backend_factory(self.config)
            except ImportError as exc:
                raise ModelProviderUnavailableError(
                    "sentence-transformers is unavailable for the configured embedding model"
                ) from exc
            except Exception as exc:  # pragma: no cover - defensive wrapper
                raise ModelProviderUnavailableError(
                    f"failed to initialize embedding model {self.config.model_name}: {exc}"
                ) from exc
        return self._backend

    def _prepare_text(self, text: str, *, instruction: str | None) -> str:
        if instruction and self.config.instruction_aware:
            return f"Instruction: {instruction}\nText: {text}"
        return text

    def _coerce_vectors(self, encoded: Any) -> list[list[float]]:
        if hasattr(encoded, "tolist"):
            encoded = encoded.tolist()
        if not isinstance(encoded, list):
            raise ModelOutputContractError("embedding backend did not return a sequence")

        vectors: list[list[float]] = []
        for item in encoded:
            if hasattr(item, "tolist"):
                item = item.tolist()
            if not isinstance(item, list):
                raise ModelOutputContractError(
                    "embedding backend returned a non-vector item"
                )
            vectors.append([float(value) for value in item])
        return vectors

    def _normalize(self, vector: Sequence[float]) -> list[float]:
        magnitude = sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            raise ModelOutputContractError("embedding backend returned a zero vector")
        return [float(value / magnitude) for value in vector]

    def _default_backend_factory(self, config: EmbeddingConfig) -> EmbeddingBackend:
        from sentence_transformers import SentenceTransformer

        return cast(EmbeddingBackend, SentenceTransformer(config.model_name))
