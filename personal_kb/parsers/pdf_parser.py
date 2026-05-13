from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import fitz  # type: ignore[import-untyped]
import pdfplumber

from personal_kb.core.errors import ParsingError
from personal_kb.parsers.base import BaseParser
from personal_kb.schemas.document import ParsedDocument

_INLINE_WHITESPACE_RE = re.compile(r"[^\S\n]+")


class PdfParser(BaseParser):
    supported_extensions = ("pdf",)

    def parse(self, file_path: Path, *, source_id: str | None = None) -> ParsedDocument:
        normalized_source_id = self._normalize_source_id(file_path, source_id)

        primary_error: Exception | None = None
        try:
            raw_text, blocks = self._extract_with_pdfplumber(file_path, normalized_source_id)
        except Exception as exc:  # pragma: no cover - fallback path verified in tests
            primary_error = exc
            raw_text, blocks = "", []

        if not self._has_usable_text(raw_text):
            try:
                raw_text, blocks = self._extract_with_pymupdf(file_path, normalized_source_id)
            except Exception as exc:  # pragma: no cover - defensive fallback
                message = f"failed to extract text from pdf {normalized_source_id}: {exc}"
                if primary_error is not None:
                    raise ParsingError(message) from primary_error
                raise ParsingError(message) from exc

        if not self._has_usable_text(raw_text):
            raise ParsingError(
                f"pdf text extraction produced no usable text for {normalized_source_id}; "
                "OCR is out of scope"
            )

        return ParsedDocument(
            source_id=normalized_source_id,
            file_path=normalized_source_id,
            file_name=file_path.name,
            file_extension="pdf",
            title=file_path.stem,
            raw_text=raw_text,
            metadata=self._build_metadata(file_path),
            structured_blocks=blocks,
        )

    def _extract_with_pdfplumber(
        self, file_path: Path, source_id: str
    ) -> tuple[str, list[dict[str, Any]]]:
        blocks: list[dict[str, Any]] = []
        page_texts: list[str] = []

        with pdfplumber.open(file_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                page_text = self._normalize_text(page.extract_text(layout=True) or "")
                if not page_text:
                    continue
                page_texts.append(page_text)
                blocks.append(
                    {
                        "type": "pdf_page",
                        "page_number": page_number,
                        "text": page_text,
                        "source_ref": {
                            "file_path": source_id,
                            "page": page_number,
                        },
                    }
                )

        return "\n\n".join(page_texts).strip(), blocks

    def _extract_with_pymupdf(
        self, file_path: Path, source_id: str
    ) -> tuple[str, list[dict[str, Any]]]:
        blocks: list[dict[str, Any]] = []
        page_texts: list[str] = []

        with fitz.open(file_path) as document:
            for page_number, page in enumerate(document, start=1):
                page_text = self._normalize_text(page.get_text("text") or "")
                if not page_text:
                    continue
                page_texts.append(page_text)
                blocks.append(
                    {
                        "type": "pdf_page",
                        "page_number": page_number,
                        "text": page_text,
                        "source_ref": {
                            "file_path": source_id,
                            "page": page_number,
                        },
                    }
                )

        return "\n\n".join(page_texts).strip(), blocks

    def _normalize_text(self, text: str) -> str:
        normalized_lines: list[str] = []
        previous_blank = False

        for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            normalized_line = _INLINE_WHITESPACE_RE.sub(" ", line).strip()
            if not normalized_line:
                if previous_blank:
                    continue
                normalized_lines.append("")
                previous_blank = True
                continue

            normalized_lines.append(normalized_line)
            previous_blank = False

        return "\n".join(normalized_lines).strip()

    def _has_usable_text(self, text: str) -> bool:
        return bool(text.strip()) and bool(re.search(r"[A-Za-z0-9]", text))
