from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List
from zipfile import BadZipFile, ZipFile

from graphrag.graph.graph_rag import GraphRag
from graphrag.llm.lm_studio import ChunkSplitConfig, LMStudioClient
from graphrag.storage.neo4j_client import Neo4jClient
from graphrag.types.models import ChunkAnnotation, Entity

logger = logging.getLogger(__name__)

_DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
PROCESSED_DOCS_DIR = Path(os.environ.get("PROCESSED_DOCS_DIR", "processed_docs"))
CACHE_FILE = PROCESSED_DOCS_DIR / "llm_annotations.json"


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def read_docx_text(path: Path) -> str:
    try:
        with ZipFile(path) as zf:
            xml_bytes = zf.read("word/document.xml")
    except (KeyError, BadZipFile) as exc:
        raise RuntimeError(f"Invalid DOCX: {path}") from exc

    root = ET.fromstring(xml_bytes)
    paragraphs: List[str] = []
    for p in root.findall(".//w:p", _DOCX_NS):
        buf: List[str] = []
        for node in p.iter():
            tag = node.tag
            if tag.endswith("}t") and node.text:
                buf.append(node.text)
            elif tag.endswith("}tab"):
                buf.append("\t")
            elif tag.endswith("}br") or tag.endswith("}cr"):
                buf.append("\n")
        line = "".join(buf).strip()
        if line:
            paragraphs.append(line)
    return "\n".join(paragraphs)


def read_rtf_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"{\\\*?\\[^{}]+}", " ", raw)
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", text)
    text = re.sub(r"[{}]", " ", text)
    return " ".join(text.split())


def read_document_text(path: Path) -> str:
    if not path.exists():
        logger.warning("File not found: %s", path)
        return ""

    suffix = path.suffix.lower()
    try:
        if suffix == ".docx":
            return read_docx_text(path)
        if suffix == ".rtf":
            return read_rtf_text(path)
        if suffix in {".txt", ".md"}:
            return read_text_file(path)
    except Exception as exc:
        logger.warning("Failed to read %s: %s", path, exc)
        return ""

    logger.warning("Unsupported file type %s for %s", suffix, path)
    return ""


def hash_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()


