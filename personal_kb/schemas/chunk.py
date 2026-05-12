from __future__ import annotations

from datetime import datetime
from pydantic import Field, model_validator

from personal_kb.core.ids import make_chunk_id
from personal_kb.schemas.common import SchemaBaseModel, SourceRef


class ChunkRecord(SchemaBaseModel):
    chunk_id: str = ""
    document_id: str
    chunk_index: int = Field(ge=0)
    text: str
    summary: str | None = None
    tags: list["TagRecord"] = Field(default_factory=list)
    entities: list["EntityRecord"] = Field(default_factory=list)
    source_ref: SourceRef
    embedding: list[float] = Field(default_factory=list)
    embedding_model: str | None = None
    embedding_dimension: int | None = Field(default=None, ge=1)
    char_count: int | None = Field(default=None, ge=0)
    token_count: int | None = Field(default=None, ge=0)
    tag_names: list[str] = Field(default_factory=list)
    entity_names: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def _populate_identity_fields(self) -> "ChunkRecord":
        if not self.chunk_id:
            object.__setattr__(
                self, "chunk_id", make_chunk_id(self.document_id, self.chunk_index)
            )
        return self


from personal_kb.schemas.entity import EntityRecord  # noqa: E402
from personal_kb.schemas.tag import TagRecord  # noqa: E402

ChunkRecord.model_rebuild()
