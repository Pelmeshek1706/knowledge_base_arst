from __future__ import annotations

from pathlib import Path

import pytest
from docx import Document

import personal_kb.parsers.docx_parser as docx_parser_module
from personal_kb.core.errors import ParsingError
from personal_kb.parsers import DocxParser

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_docx_parser_extracts_heading_paths_from_real_fixture() -> None:
    file_path = PROJECT_ROOT / "data" / "DRAFT_Tpl_Application_Form_Part_B_HE_EIC_UKRAINE_2025_AIREST_5.docx"

    parsed = DocxParser().parse(
        file_path,
        source_id="data/DRAFT_Tpl_Application_Form_Part_B_HE_EIC_UKRAINE_2025_AIREST_5.docx",
    )

    heading_paths = [block["heading_path"] for block in parsed.structured_blocks]

    assert parsed.file_extension == "docx"
    assert ["Multimodal Digital Biomarkers for Evidence-Based Mental Health Decision Support and Monitoring"] in heading_paths
    assert ["Excellence", "Technological breakthrough"] in heading_paths
    assert parsed.structured_blocks[2]["source_ref"]["section"] == "Excellence > Technological breakthrough"


def test_docx_parser_falls_back_to_python_docx_when_mammoth_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_path = PROJECT_ROOT / "data" / "DRAFT_Tpl_Application_Form_Part_B_HE_EIC_UKRAINE_2025_AIREST_5.docx"

    def raise_primary(*args, **kwargs):
        raise RuntimeError("mammoth failed")

    monkeypatch.setattr(docx_parser_module.mammoth, "convert_to_html", raise_primary)

    parsed = DocxParser().parse(
        file_path,
        source_id="data/DRAFT_Tpl_Application_Form_Part_B_HE_EIC_UKRAINE_2025_AIREST_5.docx",
    )

    assert ["Excellence", "Technological breakthrough"] in [
        block["heading_path"] for block in parsed.structured_blocks
    ]
    assert parsed.structured_blocks[0]["source_ref"]["file_path"].endswith(".docx")


def test_docx_parser_raises_typed_failure_for_empty_docx(tmp_path: Path) -> None:
    file_path = tmp_path / "blank.docx"
    Document().save(file_path)

    with pytest.raises(ParsingError):
        DocxParser().parse(file_path)
