from __future__ import annotations

from datetime import UTC, datetime

from personal_kb.core.errors import ManifestError
from personal_kb.core.time import to_utc_datetime
from personal_kb.schemas.manifest import Manifest, ManifestDocumentEntry


class DuplicateDetector:
    """Find exact raw-byte duplicates and choose a canonical manifest entry."""

    def find_exact_duplicates(
        self,
        raw_bytes_hash: str,
        manifest: Manifest,
        source_id: str | None = None,
    ) -> list[ManifestDocumentEntry]:
        duplicates = [
            entry
            for entry in manifest.documents
            if entry.raw_bytes_hash == raw_bytes_hash and entry.status != "failed"
        ]
        if source_id is not None:
            duplicates = [entry for entry in duplicates if entry.source_id != source_id]
        return duplicates

    def choose_canonical(
        self, entries: list[ManifestDocumentEntry]
    ) -> ManifestDocumentEntry:
        if not entries:
            raise ManifestError("cannot choose a canonical document from no entries")
        return max(entries, key=self._canonical_sort_key)

    def choose_canonical_document_id(
        self, entries: list[ManifestDocumentEntry]
    ) -> str:
        return self.choose_canonical(entries).document_id

    def _canonical_sort_key(self, entry: ManifestDocumentEntry) -> tuple[datetime, datetime, str]:
        modified_at = (
            to_utc_datetime(entry.modified_at)
            if entry.modified_at is not None
            else datetime.min.replace(tzinfo=UTC)
        )
        ingested_at = (
            to_utc_datetime(entry.ingested_at)
            if entry.ingested_at is not None
            else datetime.min.replace(tzinfo=UTC)
        )
        return (modified_at, ingested_at, entry.document_id)
