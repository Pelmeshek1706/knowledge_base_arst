from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, Iterator

import mammoth  # type: ignore[import-untyped]
from bs4 import BeautifulSoup, NavigableString, Tag
from docx import Document
from docx.document import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph

from personal_kb.core.errors import ParsingError
from personal_kb.parsers.base import BaseParser
from personal_kb.schemas.document import ParsedDocument

_INLINE_WHITESPACE_RE = re.compile(r"[^\S\n]+")
_NUMBERED_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)[.)]?\s+(.+?)\s*$")
_ANNOTATION_TAG_RE = re.compile(r"\s*#[@§][^@§]+[@§]#\s*")


class DocxParser(BaseParser):
    supported_extensions = ("docx",)

    def parse(self, file_path: Path, *, source_id: str | None = None) -> ParsedDocument:
        normalized_source_id = self._normalize_source_id(file_path, source_id)

        primary_error: Exception | None = None
        try:
            raw_text, blocks = self._extract_with_mammoth(file_path, normalized_source_id)
        except Exception as exc:  # pragma: no cover - fallback path verified in tests
            primary_error = exc
            raw_text, blocks = "", []

        if not self._has_usable_text(raw_text):
            try:
                raw_text, blocks = self._extract_with_python_docx(
                    file_path, normalized_source_id
                )
            except Exception as exc:  # pragma: no cover - defensive fallback
                message = f"failed to extract text from docx {normalized_source_id}: {exc}"
                if primary_error is not None:
                    raise ParsingError(message) from primary_error
                raise ParsingError(message) from exc

        if not self._has_usable_text(raw_text):
            raise ParsingError(
                f"docx text extraction produced no usable text for {normalized_source_id}"
            )

        return ParsedDocument(
            source_id=normalized_source_id,
            file_path=normalized_source_id,
            file_name=file_path.name,
            file_extension="docx",
            title=file_path.stem,
            raw_text=raw_text,
            metadata=self._build_metadata(file_path),
            structured_blocks=blocks,
        )

    def _extract_with_mammoth(
        self, file_path: Path, source_id: str
    ) -> tuple[str, list[dict[str, Any]]]:
        with file_path.open("rb") as handle:
            html = mammoth.convert_to_html(handle).value
        return self._build_blocks_from_html(html, source_id)

    def _extract_with_python_docx(
        self, file_path: Path, source_id: str
    ) -> tuple[str, list[dict[str, Any]]]:
        document = Document(str(file_path))
        return self._build_blocks_from_docx(document, source_id)

    def _build_blocks_from_html(
        self, html: str, source_id: str
    ) -> tuple[str, list[dict[str, Any]]]:
        soup = BeautifulSoup(html, "html.parser")
        container = soup.body or soup
        return self._build_blocks_from_elements(container.children, source_id)

    def _build_blocks_from_docx(
        self, document: DocxDocument, source_id: str
    ) -> tuple[str, list[dict[str, Any]]]:
        return self._build_blocks_from_elements(
            self._iter_docx_elements(document), source_id
        )

    def _build_blocks_from_elements(
        self, elements: Iterable[Any], source_id: str
    ) -> tuple[str, list[dict[str, Any]]]:
        raw_lines: list[str] = []
        blocks: list[dict[str, Any]] = []
        heading_stack: list[str] = []
        current_heading_path: list[str] = []
        current_heading_level: int | None = None
        current_lines: list[str] = []

        def flush_section() -> None:
            if not current_lines:
                return
            text = self._normalize_text("\n".join(current_lines))
            if not text:
                return
            blocks.append(
                {
                    "type": "docx_section",
                    "heading_level": current_heading_level,
                    "heading_path": list(current_heading_path),
                    "text": text,
                    "source_ref": {
                        "file_path": source_id,
                        "section": " > ".join(current_heading_path) or None,
                    },
                }
            )

        for element in elements:
            if isinstance(element, NavigableString):
                continue

            if isinstance(element, Tag) and element.name == "table":
                table_text = self._extract_html_table_text(element)
                if table_text:
                    raw_lines.append(table_text)
                    current_lines.extend(table_text.splitlines())
                continue

            if isinstance(element, Table):
                table_text = self._extract_docx_table_text(element)
                if table_text:
                    raw_lines.append(table_text)
                    current_lines.extend(table_text.splitlines())
                continue

            text = self._normalize_text(self._element_text(element))
            if not text:
                continue

            raw_lines.append(text)
            if self._is_heading_candidate(element, text):
                flush_section()
                current_heading_level, current_heading_path = self._update_heading_stack(
                    heading_stack, text
                )
                current_lines = []
                continue

            current_lines.append(text)

        flush_section()
        return self._normalize_text("\n".join(raw_lines)), blocks

    def _iter_docx_elements(self, document: DocxDocument) -> Iterator[Paragraph | Table]:
        for child in document.element.body.iterchildren():
            if child.tag.endswith("}p"):
                yield Paragraph(child, document)
            elif child.tag.endswith("}tbl"):
                yield Table(child, document)

    def _element_text(self, element: Any) -> str:
        if isinstance(element, Paragraph):
            return element.text
        if isinstance(element, Tag):
            return element.get_text(" ", strip=True)
        return str(element)

    def _extract_html_table_text(self, table: Tag) -> str:
        rows: list[str] = []
        for row in table.find_all("tr", recursive=False):
            cells: list[str] = []
            for cell in row.find_all(["th", "td"], recursive=False):
                cells.append(self._normalize_text(cell.get_text(" ", strip=True)))
            if any(cells):
                rows.append("\t".join(cells))
        return "\n".join(rows).strip()

    def _extract_docx_table_text(self, table: Table) -> str:
        rows: list[str] = []
        for row in table.rows:
            cells = [self._normalize_text(cell.text) for cell in row.cells]
            if any(cells):
                rows.append("\t".join(cells))
        return "\n".join(rows).strip()

    def _is_heading_candidate(self, element: Any, text: str) -> bool:
        if len(text) > 180:
            return False

        style_name = getattr(getattr(element, "style", None), "name", "") or ""
        if style_name.lower().startswith("heading") or style_name.lower() in {
            "title",
            "subtitle",
        }:
            return True

        if _NUMBERED_HEADING_RE.match(text):
            return True

        if isinstance(element, Tag):
            strong_text = self._collect_strong_text(element)
            if strong_text and strong_text == text:
                return True

        if isinstance(element, Paragraph):
            if self._is_prominent_paragraph(element, text):
                return True

        return False

    def _is_prominent_paragraph(self, paragraph: Paragraph, text: str) -> bool:
        if not paragraph.runs:
            return False

        bold_run_count = sum(1 for run in paragraph.runs if run.bold)
        if bold_run_count and bold_run_count >= max(1, len(paragraph.runs) // 2):
            return True
        if text.isupper() and len(text.split()) <= 12:
            return True
        if len(text) <= 80 and text[:1].isupper() and any(char.isdigit() for char in text):
            return True
        return False

    def _collect_strong_text(self, element: Tag) -> str:
        strong_nodes = element.find_all(["strong", "b"], recursive=True)
        if not strong_nodes:
            return ""
        return self._normalize_text(
            " ".join(node.get_text(" ", strip=True) for node in strong_nodes)
        )

    def _update_heading_stack(
        self, heading_stack: list[str], heading_text: str
    ) -> tuple[int | None, list[str]]:
        match = _NUMBERED_HEADING_RE.match(heading_text)
        if match:
            depth = len(match.group(1).split("."))
            heading_stack[:] = heading_stack[: depth - 1]
            heading_stack.append(self._strip_annotation_tags(match.group(2).strip()))
            return depth, list(heading_stack)

        heading_stack[:] = [self._strip_annotation_tags(heading_text)]
        return 1, list(heading_stack)

    def _strip_annotation_tags(self, text: str) -> str:
        cleaned = _ANNOTATION_TAG_RE.sub(" ", text)
        return self._normalize_text(cleaned)

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
