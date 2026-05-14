from __future__ import annotations

from personal_kb.extraction.aggregation import DocumentMetadataAggregator
from personal_kb.schemas.chunk import ChunkRecord
from personal_kb.schemas.common import SourceRef
from personal_kb.schemas.entity import EntityRecord
from personal_kb.schemas.tag import TagRecord


def _chunk(
    *,
    chunk_index: int,
    summary: str,
    tags: list[TagRecord],
    entities: list[EntityRecord],
) -> ChunkRecord:
    return ChunkRecord(
        document_id="doc-1",
        chunk_index=chunk_index,
        text=f"chunk {chunk_index}",
        summary=summary,
        tags=tags,
        entities=entities,
        source_ref=SourceRef(file_path="data/doc-1.txt", section=f"chunk-{chunk_index}"),
    )


def test_aggregator_merges_tags_entities_and_preserves_source_chunks() -> None:
    aggregator = DocumentMetadataAggregator()
    first_chunk = _chunk(
        chunk_index=0,
        summary="Budget review assigns Alice ownership of the roadmap.",
        tags=[
            TagRecord(
                name=" Budget Review ",
                normalized_name="budget review",
                confidence=0.6,
            )
        ],
        entities=[
            EntityRecord(
                name=" Alice ",
                normalized_name="alice",
                type="Person",
                confidence=0.8,
            )
        ],
    )
    second_chunk = _chunk(
        chunk_index=1,
        summary="Follow-up tasks cover the roadmap and budget review.",
        tags=[
            TagRecord(
                name="budget review",
                normalized_name=" budget  review ",
                confidence=0.9,
            ),
            TagRecord(
                name="Roadmap",
                normalized_name="roadmap",
                confidence=0.7,
            ),
        ],
        entities=[
            EntityRecord(
                name="Alice",
                normalized_name="alice",
                type="Person",
                confidence=0.95,
            ),
            EntityRecord(
                name="Roadmap",
                normalized_name="roadmap",
                type="Project",
                confidence=0.72,
            ),
        ],
    )
    chunks = [first_chunk, second_chunk]

    aggregated_tags = aggregator.aggregate_tags(chunks)
    aggregated_entities = aggregator.aggregate_entities(chunks)

    assert [(tag.name, tag.normalized_name) for tag in aggregated_tags] == [
        ("budget review", "budget review"),
        ("Roadmap", "roadmap"),
    ]
    assert aggregated_tags[0].confidence == 0.9
    assert aggregated_tags[0].source_chunks == [first_chunk.chunk_id, second_chunk.chunk_id]

    assert [(entity.name, entity.type) for entity in aggregated_entities] == [
        ("Alice", "Person"),
        ("Roadmap", "Project"),
    ]
    assert aggregated_entities[0].source_chunks == [
        first_chunk.chunk_id,
        second_chunk.chunk_id,
    ]
    assert "additional chunk" in aggregated_entities[0].summary


def test_aggregator_keeps_entity_types_separate_when_names_match() -> None:
    aggregator = DocumentMetadataAggregator()
    chunks = [
        _chunk(
            chunk_index=0,
            summary="Apollo is the project name.",
            tags=[],
            entities=[
                EntityRecord(
                    name="Apollo",
                    normalized_name="apollo",
                    type="Project",
                )
            ],
        ),
        _chunk(
            chunk_index=1,
            summary="Apollo is also a technology stack label here.",
            tags=[],
            entities=[
                EntityRecord(
                    name="Apollo",
                    normalized_name="apollo",
                    type="Technology",
                )
            ],
        ),
    ]

    aggregated_entities = aggregator.aggregate_entities(chunks)

    assert [(entity.normalized_name, entity.type) for entity in aggregated_entities] == [
        ("apollo", "Project"),
        ("apollo", "Technology"),
    ]
