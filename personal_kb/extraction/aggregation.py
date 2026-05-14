from __future__ import annotations

from collections.abc import Iterable
import re

from personal_kb.core.normalization import normalize_entity_name, normalize_tag_name
from personal_kb.schemas.chunk import ChunkRecord
from personal_kb.schemas.entity import EntityRecord
from personal_kb.schemas.tag import TagRecord

_WHITESPACE_RE = re.compile(r"\s+")


def _clean_display_text(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", value.strip())


def _merge_confidence(current: float | None, candidate: float | None) -> float | None:
    if current is None:
        return candidate
    if candidate is None:
        return current
    return max(current, candidate)


def _unique_preserving_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


class DocumentMetadataAggregator:
    """Merge chunk metadata into document-level tags and entities."""

    def aggregate_tags(self, chunks: list[ChunkRecord]) -> list[TagRecord]:
        merged: dict[str, TagRecord] = {}

        for chunk in chunks:
            for tag in chunk.tags:
                normalized_name = normalize_tag_name(tag.normalized_name or tag.name)
                source_chunks = (
                    _unique_preserving_order(tag.source_chunks)
                    if tag.source_chunks
                    else [chunk.chunk_id]
                )
                candidate = TagRecord(
                    tag_id=tag.tag_id,
                    name=_clean_display_text(tag.name),
                    normalized_name=normalized_name,
                    confidence=tag.confidence,
                    source=tag.source,
                    source_chunks=source_chunks,
                )
                existing = merged.get(normalized_name)
                if existing is None:
                    merged[normalized_name] = candidate
                    continue

                merged[normalized_name] = TagRecord(
                    tag_id=existing.tag_id,
                    name=self._choose_display_name(
                        existing.name,
                        candidate.name,
                        existing.confidence,
                        candidate.confidence,
                    ),
                    normalized_name=normalized_name,
                    confidence=_merge_confidence(
                        existing.confidence, candidate.confidence
                    ),
                    source=existing.source,
                    source_chunks=_unique_preserving_order(
                        [*existing.source_chunks, *candidate.source_chunks]
                    ),
                )

        return list(merged.values())

    def aggregate_entities(self, chunks: list[ChunkRecord]) -> list[EntityRecord]:
        merged: dict[str, EntityRecord] = {}

        for chunk in chunks:
            for entity in chunk.entities:
                normalized_name = normalize_entity_name(
                    entity.normalized_name or entity.name
                )
                source_chunks = (
                    _unique_preserving_order(entity.source_chunks)
                    if entity.source_chunks
                    else [chunk.chunk_id]
                )
                candidate = EntityRecord(
                    entity_id=entity.entity_id,
                    entity_key=entity.entity_key,
                    name=_clean_display_text(entity.name),
                    normalized_name=normalized_name,
                    type=entity.type,
                    confidence=entity.confidence,
                    source=entity.source,
                    summary=entity.summary,
                    source_chunks=source_chunks,
                )
                entity_key = candidate.entity_key
                existing = merged.get(entity_key)
                if existing is None:
                    merged[entity_key] = candidate
                    continue

                merged[entity_key] = EntityRecord(
                    entity_id=existing.entity_id,
                    entity_key=existing.entity_key,
                    name=self._choose_display_name(
                        existing.name,
                        candidate.name,
                        existing.confidence,
                        candidate.confidence,
                    ),
                    normalized_name=normalized_name,
                    type=existing.type,
                    confidence=_merge_confidence(
                        existing.confidence, candidate.confidence
                    ),
                    source=existing.source,
                    summary=self._merge_entity_summary(
                        existing,
                        candidate,
                        chunks=chunks,
                    ),
                    source_chunks=_unique_preserving_order(
                        [*existing.source_chunks, *candidate.source_chunks]
                    ),
                )

        return list(merged.values())

    def _merge_entity_summary(
        self,
        existing: EntityRecord,
        candidate: EntityRecord,
        *,
        chunks: list[ChunkRecord],
    ) -> str | None:
        for summary in (existing.summary, candidate.summary):
            if summary:
                return summary

        source_chunk_ids = _unique_preserving_order(
            [*existing.source_chunks, *candidate.source_chunks]
        )
        chunk_summaries = [
            _clean_display_text(chunk.summary)
            for chunk in chunks
            if chunk.chunk_id in source_chunk_ids and chunk.summary
        ]
        chunk_summaries = _unique_preserving_order(chunk_summaries)
        if not chunk_summaries:
            return None
        if len(chunk_summaries) == 1:
            return chunk_summaries[0]
        return (
            f"{chunk_summaries[0]} "
            f"Also referenced in {len(chunk_summaries) - 1} additional chunk(s)."
        )

    def _choose_display_name(
        self,
        current_name: str,
        candidate_name: str,
        current_confidence: float | None,
        candidate_confidence: float | None,
    ) -> str:
        if candidate_confidence is not None and (
            current_confidence is None or candidate_confidence > current_confidence
        ):
            return candidate_name
        if current_confidence == candidate_confidence and len(candidate_name) > len(
            current_name
        ):
            return candidate_name
        return current_name
