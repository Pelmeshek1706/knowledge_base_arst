from __future__ import annotations

from pathlib import Path

from personal_kb.chunking import TxtChunker, build_default_chunker_registry
from personal_kb.parsers import TxtParser

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_txt_chunker_uses_fixed_size_chunks_with_overlap() -> None:
    file_path = PROJECT_ROOT / "tests" / "fixtures" / "sample_notes.txt"
    parsed = TxtParser().parse(file_path, source_id="tests/fixtures/sample_notes.txt")

    chunks = TxtChunker(chunk_size=20, chunk_overlap=5).chunk(
        parsed,
        document_id="doc-txt-1",
    )

    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2, 3, 4]
    assert chunks[0].text == "Alpha beta gamma del"
    assert chunks[1].text.startswith("a delta epsilon")
    assert chunks[0].text[-5:] == chunks[1].text[:5]
    assert chunks[0].source_ref.section == "chars:0-20"
    assert chunks[1].source_ref.section == "chars:15-35"


def test_chunker_registry_resolves_txt_extension() -> None:
    registry = build_default_chunker_registry()

    chunker = registry.get_chunker(".txt")

    assert isinstance(chunker, TxtChunker)
