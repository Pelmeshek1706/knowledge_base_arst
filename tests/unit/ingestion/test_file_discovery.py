from __future__ import annotations

from pathlib import Path

from personal_kb.core.ids import make_document_id
from personal_kb.ingestion.file_discovery import FileDiscoveryService


def test_file_discovery_filters_supported_extensions_and_recurses(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "data"
    nested_dir = data_dir / "nested" / "deep"
    nested_dir.mkdir(parents=True)
    (data_dir / "notes.txt").write_text("notes", encoding="utf-8")
    (nested_dir / "report.pdf").write_bytes(b"pdf-bytes")
    (nested_dir / "plan.docx").write_bytes(b"docx-bytes")
    (data_dir / "ignore.png").write_bytes(b"png-bytes")
    (data_dir / "data.json").write_text("{}", encoding="utf-8")

    service = FileDiscoveryService(project_root=tmp_path)
    candidates = service.scan()

    assert [candidate.source_id for candidate in candidates] == [
        "data/nested/deep/plan.docx",
        "data/nested/deep/report.pdf",
        "data/notes.txt",
    ]
    assert {candidate.file_extension for candidate in candidates} == {
        "docx",
        "pdf",
        "txt",
    }
    assert all(candidate.raw_bytes_hash for candidate in candidates)
    assert all(
        candidate.document_id
        == make_document_id(candidate.source_id, candidate.raw_bytes_hash)
        for candidate in candidates
    )
    assert "data/ignore.png" not in {candidate.source_id for candidate in candidates}
    assert "data/data.json" not in {candidate.source_id for candidate in candidates}
