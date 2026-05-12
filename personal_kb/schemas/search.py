from __future__ import annotations

from datetime import datetime
from typing import Literal, TypeAlias, cast

from pydantic import Field, field_validator

from personal_kb.schemas.common import SchemaBaseModel, ScoreBreakdown, SourceRef
from personal_kb.schemas.document import DocumentType
from personal_kb.schemas.relationships import RelationshipType

SearchObject = Literal["document", "entity", "tag", "chunk"]
SearchLayer = Literal["keyword", "entity", "tag", "vector", "graph"]
ScoreMode = Literal["hybrid_formula", "hybrid_formula_with_reranker", "reranker_only"]


def _default_search_objects() -> list[SearchObject]:
    return cast(list[SearchObject], ["document", "entity", "tag", "chunk"])


def _default_priority() -> list[SearchLayer]:
    return cast(list[SearchLayer], ["keyword", "entity", "vector", "graph"])


class SearchFilters(SchemaBaseModel):
    document_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    file_paths: list[str] = Field(default_factory=list)
    file_extensions: list[str] = Field(default_factory=list)
    document_types: list[DocumentType] = Field(default_factory=list)
    tag_names: list[str] = Field(default_factory=list)
    entity_names: list[str] = Field(default_factory=list)
    created_after: datetime | None = None
    created_before: datetime | None = None
    modified_after: datetime | None = None
    modified_before: datetime | None = None


class SearchPlan(SchemaBaseModel):
    search_objects: list[SearchObject] = Field(default_factory=_default_search_objects)
    priority: list[SearchLayer] = Field(default_factory=_default_priority)
    top_k: int = Field(default=10, ge=1)
    reranker: str | None = "local_cross_encoder"
    score_mode: ScoreMode = "hybrid_formula_with_reranker"
    include_related_documents: bool = True
    include_chunks: bool = True
    filters: SearchFilters | None = None

    @field_validator("search_objects", "priority")
    @classmethod
    def _ensure_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("search plan values must not contain duplicates")
        return value


class MatchedChunk(SchemaBaseModel):
    chunk_id: str
    source_ref: SourceRef
    summary: str | None = None
    text: str | None = None
    score: float | None = Field(default=None, ge=0)
    reason: str | None = None


class RelatedDocumentRef(SchemaBaseModel):
    document_id: str
    relationship: RelationshipType | str
    confidence: float | None = Field(default=None, ge=0, le=1)
    reason: str | None = None


class SearchDocumentResult(SchemaBaseModel):
    document_id: str
    title: str
    file_path: str
    document_type: DocumentType
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    matched_entities: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    modified_at: datetime | None = None
    confidence: float = Field(ge=0, le=1)
    score_breakdown: ScoreBreakdown
    matched_chunks: list[MatchedChunk] = Field(default_factory=list)
    related_documents: list[RelatedDocumentRef] = Field(default_factory=list)
    source_refs: list[SourceRef] = Field(default_factory=list)


class SearchDocumentsRequest(SchemaBaseModel):
    query: str
    search_plan: SearchPlan | None = None

    @field_validator("query")
    @classmethod
    def _validate_query(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query must not be empty")
        return value


class SearchDocumentsResponse(SchemaBaseModel):
    query: str
    search_plan_used: SearchPlan
    search_mode: list[str] = Field(default_factory=list)
    results: list[SearchDocumentResult]
    warnings: list[str] = Field(default_factory=list)
    latency_ms: float | None = Field(default=None, ge=0)


SearchPlanType: TypeAlias = SearchPlan
