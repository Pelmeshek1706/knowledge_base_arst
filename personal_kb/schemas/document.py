from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from personal_kb.core.normalization import normalize_label
from personal_kb.schemas.common import SchemaBaseModel

DocumentType = Literal["pdf", "docx", "markdown", "text", "spreadsheet"]
SourceType = Literal["local_file"]
SupportedFileExtension = Literal["pdf", "docx", "md", "txt", "xlsx"]


class DocumentMetadata(SchemaBaseModel):
    created_at: datetime | None = None
    modified_at: datetime | None = None
    size_bytes: int | None = Field(default=None, ge=0)


class RawDocumentHashes(SchemaBaseModel):
    raw_bytes_hash: str | None = None
    extracted_text_hash: str | None = None


class RawDocument(SchemaBaseModel):
    source_id: str
    source_type: SourceType = "local_file"
    file_path: str
    file_name: str
    file_extension: SupportedFileExtension
    title: str
    raw_text: str
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    hashes: RawDocumentHashes | None = None


class ParsedDocument(RawDocument):
    structured_blocks: list[dict[str, object]] = Field(default_factory=list)


class DocumentRecord(SchemaBaseModel):
    document_id: str
    source_id: str
    source_type: SourceType = "local_file"
    file_path: str
    file_name: str
    file_extension: SupportedFileExtension
    document_type: DocumentType
    title: str
    normalized_title: str = ""
    summary: str | None = None
    tags: list["TagRecord"] = Field(default_factory=list)
    entities: list["EntityRecord"] = Field(default_factory=list)
    created_at: datetime | None = None
    modified_at: datetime | None = None
    ingested_at: datetime
    raw_bytes_hash: str
    extracted_text_hash: str | None = None
    content_hash: str
    is_duplicate: bool = False
    canonical_document_id: str | None = None

    @model_validator(mode="after")
    def _populate_normalized_title(self) -> "DocumentRecord":
        if not self.normalized_title:
            object.__setattr__(self, "normalized_title", normalize_label(self.title))
        return self


from personal_kb.schemas.entity import EntityRecord  # noqa: E402
from personal_kb.schemas.tag import TagRecord  # noqa: E402

DocumentRecord.model_rebuild()
