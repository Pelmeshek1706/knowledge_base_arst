from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from pydantic import ValidationError

from personal_kb.core.errors import ManifestError
from personal_kb.core.paths import PathResolver
from personal_kb.schemas.processing import ProcessedDocument
from personal_kb.storage.json_store import read_json_file, write_json_file_atomic

_PROCESSED_DOCUMENT_SCHEMA_VERSION = "0.2"


class ProcessedDocumentStore:
    """Persist and validate per-document processed JSON under `kb_storage/`."""

    def __init__(
        self,
        project_root: Path | None = None,
        storage_dir: str | Path = "kb_storage",
    ) -> None:
        self.project_root = (project_root or Path.cwd()).resolve()
        self.path_resolver = PathResolver(self.project_root)
        self.storage_dir = self.path_resolver.resolve_project_path(storage_dir)
        self.documents_dir = self.storage_dir / "documents"

    def save(self, processed_document: ProcessedDocument) -> Path:
        normalized = self._normalize_processed_document_paths(processed_document)
        document_path = self.documents_dir / f"{normalized.document.document_id}.json"
        write_json_file_atomic(document_path, normalized.model_dump(mode="json"))
        return document_path

    def load(self, document_id: str) -> ProcessedDocument:
        document_path = self.documents_dir / f"{document_id}.json"
        payload = read_json_file(document_path)
        processed_document = self._validate_processed_document_payload(
            payload, document_path
        )
        return self._normalize_processed_document_paths(processed_document)

    def exists(self, document_id: str) -> bool:
        return (self.documents_dir / f"{document_id}.json").exists()

    def iter_documents(self) -> Iterator[ProcessedDocument]:
        if not self.documents_dir.exists():
            return iter(())
        document_paths = sorted(self.documents_dir.glob("*.json"))
        return (self.load(path.stem) for path in document_paths)

    def list_documents(self) -> list[ProcessedDocument]:
        return list(self.iter_documents())

    def _validate_processed_document_payload(
        self, payload: Any, document_path: Path
    ) -> ProcessedDocument:
        try:
            processed_document = ProcessedDocument.model_validate(payload)
        except ValidationError as exc:
            raise ManifestError(
                f"invalid processed document JSON in {document_path}: {exc}"
            ) from exc

        if processed_document.schema_version != _PROCESSED_DOCUMENT_SCHEMA_VERSION:
            raise ManifestError(
                f"unsupported processed document schema version "
                f"{processed_document.schema_version!r}"
            )
        return processed_document

    def _normalize_processed_document_paths(
        self, processed_document: ProcessedDocument
    ) -> ProcessedDocument:
        payload = processed_document.model_dump(mode="python")
        document = payload["document"]
        document["source_id"] = self.path_resolver.to_storage_path(document["source_id"])
        document["file_path"] = self.path_resolver.to_storage_path(document["file_path"])

        for chunk in payload["chunks"]:
            source_ref = chunk["source_ref"]
            source_ref["file_path"] = self.path_resolver.to_storage_path(
                source_ref["file_path"]
            )

        try:
            normalized_document = ProcessedDocument.model_validate(payload)
        except ValidationError as exc:
            raise ManifestError(
                f"invalid processed document for document_id="
                f"{processed_document.document.document_id}: {exc}"
            ) from exc
        return normalized_document