def load_annotation_cache(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"version": 1, "docs": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("cache is not an object")
        if "docs" not in data or not isinstance(data.get("docs"), dict):
            data["docs"] = {}
        data.setdefault("version", 1)
        return data
    except Exception as exc:
        logger.warning("Failed to load cache %s: %s", path, exc)
        return {"version": 1, "docs": {}}


def save_annotation_cache(path: Path, cache: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(cache, indent=2, ensure_ascii=True), encoding="utf-8")
    tmp_path.replace(path)


def chunk_cfg_signature(cfg: ChunkSplitConfig) -> Dict[str, Any]:
    return {
        "mode": cfg.mode,
        "chunk_size": cfg.chunk_size,
        "chunk_overlap": cfg.chunk_overlap,
        "separators": cfg.separators or [],
        "encoding_name": cfg.encoding_name,
    }


def cache_key(file_path: str | None, doc_id: str) -> str:
    return file_path or doc_id


def annotation_to_dict(ann: ChunkAnnotation) -> Dict[str, Any]:
    return {
        "chunk_type": ann.chunk_type,
        "summary": ann.summary,
        "entities": [{"name": e.name, "type": e.type} for e in ann.entities],
        "relationships": ann.relationships,
        "tags": ann.tags,
        "candidate_qas": ann.candidate_qas,
    }


def annotation_from_dict(data: Dict[str, Any]) -> ChunkAnnotation:
    entities: List[Entity] = []
    for e in data.get("entities", []) or []:
        if isinstance(e, dict):
            name = str(e.get("name", "")).strip()
            etype = str(e.get("type", "OTHER")).strip().upper()
            if name:
                entities.append(Entity(name=name, type=etype))
    relationships = [r for r in (data.get("relationships", []) or []) if isinstance(r, dict)]
    tags = [t for t in (data.get("tags", []) or []) if isinstance(t, str)]
    cqa = [q for q in (data.get("candidate_qas", []) or []) if isinstance(q, dict)]
    return ChunkAnnotation(
        chunk_type=str(data.get("chunk_type", "other")).strip(),
        summary=str(data.get("summary", "")).strip() if data.get("summary") is not None else None,
        entities=entities,
        relationships=relationships,
        tags=tags,
        candidate_qas=cqa,
    )


def ingest_data_json(client: Neo4jClient, graph: GraphRag, llm: LMStudioClient, path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        docs = json.load(f)

    logger.info("Loading documents from %s", path)
    logger.info("Found %s documents", len(docs))

    graph.setup_graph_schema()
    logger.info("Neo4j schema ready")
    vector_index_name = os.environ.get("NEO4J_VECTOR_INDEX", "chunk_embedding_index")
    vector_similarity = os.environ.get("NEO4J_VECTOR_SIMILARITY", "cosine")
    logger.info(
        "Vector retrieval config: index=%s similarity=%s embedding_model=%s backend=%s",
        vector_index_name,
        vector_similarity,
        llm.embedding_model_id,
        llm.active_embedding_backend,
    )

    vector_index_ready = False
    existing_dim = graph.get_chunk_embedding_dimension()
    if existing_dim:
        try:
            graph.setup_chunk_vector_index(
                dimensions=existing_dim,
                index_name=vector_index_name,
                similarity_function=vector_similarity,
            )
            vector_index_ready = True
            logger.info("Vector index is ready (existing dim=%s)", existing_dim)
        except Exception as exc:
            logger.warning("Failed to ensure vector index from existing embedding dim: %s", exc)

    base_dir = Path(path).resolve().parent
    chunk_cfg = ChunkSplitConfig(
        mode=os.environ.get("CHUNK_MODE", "context"),
        chunk_size=int(os.environ.get("CHUNK_SIZE", "1200")),
        chunk_overlap=int(os.environ.get("CHUNK_OVERLAP", "200")),
    )
    chunk_cfg_sig = chunk_cfg_signature(chunk_cfg)
    cache = load_annotation_cache(CACHE_FILE)
    cache_docs: Dict[str, Any] = cache.get("docs", {})
    cache_dirty = False

    for i, d in enumerate(docs):
        doc_id = f"doc_{i:03d}"
        title = d.get("title", "") or ""
        desc = d.get("description", "") or ""
        source_type = "json"
        source_id = d.get("file_path", f"row_{i}")
        file_path = d.get("file_path")
        resolved_path = None
        if file_path:
            p = Path(file_path)
            resolved_path = p if p.is_absolute() else (base_dir / p)

        logger.info("Processing %s: %s", doc_id, title or "<untitled>")

        graph.upsert_document(
            doc_id=doc_id,
            title=title,
            source_type=source_type,
            source_id=str(source_id),
            file_path=file_path,
            description=desc,
            source_keywords=d.get("keywords", []) or [],
        )

        doc_text = read_document_text(resolved_path) if resolved_path else ""
        if not doc_text:
            logger.warning("No text extracted for %s; using description as fallback.", doc_id)
            doc_text = desc

        content_hash = hash_text(doc_text)
        c_key = cache_key(str(resolved_path) if resolved_path else file_path, doc_id)
        entry = cache_docs.get(c_key)
        use_cache = (
            isinstance(entry, dict)
            and entry.get("content_hash") == content_hash
            and entry.get("chunk_cfg") == chunk_cfg_sig
        )
        cached_chunks: Dict[int, Dict[str, Any]] = {}
        if use_cache:
            for c in entry.get("chunks", []) or []:
                idx = c.get("chunk_index")
                if isinstance(idx, int):
                    cached_chunks[idx] = c

        chunks = llm.split_document(doc_id, doc_text, chunk_cfg, heading_path="content")
        if not chunks:
            logger.warning("No chunks produced for %s; skipping.", doc_id)
            continue

        chunk_ids = [c.chunk_id for c in chunks]
        chunk_props = {
            c.chunk_id: {
                "text": c.text,
                "heading_path": c.heading_path or "content",
            }
            for c in chunks
        }
        graph.upsert_chunk_nodes(
            doc_id=doc_id,
            chunk_ids=chunk_ids,
            chunk_props=chunk_props,
        )

        # reuse previously embedded rows for the same embedding model
        embedded_rows = client.run(
            """
            MATCH (c:Chunk)
            WHERE c.chunk_id IN $chunk_ids
              AND c.embedding IS NOT NULL
              AND c.embedding_model = $embedding_model
            RETURN c.chunk_id AS chunk_id
            """,
            {"chunk_ids": chunk_ids, "embedding_model": llm.embedding_model_id},
        )
        embedded_chunk_ids = {r.get("chunk_id") for r in embedded_rows if r.get("chunk_id")}
        chunks_to_embed = [c for c in chunks if c.chunk_id not in embedded_chunk_ids]
        embedded_now = 0
        if chunks_to_embed:
            try:
                vectors = llm.embed_texts([c.text for c in chunks_to_embed])
                if vectors:
                    if not vector_index_ready:
                        graph.setup_chunk_vector_index(
                            dimensions=len(vectors[0]),
                            index_name=vector_index_name,
                            similarity_function=vector_similarity,
                        )
                        vector_index_ready = True
                    graph.upsert_chunk_embeddings(
                        {
                            chunk.chunk_id: vec
                            for chunk, vec in zip(chunks_to_embed, vectors)
                        },
                        embedding_model=llm.embedding_model_id,
                    )
                    embedded_now = len(vectors)
            except Exception as exc:
                logger.warning(
                    "Embedding failed for %s (%s chunks): %s",
                    doc_id,
                    len(chunks_to_embed),
                    exc,
                )

        total_entities = 0
        total_relationships = 0
        total_tags = 0
        updated_chunks: List[Dict[str, Any]] = []
        for chunk in chunks:
            cached = cached_chunks.get(chunk.chunk_index)
            cached_ann = cached.get("annotation") if isinstance(cached, dict) else None
            if cached and cached.get("text_hash") == hash_text(chunk.text) and isinstance(cached_ann, dict):
                ann = annotation_from_dict(cached_ann)
            else:
                ann = llm.annotate_chunk(chunk)
                cache_dirty = True
            graph.upsert_entities(chunk.chunk_id, ann.entities)
            graph.upsert_entity_relationships(ann.relationships)
            graph.upsert_tags(chunk.chunk_id, ann.tags)
            total_entities += len(ann.entities)
            total_relationships += len(ann.relationships)
            total_tags += len(ann.tags)
            updated_chunks.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": chunk.chunk_index,
                    "text_hash": hash_text(chunk.text),
                    "annotation": annotation_to_dict(ann),
                }
            )
        cache_docs[c_key] = {
            "doc_id": doc_id,
            "file_path": file_path,
            "content_hash": content_hash,
            "chunk_cfg": chunk_cfg_sig,
            "chunks": updated_chunks,
            "updated_at": int(time.time()),
        }
        logger.info(
            "  OK chunks=%s embedded(new=%s cached=%s model=%s backend=%s) entities=%s rels=%s tags=%s",
            len(chunks),
            embedded_now,
            len(embedded_chunk_ids),
            llm.embedding_model_id,
            llm.active_embedding_backend,
            total_entities,
            total_relationships,
            total_tags,
        )

    if cache_dirty:
        cache["docs"] = cache_docs
        save_annotation_cache(CACHE_FILE, cache)
        logger.info("Saved LLM cache: %s", CACHE_FILE)
