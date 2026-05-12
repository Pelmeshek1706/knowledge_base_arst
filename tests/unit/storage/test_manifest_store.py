from __future__ import annotations

from pathlib import Path

import pytest

from personal_kb.core.errors import ManifestError
from personal_kb.schemas.manifest import Manifest, ManifestDocumentEntry
from personal_kb.storage.manifest_store import ManifestStore


def _build_processed_entry(project_root: Path) -> ManifestDocumentEntry:
    source_path = project_root / "data" / "budget.xlsx"
    processed_path = project_root / "kb_storage" / "documents" / "doc-1.json"
    return ManifestDocumentEntry(
        document_id="doc-1",
        source_id=source_path.as_posix(),
        file_path=source_path.as_posix(),
        file_name="budget.xlsx",
        file_extension="xlsx",
        raw_bytes_hash="raw-hash",
        extracted_text_hash="text-hash",
        content_hash="content-hash",
        processed_json_path=processed_path.as_posix(),
        ingested_at="2026-05-09T12:00:00Z",
        modified_at="2026-05-09T12:05:00Z",
        neo4j_synced=False,
        canonical_document_id="doc-1",
        duplicate_of=None,
        newer_version_of=None,
        status="processed",
    )


def test_manifest_store_roundtrip_and_lookups(tmp_path: Path) -> None:
    store = ManifestStore(project_root=tmp_path)
    entry = _build_processed_entry(tmp_path)
    manifest = Manifest(documents=[entry])

    store.save(manifest)

    manifest_text = store.manifest_path.read_text(encoding="utf-8")
    assert manifest_text.startswith("{\n  ")
    assert '"documents": [' in manifest_text
    assert '"file_path": "data/budget.xlsx"' in manifest_text
    assert '"processed_json_path": "kb_storage/documents/doc-1.json"' in manifest_text

    loaded = store.load()
    assert loaded.documents[0].file_path == "data/budget.xlsx"
    assert loaded.documents[0].processed_json_path == "kb_storage/documents/doc-1.json"
    assert store.get_by_document_id("doc-1") is not None
    assert store.get_by_source_id(tmp_path / "data" / "budget.xlsx")
    assert store.get_by_raw_bytes_hash("raw-hash")
    assert store.get_by_extracted_text_hash("text-hash")
    assert store.get_by_content_hash("content-hash")


def test_manifest_store_save_uses_atomic_replace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ManifestStore(project_root=tmp_path)
    entry = _build_processed_entry(tmp_path)
    manifest = Manifest(documents=[entry])

    replace_calls: list[tuple[str, str]] = []

    def fake_replace(src: str | Path, dst: str | Path) -> None:
        src_path = Path(src)
        dst_path = Path(dst)
        replace_calls.append((src_path.name, dst_path.name))
        dst_path.write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")
        src_path.unlink(missing_ok=True)

    monkeypatch.setattr("personal_kb.storage.json_store.os.replace", fake_replace)

    store.save(manifest)

    assert replace_calls
    assert replace_calls[0][1] == "manifest.json"
    assert store.manifest_path.exists()


def test_manifest_store_persists_failed_entries(tmp_path: Path) -> None:
    store = ManifestStore(project_root=tmp_path)
    source_path = tmp_path / "data" / "broken.pdf"
    failed_entry = ManifestDocumentEntry(
        document_id="doc-failed",
        source_id=source_path.as_posix(),
        file_path=source_path.as_posix(),
        status="failed",
        error_message="Parser failed: unreadable PDF",
        neo4j_synced=False,
    )

    store.mark_failed(failed_entry)

    loaded = store.load()
    assert len(loaded.documents) == 1
    persisted = loaded.documents[0]
    assert persisted.status == "failed"
    assert persisted.error_message == "Parser failed: unreadable PDF"
    assert persisted.neo4j_synced is False
    assert persisted.file_name is None
    assert persisted.raw_bytes_hash is None


def test_manifest_store_rejects_corrupt_json(tmp_path: Path) -> None:
    store = ManifestStore(project_root=tmp_path)
    store.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    store.manifest_path.write_text('{"schema_version": "0.2", "documents": [}', encoding="utf-8")

    with pytest.raises(ManifestError):
        store.load()
