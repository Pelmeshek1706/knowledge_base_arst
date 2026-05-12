from __future__ import annotations

import re
from pathlib import Path

from personal_kb.parsers.base import BaseParser
from personal_kb.schemas.document import ParsedDocument

_INLINE_WHITESPACE_RE = re.compile(r"[^\S\n]+")


class TxtParser(BaseParser):
    supported_extensions = ("txt",)

    def parse(self, file_path: Path, *, source_id: str | None = None) -> ParsedDocument:
        normalized_source_id = self._normalize_source_id(file_path, source_id)
        raw_text = self._normalize_text(file_path.read_text(encoding="utf-8"))

        return ParsedDocument(
            source_id=normalized_source_id,
            file_path=file_path.as_posix(),
            file_name=file_path.name,
            file_extension="txt",
            title=file_path.stem,
            raw_text=raw_text,
            metadata=self._build_metadata(file_path),
            structured_blocks=[
                {
                    "type": "text_block",
                    "text": raw_text,
                    "source_ref": {
                        "file_path": normalized_source_id,
                        "section": "full_text",
                    },
                }
            ],
        )

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
