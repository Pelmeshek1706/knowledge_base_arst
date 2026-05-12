from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from personal_kb.schemas.common import SchemaBaseModel

ProcessingStatus = Literal[
    "new",
    "processed",
    "synced",
    "skipped",
    "duplicate",
    "failed",
    "versioned",
]


class ManifestDocumentEntry(SchemaBaseModel):
    document_id: str
    source_id: str
    file_path: str
    file_name: str
    file_extension: str
    raw_bytes_hash: str
    extracted_text_hash: str | None = None
    content_hash: str
    processed_json_path: str | None = None
    ingested_at: datetime | None = None
    modified_at: datetime | None = None
    neo4j_synced: bool = False
    canonical_document_id: str | None = None
    duplicate_of: str | None = None
    newer_version_of: str | None = None
    status: ProcessingStatus
    error_message: str | None = None
    source_type: str | None = None

    @model_validator(mode="after")
    def _validate_status_dependent_fields(self) -> "ManifestDocumentEntry":
        if self.status == "failed" and not self.error_message:
            raise ValueError("error_message is required when status='failed'")
        if self.status in {"processed", "synced", "duplicate", "versioned"} and not self.processed_json_path:
            raise ValueError(
                "processed_json_path is required when status indicates processed data"
            )
        return self


class Manifest(SchemaBaseModel):
    schema_version: str = "0.2"
    active_neo4j_database: str = "knowledge_base3"
    fallback_neo4j_database: str = "neo4j"
    documents: list[ManifestDocumentEntry] = Field(default_factory=list)
