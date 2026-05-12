from __future__ import annotations

from pathlib import Path
from collections.abc import Callable
from typing import Any

from pydantic import ValidationError

from personal_kb.core.errors import ManifestError
from personal_kb.core.paths import PathResolver
from personal_kb.schemas.manifest import Manifest, ManifestDocumentEntry
from personal_kb.storage.json_store import read_json_file, write_json_file_atomic

_MANIFEST_SCHEMA_VERSION = "0.2"


class ManifestStore:
    """Persist and query the manifest JSON under `kb_storage/`."""

    def __init__(
        self,
        project_root: Path | None = None,
        storage_dir: str | Path = "kb_storage",
    ) -> None:
        self.project_root = (project_root or Path.cwd()).resolve()
        self.path_resolver = PathResolver(self.project_root)
        self.storage_dir = self.path_resolver.resolve_project_path(storage_dir)
        self.manifest_path = self.storage_dir / "manifest.json"

    def load(self) -> Manifest:
        if not self.manifest_path.exists():
            return Manifest()

        payload = read_json_file(self.manifest_path)
        manifest = self._validate_manifest_payload(payload)
        return self._normalize_manifest_paths(manifest)

    def save(self, manifest: Manifest) -> None:
        normalized = self._normalize_manifest_paths(manifest)
        write_json_file_atomic(self.manifest_path, normalized.model_dump(mode="json"))

    def get_by_document_id(self, document_id: str) -> ManifestDocumentEntry | None:
        return self._find_first(lambda entry: entry.document_id == document_id)

    def get_by_source_id(self, source_id: str | Path) -> ManifestDocumentEntry | None:
        normalized_source_id = self.path_resolver.to_storage_path(source_id)
        return self._find_first(lambda entry: entry.source_id == normalized_source_id)

    def get_by_raw_bytes_hash(self, raw_bytes_hash: str) -> list[ManifestDocumentEntry]:
        return self._find_all(
            lambda entry: entry.raw_bytes_hash == raw_bytes_hash
        )

    def get_by_extracted_text_hash(
        self, extracted_text_hash: str
    ) -> list[ManifestDocumentEntry]:
        return self._find_all(
            lambda entry: entry.extracted_text_hash == extracted_text_hash
        )

    def get_by_content_hash(self, content_hash: str) -> list[ManifestDocumentEntry]:
        return self._find_all(lambda entry: entry.content_hash == content_hash)

    def add_or_update(self, entry: ManifestDocumentEntry) -> None:
        manifest = self.load()
        normalized_entry = self._normalize_entry_paths(entry)
        updated_documents = list(manifest.documents)
        for index, existing in enumerate(updated_documents):
            if existing.document_id == normalized_entry.document_id:
                updated_documents[index] = normalized_entry
                break
        else:
            updated_documents.append(normalized_entry)
        self.save(manifest.model_copy(update={"documents": updated_documents}))

    def mark_synced(self, document_id: str) -> None:
        manifest = self.load()
        updated_documents = []
        found = False
        for entry in manifest.documents:
            if entry.document_id != document_id:
                updated_documents.append(entry)
                continue
            found = True
            updated_documents.append(
                entry.model_copy(update={"status": "synced", "neo4j_synced": True})
            )
        if not found:
            raise ManifestError(f"manifest entry not found for document_id={document_id}")
        self.save(manifest.model_copy(update={"documents": updated_documents}))

    def mark_failed(self, entry: ManifestDocumentEntry) -> None:
        failed_entry = entry.model_copy(
            update={
                "status": "failed",
                "neo4j_synced": False,
                "error_message": entry.error_message or "processing failed",
            }
        )
        self.add_or_update(failed_entry)

    def _find_first(
        self, predicate: Callable[[ManifestDocumentEntry], bool]
    ) -> ManifestDocumentEntry | None:
        manifest = self.load()
        for entry in manifest.documents:
            if predicate(entry):
                return entry
        return None

    def _find_all(
        self, predicate: Callable[[ManifestDocumentEntry], bool]
    ) -> list[ManifestDocumentEntry]:
        manifest = self.load()
        return [entry for entry in manifest.documents if predicate(entry)]

    def _validate_manifest_payload(self, payload: Any) -> Manifest:
        try:
            manifest = Manifest.model_validate(payload)
        except ValidationError as exc:
            raise ManifestError(f"invalid manifest JSON in {self.manifest_path}: {exc}") from exc

        if manifest.schema_version != _MANIFEST_SCHEMA_VERSION:
            raise ManifestError(
                f"unsupported manifest schema version {manifest.schema_version!r}"
            )
        return manifest

    def _normalize_manifest_paths(self, manifest: Manifest) -> Manifest:
        payload = manifest.model_dump(mode="python")
        payload["documents"] = [
            self._normalize_entry_paths(entry).model_dump(mode="python")
            for entry in manifest.documents
        ]
        try:
            normalized_manifest = Manifest.model_validate(payload)
        except ValidationError as exc:
            raise ManifestError(f"invalid manifest payload: {exc}") from exc
        return normalized_manifest

    def _normalize_entry_paths(self, entry: ManifestDocumentEntry) -> ManifestDocumentEntry:
        payload = entry.model_dump(mode="python")
        payload["source_id"] = self.path_resolver.to_storage_path(payload["source_id"])
        payload["file_path"] = self.path_resolver.to_storage_path(payload["file_path"])
        processed_json_path = payload.get("processed_json_path")
        if processed_json_path:
            payload["processed_json_path"] = self.path_resolver.to_storage_path(
                processed_json_path
            )
        try:
            normalized_entry = ManifestDocumentEntry.model_validate(payload)
        except ValidationError as exc:
            raise ManifestError(
                f"invalid manifest entry for document_id={entry.document_id}: {exc}"
            ) from exc
        return normalized_entry
