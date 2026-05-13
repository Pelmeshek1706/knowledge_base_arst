from __future__ import annotations

from pathlib import Path

import fitz
import pytest

import personal_kb.parsers.pdf_parser as pdf_parser_module
from personal_kb.core.errors import ParsingError
from personal_kb.parsers import PdfParser, build_default_parser_registry

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_pdf_parser_extracts_page_text_and_page_refs_from_copied_fixture() -> None:
    file_path = PROJECT_ROOT / "tests" / "fixtures" / "openwillis_speech_dataset_feature_reference.pdf"

    parsed = PdfParser().parse(
        file_path,
        source_id="tests/fixtures/openwillis_speech_dataset_feature_reference.pdf",
    )

    assert parsed.file_extension == "pdf"
    assert len(parsed.structured_blocks) == 7
    assert [block["page_number"] for block in parsed.structured_blocks] == [1, 2, 3, 4, 5, 6, 7]
    assert parsed.structured_blocks[0]["source_ref"]["page"] == 1
    assert parsed.structured_blocks[-1]["source_ref"]["page"] == 7
    assert "Speech characteristics v3.3" in parsed.raw_text


def test_pdf_parser_falls_back_to_pymupdf_when_pdfplumber_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_path = PROJECT_ROOT / "tests" / "fixtures" / "openwillis_speech_dataset_feature_reference.pdf"

    def raise_primary(*args, **kwargs):
        raise RuntimeError("pdfplumber failed")

    monkeypatch.setattr(pdf_parser_module.pdfplumber, "open", raise_primary)

    parsed = PdfParser().parse(
        file_path,
        source_id="tests/fixtures/openwillis_speech_dataset_feature_reference.pdf",
    )

    assert len(parsed.structured_blocks) == 7
    assert parsed.structured_blocks[0]["source_ref"]["page"] == 1
    assert parsed.structured_blocks[0]["source_ref"]["file_path"] == (
        "tests/fixtures/openwillis_speech_dataset_feature_reference.pdf"
    )


def test_pdf_parser_raises_typed_failure_for_empty_pdf(tmp_path: Path) -> None:
    file_path = tmp_path / "blank.pdf"
    document = fitz.open()
    document.new_page()
    document.save(file_path)
    document.close()

    with pytest.raises(ParsingError):
        PdfParser().parse(file_path)


def test_parser_registry_resolves_pdf_docx_and_xlsx_extensions() -> None:
    registry = build_default_parser_registry()

    assert isinstance(registry.get_parser(".pdf"), PdfParser)
    assert registry.is_supported("docx")
    assert registry.is_supported(".xlsx")
