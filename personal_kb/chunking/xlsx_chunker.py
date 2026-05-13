from __future__ import annotations

from personal_kb.chunking.base import BaseChunker
from personal_kb.schemas.chunk import ChunkRecord
from personal_kb.schemas.common import SourceRef
from personal_kb.schemas.document import ParsedDocument


class XlsxChunker(BaseChunker):
    supported_extensions = ("xlsx",)

    def __init__(self, *, chunk_size: int = 1400, chunk_overlap: int = 0) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk(self, document: ParsedDocument, *, document_id: str) -> list[ChunkRecord]:
        chunks: list[ChunkRecord] = []

        for block in document.structured_blocks:
            text = str(block.get("text", "")).strip()
            if not text:
                continue

            source_ref = self._as_source_ref(document, block)
            if len(text) <= self._chunk_size:
                chunks.append(
                    ChunkRecord(
                        document_id=document_id,
                        chunk_index=len(chunks),
                        text=text,
                        char_count=len(text),
                        source_ref=source_ref,
                    )
                )
                continue

            for chunk_text, chunk_ref in self._split_block(document, block):
                chunks.append(
                    ChunkRecord(
                        document_id=document_id,
                        chunk_index=len(chunks),
                        text=chunk_text,
                        char_count=len(chunk_text),
                        source_ref=chunk_ref,
                    )
                )

        return chunks

    def _split_block(
        self, document: ParsedDocument, block: dict[str, object]
    ) -> list[tuple[str, SourceRef]]:
        text = str(block.get("text", "")).strip()
        rows = text.splitlines()
        start_row = self._optional_int(block.get("start_row"))
        end_row = self._optional_int(block.get("end_row"))
        start_col = self._optional_int(block.get("start_col"))
        end_col = self._optional_int(block.get("end_col"))
        source_ref = self._as_source_ref(document, block)

        if (
            len(rows) <= 1
            or start_row is None
            or end_row is None
            or start_col is None
            or end_col is None
        ):
            return self._split_text(text, source_ref)

        chunks: list[tuple[str, SourceRef]] = []
        current_rows: list[str] = []
        current_start_row = start_row
        current_length = 0

        for index, row_text in enumerate(rows):
            row_length = len(row_text)
            projected_length = row_length if not current_rows else current_length + 1 + row_length
            if current_rows and projected_length > self._chunk_size:
                chunks.append(
                    (
                        "\n".join(current_rows),
                        self._make_source_ref(
                            source_ref,
                            start_col=start_col,
                            end_col=end_col,
                            start_row=current_start_row,
                            end_row=current_start_row + len(current_rows) - 1,
                        ),
                    )
                )
                current_rows = []
                current_start_row = start_row + index
                current_length = 0

            if row_length > self._chunk_size and not current_rows:
                chunks.extend(
                    self._split_text(
                        row_text,
                        self._make_source_ref(
                            source_ref,
                            start_col=start_col,
                            end_col=end_col,
                            start_row=start_row + index,
                            end_row=start_row + index,
                        ),
                    )
                )
                current_start_row = start_row + index + 1
                current_length = 0
                current_rows = []
                continue

            current_rows.append(row_text)
            current_length = projected_length

        if current_rows:
            chunks.append(
                (
                    "\n".join(current_rows),
                    self._make_source_ref(
                        source_ref,
                        start_col=start_col,
                        end_col=end_col,
                        start_row=current_start_row,
                        end_row=current_start_row + len(current_rows) - 1,
                    ),
                )
            )

        return chunks

    def _split_text(self, text: str, source_ref: SourceRef) -> list[tuple[str, SourceRef]]:
        if len(text) <= self._chunk_size:
            return [(text, source_ref)]

        chunks: list[tuple[str, SourceRef]] = []
        step = self._chunk_size - self._chunk_overlap
        start = 0

        while start < len(text):
            end = min(len(text), start + self._chunk_size)
            chunks.append((text[start:end], source_ref))
            if end >= len(text):
                break
            start += step

        return chunks

    def _make_source_ref(
        self,
        source_ref: SourceRef,
        *,
        start_col: int,
        end_col: int,
        start_row: int,
        end_row: int,
    ) -> SourceRef:
        return SourceRef(
            file_path=source_ref.file_path,
            sheet=source_ref.sheet,
            cell_range=f"{self._column_letter(start_col)}{start_row}:{self._column_letter(end_col)}{end_row}",
        )

    def _as_source_ref(self, document: ParsedDocument, block: dict[str, object]) -> SourceRef:
        raw_ref = block.get("source_ref")
        if isinstance(raw_ref, dict):
            return SourceRef(
                file_path=str(raw_ref.get("file_path", document.source_id)),
                sheet=self._optional_str(raw_ref.get("sheet")),
                cell_range=self._optional_str(raw_ref.get("cell_range")),
            )
        return SourceRef(file_path=document.source_id)

    def _column_letter(self, column_index: int) -> str:
        result = ""
        current = column_index
        while current:
            current, remainder = divmod(current - 1, 26)
            result = chr(65 + remainder) + result
        return result

    def _optional_int(self, value: object) -> int | None:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return None
        return None

    def _optional_str(self, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None
