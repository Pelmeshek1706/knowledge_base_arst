from __future__ import annotations

from pathlib import Path
from typing import cast

from personal_kb.core.ids import make_document_id
from personal_kb.ingestion.processing_planner import ProcessingPlanner
from personal_kb.schemas.document import SupportedFileExtension
from personal_kb.schemas.manifest import Manifest, ManifestDocumentEntry
from personal_kb.schemas.processing import DiscoveredFile, ProcessingAction


def _candidate(source_id: str, raw_bytes_hash: str) -> DiscoveredFile:
    file_extension = cast(SupportedFileExtension, Path(source_id).suffix.lstrip("."))
    return DiscoveredFile(
        document_id=make_document_id(source_id, raw_bytes_hash),
        source_id=source_id,
        source_type="local_file",
        file_path=source_id,
        file_name=Path(source_id).name,
        file_extension=file_extension,
        raw_bytes_hash=raw_bytes_hash,
        size_bytes=123,
        modified_at="2026-05-09T14:00:00Z",
    )


def _processed_entry(
    document_id: str,
    source_id: str,
    raw_bytes_hash: str,
    modified_at: str,
    ingested_at: str,
) -> ManifestDocumentEntry:
    file_name = Path(source_id).name
    file_extension = Path(source_id).suffix.lstrip(".")
    return ManifestDocumentEntry(
        document_id=document_id,
        source_id=source_id,
        file_path=source_id,
        file_name=file_name,
        file_extension=file_extension,
        raw_bytes_hash=raw_bytes_hash,
        extracted_text_hash=f"text-{document_id}",
        content_hash=f"content-{document_id}",
        processed_json_path=f"kb_storage/documents/{document_id}.json",
        ingested_at=ingested_at,
        modified_at=modified_at,
        neo4j_synced=False,
        canonical_document_id=document_id,
        duplicate_of=None,
        newer_version_of=None,
        status="processed",
    )


def _failed_entry(document_id: str, source_id: str, raw_bytes_hash: str) -> ManifestDocumentEntry:
    return ManifestDocumentEntry(
        document_id=document_id,
        source_id=source_id,
        file_path=source_id,
        status="failed",
        error_message="parser failed",
        raw_bytes_hash=raw_bytes_hash,
        neo4j_synced=False,
    )


def test_same_path_same_hash_is_skipped() -> None:
    planner = ProcessingPlanner()
    manifest = Manifest(
        documents=[
            _processed_entry(
                "doc-1",
                "data/budget.pdf",
                "raw-1",
                "2026-05-09T12:00:00Z",
                "2026-05-09T12:10:00Z",
            )
        ]
    )

    decision = planner.plan(_candidate("data/budget.pdf", "raw-1"), manifest)

    assert decision.action == ProcessingAction.SKIP
    assert decision.matched_document_id == "doc-1"
    assert decision.relationship_type is None


def test_same_path_changed_hash_creates_newer_version() -> None:
    planner = ProcessingPlanner()
    manifest = Manifest(
        documents=[
            _processed_entry(
                "doc-older",
                "data/budget.pdf",
                "raw-1",
                "2026-05-09T12:00:00Z",
                "2026-05-09T12:10:00Z",
            )
        ]
    )

    decision = planner.plan(_candidate("data/budget.pdf", "raw-2"), manifest)

    assert decision.action == ProcessingAction.NEWER_VERSION_OF
    assert decision.related_document_id == "doc-older"
    assert decision.relationship_type == "NEWER_VERSION_OF"


def test_different_path_same_hash_creates_duplicate() -> None:
    planner = ProcessingPlanner()
    manifest = Manifest(
        documents=[
            _processed_entry(
                "doc-original",
                "data/original.pdf",
                "raw-1",
                "2026-05-09T12:00:00Z",
                "2026-05-09T12:10:00Z",
            )
        ]
    )

    decision = planner.plan(_candidate("data/copy.pdf", "raw-1"), manifest)

    assert decision.action == ProcessingAction.DUPLICATE_OF
    assert decision.related_document_id == "doc-original"
    assert decision.relationship_type == "DUPLICATE_OF"


def test_failed_entry_requires_retry_flag_for_unchanged_file() -> None:
    planner = ProcessingPlanner()
    manifest = Manifest(
        documents=[_failed_entry("doc-failed", "data/broken.pdf", "raw-1")]
    )

    no_retry_decision = planner.plan(_candidate("data/broken.pdf", "raw-1"), manifest)
    retry_decision = planner.plan(
        _candidate("data/broken.pdf", "raw-1"),
        manifest,
        allow_failed_retry=True,
    )

    assert no_retry_decision.action == ProcessingAction.SKIP
    assert retry_decision.action == ProcessingAction.RETRY_FAILED
    assert retry_decision.retry_allowed is True


def test_failed_entry_allows_new_version_when_file_changed() -> None:
    planner = ProcessingPlanner()
    manifest = Manifest(
        documents=[_failed_entry("doc-failed", "data/broken.pdf", "raw-1")]
    )

    decision = planner.plan(_candidate("data/broken.pdf", "raw-2"), manifest)

    assert decision.action == ProcessingAction.NEWER_VERSION_OF
    assert decision.related_document_id == "doc-failed"
