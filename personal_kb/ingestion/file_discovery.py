from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, cast

from personal_kb.core.hashing import HashingService
from personal_kb.core.ids import make_document_id
from personal_kb.core.paths import PathResolver
from personal_kb.schemas.document import SupportedFileExtension
from personal_kb.schemas.processing import DiscoveredFile

_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({"pdf", "docx", "md", "txt", "xlsx"})


class FileDiscoveryService:
    """Discover supported local files under the project data directory."""

    def __init__(
        self,
        project_root: Path | None = None,
        hashing_service: HashingService | None = None,
        supported_extensions: Iterable[str] | None = None,
    ) -> None:
        self.project_root = (project_root or Path.cwd()).resolve()
        self.path_resolver = PathResolver(self.project_root)
        self.hashing_service = hashing_service or HashingService()
        self.supported_extensions = frozenset(
            extension.lower().lstrip(".")
            for extension in (supported_extensions or _SUPPORTED_EXTENSIONS)
        )

    def scan(self, documents_dir: Path | str | None = None) -> list[DiscoveredFile]:
        """Return discovered supported files in deterministic path order."""

        if documents_dir is None:
            resolved_documents_dir = self.path_resolver.resolve_documents_dir()
        else:
            resolved_documents_dir = self.path_resolver.resolve_project_path(
                documents_dir
            )
        if not resolved_documents_dir.exists():
            return []

        file_paths = [
            path
            for path in resolved_documents_dir.rglob("*")
            if path.is_file() and self._is_supported(path)
        ]
        file_paths.sort(key=lambda path: self.path_resolver.to_storage_path(path))

        return [self._build_candidate(path) for path in file_paths]

    def discover(self, documents_dir: Path | str | None = None) -> list[DiscoveredFile]:
        """Compatibility alias for the roadmap class design."""

        return self.scan(documents_dir)

    def _is_supported(self, path: Path) -> bool:
        extension = path.suffix.lower().lstrip(".")
        return bool(extension) and extension in self.supported_extensions

    def _build_candidate(self, path: Path) -> DiscoveredFile:
        source_id = self.path_resolver.to_storage_path(path)
        raw_bytes_hash = self.hashing_service.hash_file_bytes(path)
        stat_result = path.stat()
        modified_at = datetime.fromtimestamp(stat_result.st_mtime, tz=UTC)
        file_extension = cast(SupportedFileExtension, path.suffix.lower().lstrip("."))
        return DiscoveredFile(
            document_id=make_document_id(source_id, raw_bytes_hash),
            source_id=source_id,
            source_type="local_file",
            file_path=source_id,
            file_name=path.name,
            file_extension=file_extension,
            raw_bytes_hash=raw_bytes_hash,
            size_bytes=stat_result.st_size,
            modified_at=modified_at,
        )
