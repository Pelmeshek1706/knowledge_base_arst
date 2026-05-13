from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Protocol, cast

from personal_kb.core.errors import (
    ModelOutputContractError,
    ModelProviderUnavailableError,
    RerankerError,
)
from personal_kb.schemas.common import ScoreBreakdown
from personal_kb.schemas.config import RerankerConfig
from personal_kb.schemas.search import SearchDocumentResult


class RerankerBackend(Protocol):
    def predict(self, sentences: Sequence[tuple[str, str]], **kwargs: Any) -> Any: ...


RerankerBackendFactory = Callable[[RerankerConfig], RerankerBackend]


class RerankerClient:
    """Lazy reranker boundary for local reranking models."""

    def __init__(
        self,
        config: RerankerConfig,
        *,
        backend_factory: RerankerBackendFactory | None = None,
    ) -> None:
        self.config = config
        self._backend_factory = backend_factory or self._default_backend_factory
        self._backend: RerankerBackend | None = None

    def score_pairs(self, query: str, texts: Sequence[str]) -> list[float]:
        if not texts:
            return []
        pairs = [(query, text) for text in texts]
        try:
            raw_scores = self._get_backend().predict(pairs, show_progress_bar=False)
        except Exception as exc:
            raise RerankerError(
                f"reranker scoring failed for model {self.config.model_name}: {exc}"
            ) from exc
        return self._coerce_scores(raw_scores, expected=len(texts))

    def rerank(
        self,
        query: str,
        candidates: Sequence[SearchDocumentResult],
        *,
        top_k: int | None = None,
    ) -> list[SearchDocumentResult]:
        if not candidates:
            return []

        scores = self.score_pairs(query, [self._candidate_text(item) for item in candidates])
        ranked = sorted(
            enumerate(zip(candidates, scores)),
            key=lambda item: item[1][1],
            reverse=True,
        )
        limit = self.config.top_k_after_rerank if top_k is None else top_k
        results: list[SearchDocumentResult] = []
        for _, (candidate, score) in ranked[:limit]:
            score_breakdown = self._with_reranker_score(candidate.score_breakdown, score)
            results.append(
                candidate.model_copy(update={"score_breakdown": score_breakdown})
            )
        return results

    def _get_backend(self) -> RerankerBackend:
        if self._backend is None:
            try:
                self._backend = self._backend_factory(self.config)
            except ImportError as exc:
                raise ModelProviderUnavailableError(
                    "sentence-transformers is unavailable for the configured reranker model"
                ) from exc
            except Exception as exc:  # pragma: no cover - defensive wrapper
                raise ModelProviderUnavailableError(
                    f"failed to initialize reranker model {self.config.model_name}: {exc}"
                ) from exc
        return self._backend

    def _coerce_scores(self, raw_scores: Any, *, expected: int) -> list[float]:
        if hasattr(raw_scores, "tolist"):
            raw_scores = raw_scores.tolist()
        if not isinstance(raw_scores, list):
            raise ModelOutputContractError("reranker backend did not return a sequence")
        scores = [float(value) for value in raw_scores]
        if len(scores) != expected:
            raise ModelOutputContractError(
                f"reranker score count mismatch: expected {expected}, got {len(scores)}"
            )
        return scores

    def _candidate_text(self, candidate: SearchDocumentResult) -> str:
        if candidate.summary:
            return candidate.summary
        matched_text = " ".join(
            chunk.text or "" for chunk in candidate.matched_chunks if chunk.text
        ).strip()
        if matched_text:
            return matched_text
        return candidate.title

    def _with_reranker_score(
        self, breakdown: ScoreBreakdown, score: float
    ) -> ScoreBreakdown:
        return breakdown.model_copy(update={"reranker_score": score})

    def _default_backend_factory(self, config: RerankerConfig) -> RerankerBackend:
        from sentence_transformers import CrossEncoder

        return cast(RerankerBackend, CrossEncoder(config.model_name))
