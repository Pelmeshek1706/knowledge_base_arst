from __future__ import annotations

from personal_kb.chunking.base import BaseChunker
from personal_kb.schemas.chunk import ChunkRecord
from personal_kb.schemas.common import SourceRef
from personal_kb.schemas.document import ParsedDocument


class PdfChunker(BaseChunker):
    supported_extensions = ("pdf",)

    def __init__(self, *, chunk_size: int = 2000, chunk_overlap: int = 200) -> None:
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
            for chunk_text in self._split_text(text):
                chunks.append(
                    ChunkRecord(
                        document_id=document_id,
                        chunk_index=len(chunks),
                        text=chunk_text,
                        char_count=len(chunk_text),
                        source_ref=source_ref,
                    )
                )

        return chunks

    def _split_text(self, text: str) -> list[str]:
        if len(text) <= self._chunk_size:
            return [text]

        chunks: list[str] = []
        step = self._chunk_size - self._chunk_overlap
        start = 0

        while start < len(text):
            end = min(len(text), start + self._chunk_size)
            chunks.append(text[start:end])
            if end >= len(text):
                break
            start += step

        return chunks

    def _as_source_ref(self, document: ParsedDocument, block: dict[str, object]) -> SourceRef:
        raw_ref = block.get("source_ref")
        if isinstance(raw_ref, dict):
            return SourceRef(
                file_path=str(raw_ref.get("file_path", document.source_id)),
                page=self._optional_int(raw_ref.get("page")),
            )
        return SourceRef(file_path=document.source_id)

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
