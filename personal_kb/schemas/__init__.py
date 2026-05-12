"""Pydantic schemas for personal_kb."""

# ruff: noqa: F401

from personal_kb.schemas.chunk import ChunkRecord
from personal_kb.schemas.config import (
    AppConfig,
    EmbeddingConfig,
    LLMConfig,
    ModelConfig,
    Neo4jConfig,
    NormalizationConfig,
    PersonalKBConfig,
    ProjectConfig,
    RerankerConfig,
    SearchConfig,
    SearchWeights,
    StorageConfig,
)
from personal_kb.schemas.common import ScoreBreakdown, SchemaBaseModel, SourceRef
from personal_kb.schemas.document import (
    DocumentMetadata,
    DocumentRecord,
    DocumentType,
    ParsedDocument,
    RawDocument,
    RawDocumentHashes,
    SourceType,
    SupportedFileExtension,
)
from personal_kb.schemas.entity import EntityRecord, EntityType
from personal_kb.schemas.manifest import Manifest, ManifestDocumentEntry, ProcessingStatus
from personal_kb.schemas.processing import ProcessingMetadata, ProcessedDocument
from personal_kb.schemas.qa import AnswerQuestionRequest, AnswerQuestionResponse, SourceDocumentRef
from personal_kb.schemas.relationships import DocumentRelationship, RelationshipType
from personal_kb.schemas.search import (
    MatchedChunk,
    RelatedDocumentRef,
    ScoreMode,
    SearchDocumentResult,
    SearchDocumentsRequest,
    SearchDocumentsResponse,
    SearchFilters,
    SearchLayer,
    SearchObject,
    SearchPlan,
)
from personal_kb.schemas.tag import TagRecord
from personal_kb.schemas.tools import ToolName, ToolRequest, ToolResponse
