from __future__ import annotations

from datetime import datetime

from pydantic import Field, model_validator

from personal_kb.core.ids import make_tag_id
from personal_kb.core.normalization import normalize_tag_name
from personal_kb.schemas.common import SchemaBaseModel


class TagRecord(SchemaBaseModel):
    tag_id: str = ""
    name: str
    normalized_name: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    source: str = "llm_extraction"
    source_chunks: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def _populate_identity_fields(self) -> "TagRecord":
        object.__setattr__(self, "normalized_name", normalize_tag_name(self.normalized_name))
        if not self.tag_id:
            object.__setattr__(self, "tag_id", make_tag_id(self.normalized_name))
        return self
