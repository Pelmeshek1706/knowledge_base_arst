from __future__ import annotations

from pathlib import Path


class PersonalKBError(Exception):
    """Base class for project-specific errors."""


class ConfigError(PersonalKBError):
    """Raised when configuration loading or validation fails."""


class PathError(PersonalKBError):
    """Raised when path resolution fails."""


class PathTraversalError(PathError):
    """Raised when a path escapes the configured project root."""

    def __init__(self, path: str | Path, project_root: str | Path) -> None:
        self.path = Path(path)
        self.project_root = Path(project_root)
        super().__init__(
            f"path '{self.path}' escapes project root '{self.project_root}'"
        )


class HashingError(PersonalKBError):
    """Raised when hashing file or text content fails."""


class NormalizationError(PersonalKBError):
    """Raised when a value cannot be normalized."""


class IdError(PersonalKBError):
    """Raised when deterministic identifier generation fails."""


class TimeError(PersonalKBError):
    """Raised when a timestamp cannot be parsed or formatted."""


class ManifestError(PersonalKBError):
    """Raised when manifest data is invalid."""


class ParsingError(PersonalKBError):
    """Raised when document parsing fails."""


class ExtractionError(PersonalKBError):
    """Raised when model-based extraction fails."""


class ModelClientError(PersonalKBError):
    """Raised when a model client cannot satisfy a request."""


class ModelProviderUnavailableError(ModelClientError):
    """Raised when a local model provider or runtime cannot be loaded."""


class ModelOutputContractError(ModelClientError):
    """Raised when a provider returns data that violates a typed contract."""


class LLMError(ModelClientError):
    """Raised when LLM generation fails."""


class StructuredOutputError(LLMError):
    """Raised when structured output cannot be parsed or validated."""


class EmbeddingError(PersonalKBError):
    """Raised when embedding generation fails."""


class RerankerError(ModelClientError):
    """Raised when reranking or reranker scoring fails."""


class GraphSyncError(PersonalKBError):
    """Raised when graph sync fails."""


class RetrievalError(PersonalKBError):
    """Raised when retrieval fails."""


class QAError(PersonalKBError):
    """Raised when question answering fails."""


class ToolExecutionError(PersonalKBError):
    """Raised when a tool-facing action fails."""
