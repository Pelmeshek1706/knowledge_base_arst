from __future__ import annotations

from personal_kb.chunking.base import BaseChunker
from personal_kb.schemas.chunk import ChunkRecord
from personal_kb.schemas.common import SourceRef
from personal_kb.schemas.document import ParsedDocument


class TxtChunker(BaseChunker):
    supported_extensions = ("txt",)

    def __init__(self, *, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk(self, document: ParsedDocument, *, document_id: str) -> list[ChunkRecord]:
        if not document.raw_text:
            return []

        chunks: list[ChunkRecord] = []
        step = self._chunk_size - self._chunk_overlap
        start = 0
        chunk_index = 0

        while start < len(document.raw_text):
            end = min(len(document.raw_text), start + self._chunk_size)
            text = document.raw_text[start:end]
            chunks.append(
                ChunkRecord(
                    document_id=document_id,
                    chunk_index=chunk_index,
                    text=text,
                    char_count=len(text),
                    source_ref=SourceRef(
                        file_path=document.source_id,
                        section=f"chars:{start}-{end}",
                    ),
                )
            )
            if end >= len(document.raw_text):
                break
            start += step
            chunk_index += 1

        return chunks
