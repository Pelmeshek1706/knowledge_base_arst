from __future__ import annotations

from pathlib import Path

from personal_kb.chunking import MarkdownChunker, build_default_chunker_registry
from personal_kb.parsers import MarkdownParser

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_markdown_chunker_preserves_heading_hierarchy() -> None:
    file_path = PROJECT_ROOT / "tests" / "fixtures" / "sample_outline.md"
    parsed = MarkdownParser().parse(file_path, source_id="tests/fixtures/sample_outline.md")

    chunks = MarkdownChunker(chunk_size=200, chunk_overlap=25).chunk(
        parsed,
        document_id="doc-md-1",
    )

    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2, 3]
    assert chunks[1].source_ref.section == "Overview > Details"
    assert chunks[1].text.startswith("Overview > Details")
    assert chunks[2].source_ref.section == "Overview > Details > Deep Dive"


def test_markdown_chunker_only_splits_oversized_sections() -> None:
    file_path = PROJECT_ROOT / "tests" / "fixtures" / "oversized_section.md"
    parsed = MarkdownParser().parse(file_path, source_id="tests/fixtures/oversized_section.md")

    chunks = MarkdownChunker(chunk_size=80, chunk_overlap=10).chunk(
        parsed,
        document_id="doc-md-2",
    )

    assert [chunk.source_ref.section for chunk in chunks] == [
        "Short",
        "Large",
        "Large",
        "Large",
    ]
    large_chunks = chunks[1:]

    assert all(chunk.text.startswith("Large\n\n") for chunk in large_chunks)
    assert large_chunks[0].text.endswith(large_chunks[1].text[7:17])
    assert large_chunks[1].text.endswith(large_chunks[2].text[7:17])


def test_chunker_registry_resolves_markdown_extension() -> None:
    registry = build_default_chunker_registry()

    chunker = registry.get_chunker("md")

    assert isinstance(chunker, MarkdownChunker)
