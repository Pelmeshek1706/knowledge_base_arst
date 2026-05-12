from __future__ import annotations

from typing import Any

from personal_kb.chunking.base import BaseChunker
from personal_kb.schemas.chunk import ChunkRecord
from personal_kb.schemas.common import SourceRef
from personal_kb.schemas.document import ParsedDocument


class MarkdownChunker(BaseChunker):
    supported_extensions = ("md",)

    def __init__(self, *, chunk_size: int = 1200, chunk_overlap: int = 200) -> None:
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
            heading_path = self._as_heading_path(block)
            source_ref = self._as_source_ref(document, block)
            block_text = str(block.get("text", "")).strip()
            if not block_text:
                continue

            section_text = self._compose_section_text(heading_path, block_text)
            if len(section_text) <= self._chunk_size:
                chunks.append(
                    self._make_chunk(
                        document_id=document_id,
                        chunk_index=len(chunks),
                        text=section_text,
                        source_ref=source_ref,
                    )
                )
                continue

            for text in self._split_oversized_section(
                heading_path=heading_path,
                block_text=block_text,
            ):
                chunks.append(
                    self._make_chunk(
                        document_id=document_id,
                        chunk_index=len(chunks),
                        text=text,
                        source_ref=source_ref,
                    )
                )

        return chunks

    def _make_chunk(
        self,
        *,
        document_id: str,
        chunk_index: int,
        text: str,
        source_ref: SourceRef,
    ) -> ChunkRecord:
        return ChunkRecord(
            document_id=document_id,
            chunk_index=chunk_index,
            text=text,
            char_count=len(text),
            source_ref=source_ref,
        )

    def _compose_section_text(self, heading_path: list[str], block_text: str) -> str:
        if not heading_path:
            return block_text
        heading_context = " > ".join(heading_path)
        return f"{heading_context}\n\n{block_text}"

    def _split_oversized_section(
        self,
        *,
        heading_path: list[str],
        block_text: str,
    ) -> list[str]:
        prefix = self._compose_heading_prefix(heading_path)
        body_chunk_size = max(1, self._chunk_size - len(prefix))
        sections: list[str] = []
        body_overlap = min(self._chunk_overlap, body_chunk_size - 1)
        step = body_chunk_size - body_overlap
        start = 0

        while start < len(block_text):
            end = min(len(block_text), start + body_chunk_size)
            sections.append(f"{prefix}{block_text[start:end]}")
            if end >= len(block_text):
                break
            start += step

        return sections

    def _compose_heading_prefix(self, heading_path: list[str]) -> str:
        if not heading_path:
            return ""
        return f"{' > '.join(heading_path)}\n\n"

    def _as_heading_path(self, block: dict[str, Any]) -> list[str]:
        heading_path = block.get("heading_path", [])
        if not isinstance(heading_path, list):
            return []
        return [str(item) for item in heading_path]

    def _as_source_ref(self, document: ParsedDocument, block: dict[str, Any]) -> SourceRef:
        raw_ref = block.get("source_ref")
        if isinstance(raw_ref, dict):
            return SourceRef(
                file_path=str(raw_ref.get("file_path", document.source_id)),
                section=self._optional_str(raw_ref.get("section")),
            )
        return SourceRef(file_path=document.source_id)

    def _optional_str(self, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None
