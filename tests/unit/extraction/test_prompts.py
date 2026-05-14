from __future__ import annotations

from personal_kb.extraction.prompts import (
    STRICT_JSON_SYSTEM_PROMPT,
    build_chunk_extraction_prompt,
    build_document_aggregation_prompt,
)
from personal_kb.schemas.chunk import ChunkRecord
from personal_kb.schemas.common import SourceRef
from personal_kb.schemas.document import DocumentRecord


def test_chunk_extraction_prompt_is_explicit_and_json_only() -> None:
    chunk = ChunkRecord(
        document_id="doc-1",
        chunk_index=0,
        text="Alice reviews the roadmap budget in Prague.",
        source_ref=SourceRef(file_path="data/doc-1.txt", section="full_text"),
    )

    prompt = build_chunk_extraction_prompt(chunk)

    assert "Return only valid JSON" in STRICT_JSON_SYSTEM_PROMPT
    assert "code fences" in STRICT_JSON_SYSTEM_PROMPT
    assert "<think> blocks" in STRICT_JSON_SYSTEM_PROMPT
    assert "Use only facts grounded in the provided chunk text." in prompt
    assert "Return exactly these schema fields: `summary`, `tags`, and `entities`." in prompt
    assert "names, organizations, projects, systems, tools, models" in prompt
    assert "libraries, technologies, documents, concepts, and domain terms" in prompt
    assert "Return `entities` as typed objects with `name`, `type`, and optional" in prompt
    assert "Person, Organization, Project, Topic" in prompt
    assert "main subject, project, product, or system" in prompt
    assert "Examples to preserve when present: Personal KB" in prompt
    assert "LM Studio, Qwen, Neo4j, LangGraph, and structured JSON" in prompt
    assert "Each tag must be a string" in prompt
    assert "Use an empty entity list only when the chunk genuinely contains no clear" in prompt
    assert "For tag-rich technical text, return useful non-empty tags." in prompt
    assert "Alice reviews the roadmap budget in Prague." in prompt
    assert '"section": "full_text"' in prompt


def test_document_aggregation_prompt_uses_chunk_metadata_only() -> None:
    document = DocumentRecord(
        document_id="doc-1",
        source_id="data/doc-1.txt",
        file_path="data/doc-1.txt",
        file_name="doc-1.txt",
        file_extension="txt",
        document_type="text",
        title="Roadmap Notes",
        ingested_at="2026-05-09T12:00:00Z",
        raw_bytes_hash="raw",
        extracted_text_hash="text",
        content_hash="content",
    )
    chunks = [
        ChunkRecord(
            document_id="doc-1",
            chunk_index=0,
            text="ignored raw text",
            summary="Alice reviews the roadmap budget.",
            source_ref=SourceRef(file_path="data/doc-1.txt", section="chars:0-20"),
        )
    ]

    prompt = build_document_aggregation_prompt(document, chunks)

    assert "Use only the chunk summaries and metadata provided below." in prompt
    assert "Alice reviews the roadmap budget." in prompt
    assert "ignored raw text" not in prompt
    assert "Return only valid JSON" in prompt
