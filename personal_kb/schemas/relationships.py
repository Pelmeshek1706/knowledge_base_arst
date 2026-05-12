from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from personal_kb.schemas.common import SchemaBaseModel

RelationshipType = Literal[
    "DUPLICATE_OF",
    "NEWER_VERSION_OF",
    "RELATED_TO",
]


class DocumentRelationship(SchemaBaseModel):
    type: RelationshipType
    source_document_id: str
    target_document_id: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    source: str
    reason: str | None = None
    source_chunk_ids: list[str] = Field(default_factory=list)
    created_at: datetime | None = None

