from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import Workbook

from personal_kb.core.errors import ParsingError
from personal_kb.parsers import XlsxParser

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_xlsx_parser_extracts_sheet_and_cell_range_blocks_from_fixture() -> None:
    file_path = PROJECT_ROOT / "tests" / "fixtures" / "sample_budget.xlsx"

    parsed = XlsxParser().parse(file_path, source_id="tests/fixtures/sample_budget.xlsx")

    assert parsed.file_extension == "xlsx"
    assert [block["sheet_name"] for block in parsed.structured_blocks] == [
        "Budget",
        "Budget",
        "Summary",
    ]
    assert [block["cell_range"] for block in parsed.structured_blocks] == [
        "A1:C3",
        "A5:C7",
        "A1:B3",
    ]
    assert parsed.structured_blocks[0]["source_ref"]["sheet"] == "Budget"
    assert "Summary" in parsed.raw_text


def test_xlsx_parser_raises_typed_failure_for_empty_workbook(tmp_path: Path) -> None:
    file_path = tmp_path / "blank.xlsx"
    Workbook().save(file_path)

    with pytest.raises(ParsingError):
        XlsxParser().parse(file_path)
