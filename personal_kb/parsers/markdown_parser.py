from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from personal_kb.parsers.base import BaseParser
from personal_kb.schemas.document import ParsedDocument

_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")


class MarkdownParser(BaseParser):
    supported_extensions = ("md",)

    def parse(self, file_path: Path, *, source_id: str | None = None) -> ParsedDocument:
        normalized_source_id = self._normalize_source_id(file_path, source_id)
        raw_text = file_path.read_text(encoding="utf-8")

        return ParsedDocument(
            source_id=normalized_source_id,
            file_path=normalized_source_id,
            file_name=file_path.name,
            file_extension="md",
            title=file_path.stem,
            raw_text=raw_text,
            metadata=self._build_metadata(file_path),
            structured_blocks=self._build_structured_blocks(
                raw_text=raw_text,
                source_id=normalized_source_id,
            ),
        )

    def _build_structured_blocks(
        self,
        *,
        raw_text: str,
        source_id: str,
    ) -> list[dict[str, Any]]:
        lines = raw_text.splitlines()
        sections: list[dict[str, Any]] = []
        heading_stack: list[str] = []
        current_lines: list[str] = []
        current_path: list[str] = []
        current_level: int | None = None

        def flush_section() -> None:
            if not current_lines:
                return

            content_lines = current_lines
            if current_level is not None:
                content_lines = current_lines[1:]

            text = "\n".join(content_lines).strip()
            if not text:
                return

            section_name = " > ".join(current_path) if current_path else None
            sections.append(
                {
                    "type": "markdown_section",
                    "heading_level": current_level,
                    "heading_path": list(current_path),
                    "text": text,
                    "source_ref": {
                        "file_path": source_id,
                        "section": section_name,
                    },
                }
            )

        for line in lines:
            match = _HEADING_RE.match(line)
            if match:
                flush_section()
                level = len(match.group(1))
                heading_text = match.group(2).strip()
                heading_stack[:] = heading_stack[: level - 1]
                heading_stack.append(heading_text)
                current_path = list(heading_stack)
                current_level = level
                current_lines = [line]
                continue

            current_lines.append(line)

        flush_section()
        return sections
