from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from personal_kb.core.ids import make_entity_id, make_entity_key
from personal_kb.core.normalization import normalize_entity_name
from personal_kb.schemas.common import SchemaBaseModel

EntityType = Literal[
    "Person",
    "Organization",
    "Project",
    "Topic",
    "DocumentType",
    "Date",
    "MoneyAmount",
    "Account",
    "Invoice",
    "Task",
    "Technology",
    "UnknownEntity",
    "LinkedEntity",
]


class EntityRecord(SchemaBaseModel):
    entity_id: str = ""
    entity_key: str = ""
    name: str
    normalized_name: str
    type: EntityType
    confidence: float | None = Field(default=None, ge=0, le=1)
    source: str = "llm_extraction"
    summary: str | None = None
    source_chunks: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def _populate_identity_fields(self) -> "EntityRecord":
        object.__setattr__(self, "normalized_name", normalize_entity_name(self.normalized_name))
        if not self.entity_id:
            object.__setattr__(
                self, "entity_id", make_entity_id(self.type, self.normalized_name)
            )
        if not self.entity_key:
            object.__setattr__(
                self, "entity_key", make_entity_key(self.type, self.normalized_name)
            )
        return self
