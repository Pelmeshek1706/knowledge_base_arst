from __future__ import annotations

from personal_kb.parsers.base import BaseParser
from personal_kb.parsers.markdown_parser import MarkdownParser
from personal_kb.parsers.txt_parser import TxtParser


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers: dict[str, BaseParser] = {}

    def register(self, parser: BaseParser) -> None:
        for extension in parser.supported_extensions:
            self._parsers[self._normalize_extension(extension)] = parser

    def get_parser(self, extension: str) -> BaseParser:
        normalized = self._normalize_extension(extension)
        try:
            return self._parsers[normalized]
        except KeyError as exc:
            raise ValueError(f"unsupported parser extension: {extension}") from exc

    @staticmethod
    def _normalize_extension(extension: str) -> str:
        return extension.lower().lstrip(".")


def build_default_parser_registry() -> ParserRegistry:
    registry = ParserRegistry()
    registry.register(TxtParser())
    registry.register(MarkdownParser())
    return registry
