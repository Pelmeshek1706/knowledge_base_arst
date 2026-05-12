from __future__ import annotations

from pathlib import Path

from personal_kb.parsers import TxtParser, build_default_parser_registry


def test_txt_parser_reads_text_and_metadata(tmp_path: Path) -> None:
    file_path = tmp_path / "notes.txt"
    file_path.write_text("plain text body", encoding="utf-8")

    parsed = TxtParser().parse(file_path, source_id="data/notes.txt")

    assert parsed.source_id == "data/notes.txt"
    assert parsed.file_extension == "txt"
    assert parsed.title == "notes"
    assert parsed.raw_text == "plain text body"
    assert parsed.structured_blocks == [
        {
            "type": "text_block",
            "text": "plain text body",
            "source_ref": {
                "file_path": "data/notes.txt",
                "section": "full_text",
            },
        }
    ]
    assert parsed.metadata.size_bytes == len("plain text body")


def test_txt_parser_normalizes_whitespace_noise(tmp_path: Path) -> None:
    file_path = tmp_path / "messy_notes.txt"
    file_path.write_text(
        " Alpha\t\tbeta  gamma \n\n\nDelta\t epsilon \r\n  \r\nZeta    eta\t",
        encoding="utf-8",
    )

    parsed = TxtParser().parse(file_path, source_id="data/messy_notes.txt")

    assert parsed.raw_text == "Alpha beta gamma\n\nDelta epsilon\n\nZeta eta"
    assert parsed.structured_blocks == [
        {
            "type": "text_block",
            "text": "Alpha beta gamma\n\nDelta epsilon\n\nZeta eta",
            "source_ref": {
                "file_path": "data/messy_notes.txt",
                "section": "full_text",
            },
        }
    ]


def test_parser_registry_resolves_txt_extension() -> None:
    registry = build_default_parser_registry()

    parser = registry.get_parser(".txt")

    assert isinstance(parser, TxtParser)
