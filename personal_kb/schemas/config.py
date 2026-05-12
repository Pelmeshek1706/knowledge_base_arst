from __future__ import annotations

from typing import Literal

from pydantic import Field

from personal_kb.schemas.common import SchemaBaseModel
from personal_kb.schemas.search import ScoreMode


class ProjectConfig(SchemaBaseModel):
    name: str = "personal_kb"
    config_path: str = "configs/default.yaml"
    path_mode: Literal["relative", "absolute"] = "relative"


class StorageConfig(SchemaBaseModel):
    data_dir: str = "data"
    kb_storage_dir: str = "kb_storage"
    benchmark_dir: str = "benchmark"


class Neo4jConfig(SchemaBaseModel):
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = "change-me"
    database: str = "knowledge_base3"
    fallback_database: str = "neo4j"
    apoc_required: bool = False
    schema_setup_mode: str = "explicit_kb_setup_db"
    ingest_auto_sync: bool = True


class LLMConfig(SchemaBaseModel):
    provider: str = "lmstudio_openai_compatible"
    base_url: str = "http://localhost:1234/v1"
    model_name: str = "mlx-community/Qwen3.5-9B-OptiQ-4bit"
    runtime: str = "mlx-lm"
    quantization: str = "mixed_precision_4bit"
    role: str = "production_default"


class EmbeddingConfig(SchemaBaseModel):
    provider: str = "local"
    model_name: str = "Qwen/Qwen3-Embedding-0.6B"
    dimension: int = Field(default=1024, ge=1)
    context_length: int = Field(default=32768, ge=1)
    normalize_embeddings: bool = True
    instruction_aware: bool = True
    store_full_vectors_in_json: bool = True


class RerankerConfig(SchemaBaseModel):
    provider: str = "local"
    model_name: str = "Qwen/Qwen3-Reranker-0.6B"
    context_length: int = Field(default=32768, ge=1)
    top_k_before_rerank: int = Field(default=50, ge=1)
    top_k_after_rerank: int = Field(default=8, ge=1)
    instruction_aware: bool = True


class ModelConfig(SchemaBaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    reranker: RerankerConfig = Field(default_factory=RerankerConfig)


class SearchWeights(SchemaBaseModel):
    graph_score: float = Field(default=0.25, ge=0)
    vector_score: float = Field(default=0.20, ge=0)
    entity_score: float = Field(default=0.15, ge=0)
    tag_score: float = Field(default=0.10, ge=0)
    title_keyword_score: float = Field(default=0.10, ge=0)
    reranker_score: float = Field(default=0.20, ge=0)


class SearchConfig(SchemaBaseModel):
    default_top_k: int = Field(default=10, ge=1)
    include_related_documents: bool = True
    include_chunks: bool = True
    score_mode: ScoreMode = "hybrid_formula_with_reranker"
    weights: SearchWeights = Field(default_factory=SearchWeights)


class NormalizationConfig(SchemaBaseModel):
    tag_entity_normalization: Literal["lowercase_trim_collapse_spaces"] = (
        "lowercase_trim_collapse_spaces"
    )


class AppConfig(SchemaBaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    neo4j: Neo4jConfig = Field(default_factory=Neo4jConfig)
    models: ModelConfig = Field(default_factory=ModelConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    normalization: NormalizationConfig = Field(default_factory=NormalizationConfig)


PersonalKBConfig = AppConfig

