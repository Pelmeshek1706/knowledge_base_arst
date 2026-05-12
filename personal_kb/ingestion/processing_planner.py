from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

from personal_kb.core.time import to_utc_datetime
from personal_kb.schemas.manifest import Manifest, ManifestDocumentEntry
from personal_kb.schemas.processing import (
    DiscoveredFile,
    ProcessingAction,
    ProcessingDecision,
    ProcessingPlan,
)
from personal_kb.schemas.relationships import RelationshipType

from personal_kb.ingestion.duplicate_detector import DuplicateDetector


class ProcessingPlanner:
    """Decide skip/version/duplicate/new behavior before expensive processing."""

    def __init__(self, duplicate_detector: DuplicateDetector | None = None) -> None:
        self.duplicate_detector = duplicate_detector or DuplicateDetector()

    def plan(
        self,
        candidate: DiscoveredFile,
        manifest: Manifest,
        allow_failed_retry: bool = False,
    ) -> ProcessingDecision:
        latest_source_entry = self._latest_source_entry(manifest, candidate.source_id)
        if latest_source_entry is not None:
            return self._plan_against_source_entry(
                candidate, latest_source_entry, allow_failed_retry
            )

        duplicates = self.duplicate_detector.find_exact_duplicates(
            candidate.raw_bytes_hash,
            manifest,
            source_id=candidate.source_id,
        )
        if duplicates:
            canonical = self.duplicate_detector.choose_canonical(duplicates)
            return ProcessingDecision(
                candidate=candidate,
                action=ProcessingAction.DUPLICATE_OF,
                reason="different source_id with an existing raw-bytes hash match",
                matched_document_id=canonical.document_id,
                related_document_id=canonical.document_id,
                relationship_type=cast(RelationshipType, "DUPLICATE_OF"),
                retry_allowed=False,
            )

        return ProcessingDecision(
            candidate=candidate,
            action=ProcessingAction.PROCESS_NEW,
            reason="no manifest entry matched source_id or raw_bytes_hash",
            retry_allowed=False,
        )

    def plan_batch(
        self,
        candidates: list[DiscoveredFile],
        manifest: Manifest,
        allow_failed_retry: bool = False,
    ) -> ProcessingPlan:
        return ProcessingPlan(
            decisions=[
                self.plan(candidate, manifest, allow_failed_retry=allow_failed_retry)
                for candidate in candidates
            ]
        )

    def _plan_against_source_entry(
        self,
        candidate: DiscoveredFile,
        source_entry: ManifestDocumentEntry,
        allow_failed_retry: bool,
    ) -> ProcessingDecision:
        if candidate.raw_bytes_hash == source_entry.raw_bytes_hash:
            if source_entry.status == "failed" and allow_failed_retry:
                return ProcessingDecision(
                    candidate=candidate,
                    action=ProcessingAction.RETRY_FAILED,
                    reason="failed source entry may be retried when retry is allowed",
                    matched_document_id=source_entry.document_id,
                    retry_allowed=True,
                )
            if source_entry.status == "failed":
                return ProcessingDecision(
                    candidate=candidate,
                    action=ProcessingAction.SKIP,
                    reason="previous source entry failed and retry was not allowed",
                    matched_document_id=source_entry.document_id,
                    retry_allowed=False,
                )
            return ProcessingDecision(
                candidate=candidate,
                action=ProcessingAction.SKIP,
                reason="same source_id and same raw_bytes_hash already exist",
                matched_document_id=source_entry.document_id,
                retry_allowed=False,
            )

        return ProcessingDecision(
            candidate=candidate,
            action=ProcessingAction.NEWER_VERSION_OF,
            reason="same source_id with a changed raw_bytes_hash",
            matched_document_id=source_entry.document_id,
            related_document_id=source_entry.document_id,
            relationship_type=cast(RelationshipType, "NEWER_VERSION_OF"),
            retry_allowed=False,
        )

    def _latest_source_entry(
        self, manifest: Manifest, source_id: str
    ) -> ManifestDocumentEntry | None:
        source_entries = [
            entry for entry in manifest.documents if entry.source_id == source_id
        ]
        if not source_entries:
            return None
        return max(source_entries, key=self._source_sort_key)

    def _source_sort_key(
        self, entry: ManifestDocumentEntry
    ) -> tuple[datetime, datetime, str]:
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
