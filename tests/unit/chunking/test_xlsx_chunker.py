from __future__ import annotations

from pathlib import Path

from personal_kb.chunking import XlsxChunker
from personal_kb.parsers import XlsxParser

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_xlsx_chunker_preserves_sheet_and_cell_range_source_refs() -> None:
    file_path = PROJECT_ROOT / "tests" / "fixtures" / "sample_budget.xlsx"
    parsed = XlsxParser().parse(file_path, source_id="tests/fixtures/sample_budget.xlsx")

    chunks = XlsxChunker(chunk_size=40).chunk(parsed, document_id="doc-xlsx-1")

    assert [chunk.source_ref.cell_range for chunk in chunks] == [
        "A1:C1",
        "A2:C2",
        "A3:C3",
        "A5:C5",
        "A6:C6",
        "A7:C7",
        "A1:B3",
    ]
    assert chunks[0].source_ref.sheet == "Budget"
    assert chunks[-1].source_ref.sheet == "Summary"


def test_xlsx_chunker_keeps_small_blocks_as_single_chunks() -> None:
    file_path = PROJECT_ROOT / "tests" / "fixtures" / "sample_budget.xlsx"
    parsed = XlsxParser().parse(file_path, source_id="tests/fixtures/sample_budget.xlsx")

    chunks = XlsxChunker(chunk_size=500).chunk(parsed, document_id="doc-xlsx-2")

    assert len(chunks) == len(parsed.structured_blocks)
    assert chunks[0].text == "Category\tAmount\tNotes\nTravel\t1200\tConference flights\nMeals\t450\tTeam offsite"
