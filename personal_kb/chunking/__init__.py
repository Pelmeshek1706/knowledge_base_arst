"""Chunking package for personal_kb."""

from personal_kb.chunking.base import BaseChunker
from personal_kb.chunking.docx_chunker import DocxChunker
from personal_kb.chunking.markdown_chunker import MarkdownChunker
from personal_kb.chunking.registry import ChunkerRegistry, build_default_chunker_registry
from personal_kb.chunking.pdf_chunker import PdfChunker
from personal_kb.chunking.xlsx_chunker import XlsxChunker
from personal_kb.chunking.txt_chunker import TxtChunker

__all__ = [
    "BaseChunker",
    "DocxChunker",
    "ChunkerRegistry",
    "MarkdownChunker",
    "PdfChunker",
    "XlsxChunker",
    "TxtChunker",
    "build_default_chunker_registry",
]
