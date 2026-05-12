from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path

from personal_kb.schemas.document import DocumentMetadata, ParsedDocument


class BaseParser(ABC):
    """Base contract for deterministic file parsers."""

    supported_extensions: tuple[str, ...] = ()

    @abstractmethod
    def parse(self, file_path: Path, *, source_id: str | None = None) -> ParsedDocument:
        """Parse a source file into a typed parsed document."""

    def _build_metadata(self, file_path: Path) -> DocumentMetadata:
        stat = file_path.stat()
        return DocumentMetadata(
            modified_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
            size_bytes=stat.st_size,
        )

    def _normalize_source_id(self, file_path: Path, source_id: str | None) -> str:
        return source_id or file_path.as_posix()
