from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SchemaBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class SourceRef(SchemaBaseModel):
    file_path: str
    page: int | None = None
    section: str | None = None
    sheet: str | None = None
    cell_range: str | None = None


class ScoreBreakdown(SchemaBaseModel):
    graph_score: float | None = Field(default=None, ge=0)
    vector_score: float | None = Field(default=None, ge=0)
    entity_score: float | None = Field(default=None, ge=0)
    tag_score: float | None = Field(default=None, ge=0)
    title_keyword_score: float | None = Field(default=None, ge=0)
    reranker_score: float | None = Field(default=None, ge=0)
    final_score: float = Field(ge=0)

    @field_validator(
        "graph_score",
        "vector_score",
        "entity_score",
        "tag_score",
        "title_keyword_score",
        "reranker_score",
    )
    @classmethod
    def _validate_score_bounds(cls, value: float | None) -> float | None:
        if value is not None and value < 0:
            raise ValueError("scores must be non-negative")
        return value
