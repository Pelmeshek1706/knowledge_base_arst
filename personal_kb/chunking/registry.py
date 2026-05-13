from __future__ import annotations

from personal_kb.chunking.base import BaseChunker
from personal_kb.chunking.docx_chunker import DocxChunker
from personal_kb.chunking.markdown_chunker import MarkdownChunker
from personal_kb.chunking.pdf_chunker import PdfChunker
from personal_kb.chunking.xlsx_chunker import XlsxChunker
from personal_kb.chunking.txt_chunker import TxtChunker


class ChunkerRegistry:
    def __init__(self) -> None:
        self._chunkers: dict[str, BaseChunker] = {}

    def register(self, chunker: BaseChunker) -> None:
        for extension in chunker.supported_extensions:
            self._chunkers[self._normalize_extension(extension)] = chunker

    def get_chunker(self, extension: str) -> BaseChunker:
        normalized = self._normalize_extension(extension)
        try:
            return self._chunkers[normalized]
        except KeyError as exc:
            raise ValueError(f"unsupported chunker extension: {extension}") from exc

    def is_supported(self, extension: str) -> bool:
        return self._normalize_extension(extension) in self._chunkers

    @staticmethod
    def _normalize_extension(extension: str) -> str:
        return extension.lower().lstrip(".")


def build_default_chunker_registry() -> ChunkerRegistry:
    registry = ChunkerRegistry()
    registry.register(TxtChunker())
    registry.register(MarkdownChunker())
    registry.register(PdfChunker())
    registry.register(DocxChunker())
    registry.register(XlsxChunker())
    return registry
