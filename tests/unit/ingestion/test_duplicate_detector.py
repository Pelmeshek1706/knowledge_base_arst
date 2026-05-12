from __future__ import annotations

from pathlib import Path

from personal_kb.ingestion.duplicate_detector import DuplicateDetector
from personal_kb.schemas.manifest import Manifest, ManifestDocumentEntry


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


def test_duplicate_detector_filters_failed_entries_and_selects_canonical() -> None:
    detector = DuplicateDetector()
    manifest = Manifest(
        documents=[
            _processed_entry(
                "doc-older",
                "data/original.pdf",
                "same-hash",
                "2026-05-09T12:00:00Z",
                "2026-05-09T12:10:00Z",
            ),
            _processed_entry(
                "doc-newer",
                "data/duplicate.pdf",
                "same-hash",
                "2026-05-09T13:00:00Z",
                "2026-05-09T13:10:00Z",
            ),
            ManifestDocumentEntry(
                document_id="doc-failed",
                source_id="data/failed.pdf",
                file_path="data/failed.pdf",
                status="failed",
                error_message="parser failed",
                raw_bytes_hash="same-hash",
                neo4j_synced=False,
            ),
        ]
    )

    duplicates = detector.find_exact_duplicates(
        "same-hash",
        manifest,
        source_id="data/incoming.pdf",
    )

    assert [entry.document_id for entry in duplicates] == ["doc-older", "doc-newer"]
    assert detector.choose_canonical_document_id(duplicates) == "doc-newer"
