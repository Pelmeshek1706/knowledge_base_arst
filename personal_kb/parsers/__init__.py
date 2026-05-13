"""Parser package for personal_kb."""

from personal_kb.parsers.base import BaseParser
from personal_kb.parsers.docx_parser import DocxParser
from personal_kb.parsers.markdown_parser import MarkdownParser
from personal_kb.parsers.registry import ParserRegistry, build_default_parser_registry
from personal_kb.parsers.pdf_parser import PdfParser
from personal_kb.parsers.xlsx_parser import XlsxParser
from personal_kb.parsers.txt_parser import TxtParser

__all__ = [
    "BaseParser",
    "DocxParser",
    "MarkdownParser",
    "ParserRegistry",
    "PdfParser",
    "XlsxParser",
    "TxtParser",
    "build_default_parser_registry",
]
