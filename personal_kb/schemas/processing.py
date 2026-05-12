from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from personal_kb.schemas.common import SchemaBaseModel
from personal_kb.schemas.document import (
    DocumentMetadata,
    RawDocumentHashes,
    SourceType,
    SupportedFileExtension,
)
from personal_kb.schemas.relationships import RelationshipType


class ProcessingAction(str, Enum):
    SKIP = "SKIP"
    PROCESS_NEW = "PROCESS_NEW"
    NEWER_VERSION_OF = "NEWER_VERSION_OF"
    DUPLICATE_OF = "DUPLICATE_OF"
    RETRY_FAILED = "RETRY_FAILED"


class DiscoveredFile(SchemaBaseModel):
    document_id: str
    source_id: str
    source_type: SourceType = "local_file"
    file_path: str
    file_name: str
    file_extension: SupportedFileExtension
    raw_bytes_hash: str
    size_bytes: int | None = None
    modified_at: datetime | None = None


class ProcessingDecision(SchemaBaseModel):
    candidate: DiscoveredFile
    action: ProcessingAction
    reason: str
    matched_document_id: str | None = None
    related_document_id: str | None = None
    relationship_type: RelationshipType | None = None
    retry_allowed: bool = False


class ProcessingPlan(SchemaBaseModel):
    decisions: list[ProcessingDecision] = Field(default_factory=list)


class ProcessingMetadata(SchemaBaseModel):
    parser: str
    chunker: str
    llm_model: str | None = None
    embedding_model: str | None = None
    reranker_model: str | None = None
    processed_at: datetime
    errors: list[str] = Field(default_factory=list)


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
    structured_blocks: list[dict[str, Any]] = Field(default_factory=list)


class ProcessedDocument(SchemaBaseModel):
    schema_version: str = "0.2"
    document: "DocumentRecord"
    raw_text: str
    chunks: list["ChunkRecord"]
    relationships: list["DocumentRelationship"] = Field(default_factory=list)
    processing: ProcessingMetadata


from personal_kb.schemas.chunk import ChunkRecord  # noqa: E402
from personal_kb.schemas.document import DocumentRecord  # noqa: E402
from personal_kb.schemas.relationships import DocumentRelationship  # noqa: E402

ProcessedDocument.model_rebuild()
