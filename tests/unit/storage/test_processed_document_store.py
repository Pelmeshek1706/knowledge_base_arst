from __future__ import annotations

from pathlib import Path

import pytest

from personal_kb.core.errors import ManifestError
from personal_kb.schemas.chunk import ChunkRecord
from personal_kb.schemas.common import SourceRef
from personal_kb.schemas.document import DocumentRecord
from personal_kb.schemas.entity import EntityRecord
from personal_kb.schemas.processing import ProcessingMetadata, ProcessedDocument
from personal_kb.schemas.tag import TagRecord
from personal_kb.storage.processed_document_store import ProcessedDocumentStore


def _build_processed_document(project_root: Path, document_id: str) -> ProcessedDocument:
    source_path = project_root / "data" / f"{document_id}.md"
    tag = TagRecord(name="Budget Review", normalized_name="Budget Review", confidence=1.0)
    entity = EntityRecord(
        name="Penelope",
        normalized_name="Penelope",
        type="Person",
        confidence=0.91,
    )
    source_ref = SourceRef(file_path=source_path.as_posix(), section="Overview")
    document = DocumentRecord(
        document_id=document_id,
        source_id=source_path.as_posix(),
        file_path=source_path.as_posix(),
        file_name=f"{document_id}.md",
        file_extension="md",
        document_type="markdown",
        title="Budget Review",
        ingested_at="2026-05-09T12:00:00Z",
        raw_bytes_hash=f"raw-{document_id}",
        extracted_text_hash=f"text-{document_id}",
        content_hash=f"content-{document_id}",
        tags=[tag],
        entities=[entity],
    )
    chunk = ChunkRecord(
        document_id=document_id,
        chunk_index=0,
        text="Budget planning notes",
        source_ref=source_ref,
        tags=[tag],
        entities=[entity],
    )
    return ProcessedDocument(
        document=document,
        raw_text="Budget planning notes",
        chunks=[chunk],
        processing=ProcessingMetadata(
            parser="markdown_parser",
            chunker="markdown_chunker",
            processed_at="2026-05-09T12:05:00Z",
        ),
    )


def test_processed_document_store_roundtrip_and_iterates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ProcessedDocumentStore(project_root=tmp_path)
    first = _build_processed_document(tmp_path, "doc-1")
    second = _build_processed_document(tmp_path, "doc-2")

    saved_first = store.save(first)
    saved_second = store.save(second)

    assert saved_first == store.documents_dir / "doc-1.json"
    assert saved_second == store.documents_dir / "doc-2.json"
    assert store.exists("doc-1") is True
    assert store.exists("missing") is False

    loaded = store.load("doc-1")
    assert loaded.document.document_id == "doc-1"
    assert loaded.document.file_path == "data/doc-1.md"
    assert loaded.chunks[0].source_ref.file_path == "data/doc-1.md"

    iterated_ids = [document.document.document_id for document in store.iter_documents()]
    assert iterated_ids == ["doc-1", "doc-2"]


def test_processed_document_store_save_uses_atomic_replace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ProcessedDocumentStore(project_root=tmp_path)
    document = _build_processed_document(tmp_path, "doc-1")

    replace_calls: list[tuple[str, str]] = []

    def fake_replace(src: str | Path, dst: str | Path) -> None:
        src_path = Path(src)
        dst_path = Path(dst)
        replace_calls.append((src_path.name, dst_path.name))
        dst_path.write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")
        src_path.unlink(missing_ok=True)

    monkeypatch.setattr("personal_kb.storage.json_store.os.replace", fake_replace)

    store.save(document)

    assert replace_calls
    assert replace_calls[0][1] == "doc-1.json"
    assert store.exists("doc-1")


def test_processed_document_store_rejects_invalid_json(tmp_path: Path) -> None:
    store = ProcessedDocumentStore(project_root=tmp_path)
    document_path = store.documents_dir / "doc-1.json"
    document_path.parent.mkdir(parents=True, exist_ok=True)
    document_path.write_text("not-json", encoding="utf-8")

    with pytest.raises(ManifestError):
        store.load("doc-1")


def test_processed_document_store_rejects_invalid_schema(tmp_path: Path) -> None:
    store = ProcessedDocumentStore(project_root=tmp_path)
    document_path = store.documents_dir / "doc-1.json"
    document_path.parent.mkdir(parents=True, exist_ok=True)
    document_path.write_text(
        """
{
  "schema_version": "0.2",
  "document": {"document_id": "doc-1"},
  "raw_text": "x",
  "chunks": [],
  "relationships": [],
  "processing": {
    "parser": "markdown_parser",
    "chunker": "markdown_chunker",
    "processed_at": "2026-05-09T12:05:00Z"
  }
}
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ManifestError):
        store.load("doc-1")
