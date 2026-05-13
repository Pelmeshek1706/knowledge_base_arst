from __future__ import annotations

from math import isclose

import pytest

from personal_kb.core.errors import ModelOutputContractError
from personal_kb.models.embedding_client import EmbeddingClient
from personal_kb.schemas.config import EmbeddingConfig


class FakeEmbeddingBackend:
    def __init__(self, vectors: list[list[float]]) -> None:
        self.vectors = vectors
        self.calls: list[tuple[list[str], dict[str, object]]] = []

    def encode(self, sentences: list[str], **kwargs: object) -> list[list[float]]:
        self.calls.append((sentences, kwargs))
        return self.vectors


def test_embedding_client_is_lazy_and_preserves_batch_order() -> None:
    created: list[FakeEmbeddingBackend] = []

    def factory(config: EmbeddingConfig) -> FakeEmbeddingBackend:
        backend = FakeEmbeddingBackend(
            vectors=[
                [3.0, 4.0] + [0.0] * 1022,
                [5.0, 12.0] + [0.0] * 1022,
            ]
        )
        created.append(backend)
        return backend

    client = EmbeddingClient(EmbeddingConfig(), backend_factory=factory)

    assert created == []

    vectors = client.embed_batch(["alpha", "beta"], instruction="Index this")

    assert len(created) == 1
    sentences, kwargs = created[0].calls[0]
    assert sentences[0].startswith("Instruction: Index this")
    assert sentences[1].endswith("beta")
    assert kwargs["normalize_embeddings"] is False
    assert len(vectors) == 2
    assert len(vectors[0]) == 1024
    assert isclose(sum(value * value for value in vectors[0]), 1.0, rel_tol=1e-6)
    assert isclose(sum(value * value for value in vectors[1]), 1.0, rel_tol=1e-6)


def test_embedding_client_raises_for_dimension_mismatch() -> None:
    client = EmbeddingClient(
        EmbeddingConfig(dimension=1024),
        backend_factory=lambda config: FakeEmbeddingBackend(vectors=[[1.0, 2.0]]),
    )

    with pytest.raises(ModelOutputContractError):
        client.embed_text("hello")
