from __future__ import annotations

from pydantic import Field, field_validator

from personal_kb.schemas.common import SchemaBaseModel, SourceRef
from personal_kb.schemas.search import MatchedChunk, SearchPlan


class AnswerQuestionRequest(SchemaBaseModel):
    question: str
    search_plan: SearchPlan | None = None
    document_ids: list[str] | None = None
    include_supporting_text: bool = True
    top_k_chunks: int = Field(default=8, ge=1)

    @field_validator("question")
    @classmethod
    def _validate_question(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be empty")
        return value


class SourceDocumentRef(SchemaBaseModel):
    document_id: str
    title: str
    file_path: str
    source_refs: list[SourceRef] = Field(default_factory=list)


class AnswerQuestionResponse(SchemaBaseModel):
    question: str
    answer: str
    confidence: float = Field(ge=0, le=1)
    source_documents: list[SourceDocumentRef]
    supporting_chunks: list[MatchedChunk]
    missing_information: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

