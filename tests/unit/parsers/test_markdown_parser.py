from __future__ import annotations

from pathlib import Path

from personal_kb.parsers import MarkdownParser, build_default_parser_registry

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_markdown_parser_builds_heading_aware_blocks_from_fixture() -> None:
    file_path = PROJECT_ROOT / "tests" / "fixtures" / "sample_outline.md"

    parsed = MarkdownParser().parse(file_path, source_id="tests/fixtures/sample_outline.md")

    assert parsed.file_extension == "md"
    assert parsed.title == "sample_outline"
    assert [block["heading_path"] for block in parsed.structured_blocks] == [
        ["Overview"],
        ["Overview", "Details"],
        ["Overview", "Details", "Deep Dive"],
        ["Overview", "Wrap Up"],
    ]
    assert parsed.structured_blocks[2]["source_ref"]["section"] == (
        "Overview > Details > Deep Dive"
    )


def test_markdown_parser_handles_real_project_markdown_sample() -> None:
    file_path = PROJECT_ROOT / "data" / "Product_Requirements_Document_Personal_KB_v0.2.md"

    parsed = MarkdownParser().parse(
        file_path,
        source_id="data/Product_Requirements_Document_Personal_KB_v0.2.md",
    )

    heading_paths = [block["heading_path"] for block in parsed.structured_blocks]

    assert parsed.raw_text.startswith("# Product Requirements Document")
    assert parsed.structured_blocks[0]["heading_path"] == [
        "Product Requirements Document — Personal KB Local-First GraphRAG System"
    ]
    assert len(parsed.structured_blocks) >= 20
    assert [
        "Product Requirements Document — Personal KB Local-First GraphRAG System"
    ] in heading_paths
    assert [
        "Product Requirements Document — Personal KB Local-First GraphRAG System",
        "1. Executive Summary",
    ] in heading_paths
    assert [
        "Product Requirements Document — Personal KB Local-First GraphRAG System",
        "1. Executive Summary",
        "Core MVP promise",
    ] in heading_paths
    assert [
        "Product Requirements Document — Personal KB Local-First GraphRAG System",
        "8. Functional Requirements",
        "8.4 Parsers",
    ] in heading_paths
    assert [
        "Product Requirements Document — Personal KB Local-First GraphRAG System",
        "8. Functional Requirements",
        "8.5 Chunking",
    ] in heading_paths
    assert parsed.structured_blocks[0]["source_ref"]["section"] == (
        "Product Requirements Document — Personal KB Local-First GraphRAG System"
    )


def test_parser_registry_resolves_markdown_extension() -> None:
    registry = build_default_parser_registry()

    parser = registry.get_parser("md")

    assert isinstance(parser, MarkdownParser)
