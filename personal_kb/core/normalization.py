from __future__ import annotations

import re

from personal_kb.core.errors import NormalizationError

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_label(value: str) -> str:
    """Lowercase, trim, and collapse repeated whitespace."""

    if not isinstance(value, str):
        raise NormalizationError("label value must be a string")
    normalized = _WHITESPACE_RE.sub(" ", value.strip()).lower()
    return normalized


def normalize_entity_name(value: str) -> str:
    """Normalize an entity name using the MVP normalization rule."""

    return normalize_label(value)


def normalize_tag_name(value: str) -> str:
    """Normalize a tag name using the MVP normalization rule."""

    return normalize_label(value)


class NormalizationService:
    """Thin convenience wrapper around label normalization helpers."""

    def normalize_label(self, value: str) -> str:
        return normalize_label(value)

    def normalize_entity_name(self, value: str) -> str:
        return normalize_entity_name(value)

    def normalize_tag_name(self, value: str) -> str:
        return normalize_tag_name(value)

