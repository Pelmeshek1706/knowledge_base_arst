from __future__ import annotations

from typing import Any

from personal_kb.models.reranker_client import RerankerClient
from personal_kb.schemas.common import ScoreBreakdown
from personal_kb.schemas.config import RerankerConfig
from personal_kb.schemas.search import SearchDocumentResult


class FakeRerankerBackend:
    def __init__(self, scores: list[float]) -> None:
        self.scores = scores
        self.calls: list[tuple[list[tuple[str, str]], dict[str, Any]]] = []

    def predict(
        self, sentences: list[tuple[str, str]], **kwargs: Any
    ) -> list[float]:
        self.calls.append((sentences, kwargs))
        return self.scores


def _candidate(document_id: str, title: str, summary: str) -> SearchDocumentResult:
    return SearchDocumentResult(
        document_id=document_id,
        title=title,
        file_path=f"data/{document_id}.md",
        document_type="markdown",
        summary=summary,
        confidence=0.5,
        score_breakdown=ScoreBreakdown(final_score=0.5),
    )


def test_reranker_scores_pairs_and_reranks_stably() -> None:
    backend = FakeRerankerBackend(scores=[0.2, 0.9, 0.9])
    created: list[FakeRerankerBackend] = []

    def factory(config: RerankerConfig) -> FakeRerankerBackend:
        created.append(backend)
        return backend

    client = RerankerClient(RerankerConfig(), backend_factory=factory)
    candidates = [
        _candidate("doc-a", "A", "alpha"),
        _candidate("doc-b", "B", "beta"),
        _candidate("doc-c", "C", "gamma"),
    ]

    ranked = client.rerank("query", candidates, top_k=3)

    assert len(created) == 1
    pairs, kwargs = backend.calls[0]
    assert pairs[0] == ("query", "alpha")
    assert kwargs["show_progress_bar"] is False
    assert [item.document_id for item in ranked] == ["doc-b", "doc-c", "doc-a"]
    assert ranked[0].score_breakdown.reranker_score == 0.9
    assert ranked[1].score_breakdown.reranker_score == 0.9
    assert ranked[2].score_breakdown.reranker_score == 0.2


def test_reranker_uses_configured_default_when_top_k_is_none() -> None:
    backend = FakeRerankerBackend(scores=[0.2, 0.9, 0.4])
    client = RerankerClient(
        RerankerConfig(top_k_after_rerank=2),
        backend_factory=lambda config: backend,
    )
    candidates = [
        _candidate("doc-a", "A", "alpha"),
        _candidate("doc-b", "B", "beta"),
        _candidate("doc-c", "C", "gamma"),
    ]

    ranked = client.rerank("query", candidates, top_k=None)

    assert [item.document_id for item in ranked] == ["doc-b", "doc-c"]


def test_reranker_returns_empty_list_when_top_k_is_zero() -> None:
    backend = FakeRerankerBackend(scores=[0.2, 0.9, 0.4])
    client = RerankerClient(
        RerankerConfig(top_k_after_rerank=2),
        backend_factory=lambda config: backend,
    )
    candidates = [
        _candidate("doc-a", "A", "alpha"),
        _candidate("doc-b", "B", "beta"),
        _candidate("doc-c", "C", "gamma"),
    ]

    ranked = client.rerank("query", candidates, top_k=0)

    assert ranked == []


def test_reranker_returns_exactly_one_result_when_top_k_is_one() -> None:
    backend = FakeRerankerBackend(scores=[0.2, 0.9, 0.4])
    client = RerankerClient(
        RerankerConfig(top_k_after_rerank=3),
        backend_factory=lambda config: backend,
    )
    candidates = [
        _candidate("doc-a", "A", "alpha"),
        _candidate("doc-b", "B", "beta"),
        _candidate("doc-c", "C", "gamma"),
    ]

    ranked = client.rerank("query", candidates, top_k=1)

    assert [item.document_id for item in ranked] == ["doc-b"]
