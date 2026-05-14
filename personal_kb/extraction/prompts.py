from __future__ import annotations

from collections.abc import Sequence
import json

from personal_kb.schemas.chunk import ChunkRecord
from personal_kb.schemas.document import DocumentRecord

STRICT_JSON_SYSTEM_PROMPT = (
    "You are a precise information extraction system. "
    "Return only valid JSON as one object that matches the provided schema exactly. "
    "Do not include markdown, code fences, comments, explanations, thinking text, "
    "<think> blocks, or extra keys."
)

def build_chunk_extraction_prompt(chunk: ChunkRecord) -> str:
    source_ref_json = json.dumps(chunk.source_ref.model_dump(mode="json"), indent=2)
    return f"""
Task:
Extract retrieval-ready metadata from the chunk below.

Rules:
- Use only facts grounded in the provided chunk text.
- Return exactly these schema fields: `summary` and `tags`.
- Write `summary` as 1 to 3 sentences and keep it concise.
- Return `tags` as short free-form strings useful for retrieval.
- Include important names, organizations, projects, systems, tools, models,
  libraries, technologies, documents, concepts, and domain terms as tags.
- If the chunk names its main subject, project, product, or system, include that
  exact phrase as a tag.
- Prefer exact terms from the text, such as product names, model names, library
  names, database names, and project names.
- Preserve central named project, system, tool, model, and technology phrases
  that appear in the text. Examples to preserve when present: Personal KB,
  LM Studio, Qwen, Neo4j, LangGraph, and structured JSON.
- Do not return objects for tags. Each tag must be a string.
- Do not return typed entities in this response. Entity extraction is separate.
- Do not invent tags. Omit unsupported tags instead of guessing.
- For tag-rich technical text, return useful non-empty tags. Use an empty tag
  list only when the chunk genuinely contains no useful retrieval terms.
- Return only valid JSON that satisfies the schema. Do not include markdown,
  code fences, thinking text, or `<think>` blocks.

Chunk metadata:
- chunk_id: {chunk.chunk_id}
- document_id: {chunk.document_id}
- chunk_index: {chunk.chunk_index}

Source reference:
{source_ref_json}

Chunk text:
\"\"\"
{chunk.text}
\"\"\"
""".strip()


def build_document_aggregation_prompt(
    document: DocumentRecord, chunks: Sequence[ChunkRecord]
) -> str:
    chunk_lines: list[str] = []
    for chunk in chunks:
        tag_names = ", ".join(tag.name for tag in chunk.tags) or "none"
        entity_names = ", ".join(entity.name for entity in chunk.entities) or "none"
        chunk_summary = chunk.summary or "(missing summary)"
        chunk_lines.append(
            f"- chunk_id: {chunk.chunk_id}\n"
            f"  chunk_index: {chunk.chunk_index}\n"
            f"  summary: {chunk_summary}\n"
            f"  tags: {tag_names}\n"
            f"  entities: {entity_names}"
        )

    joined_chunks = "\n".join(chunk_lines) if chunk_lines else "- none"
    return f"""
Task:
Create one document-level summary from chunk-level metadata.

Rules:
- Use only the chunk summaries and metadata provided below.
- Write `summary` as 2 to 4 sentences and keep it concise.
- Emphasize the document's main subjects, actors, and outcomes.
- Do not invent facts that are not supported by the chunk metadata.
- Return only valid JSON that satisfies the schema.

Document metadata:
- document_id: {document.document_id}
- title: {document.title}
- file_name: {document.file_name}
- document_type: {document.document_type}

Chunk metadata:
{joined_chunks}
""".strip()
