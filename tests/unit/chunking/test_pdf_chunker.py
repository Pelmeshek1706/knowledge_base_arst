from __future__ import annotations

from pathlib import Path

from personal_kb.chunking import PdfChunker, build_default_chunker_registry
from personal_kb.parsers import PdfParser

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_pdf_chunker_preserves_page_refs_and_only_splits_within_pages() -> None:
    file_path = PROJECT_ROOT / "tests" / "fixtures" / "openwillis_speech_dataset_feature_reference.pdf"
    parsed = PdfParser().parse(
        file_path,
        source_id="tests/fixtures/openwillis_speech_dataset_feature_reference.pdf",
    )

    chunks = PdfChunker(chunk_size=1500, chunk_overlap=100).chunk(
        parsed,
        document_id="doc-pdf-1",
    )

    assert len(chunks) > len(parsed.structured_blocks)
    assert [chunk.source_ref.page for chunk in chunks[:4]] == [1, 1, 2, 2]
    assert [chunk.source_ref.page for chunk in chunks] == sorted(
        chunk.source_ref.page for chunk in chunks
    )
    assert all(
        chunk.source_ref.file_path == "tests/fixtures/openwillis_speech_dataset_feature_reference.pdf"
        for chunk in chunks
    )


def test_chunker_registry_resolves_pdf_docx_and_xlsx_extensions() -> None:
    registry = build_default_chunker_registry()

    assert isinstance(registry.get_chunker("pdf"), PdfChunker)
    assert registry.is_supported(".docx")
    assert registry.is_supported("xlsx")
