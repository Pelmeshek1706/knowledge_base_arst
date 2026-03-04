from __future__ import annotations

import hashlib
import math
import os
import re
import requests
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Literal

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter, TokenTextSplitter
except Exception:  # pragma: no cover - optional dependency
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter, TokenTextSplitter
    except Exception:  # pragma: no cover - optional dependency
        RecursiveCharacterTextSplitter = None  # type: ignore[assignment]
        TokenTextSplitter = None  # type: ignore[assignment]

try:
    from langsmith import traceable, tracing_context
except Exception:  # pragma: no cover - optional dependency
    def traceable(*decorator_args: Any, **decorator_kwargs: Any):  # type: ignore[no-redef]
        # No-op fallback when langsmith is not available.
        if (
            decorator_args
            and callable(decorator_args[0])
            and len(decorator_args) == 1
            and not decorator_kwargs
        ):
            return decorator_args[0]

        def _decorator(func: Any) -> Any:
            return func

        return _decorator

    @contextmanager
    def tracing_context(*args: Any, **kwargs: Any) -> Iterator[None]:  # type: ignore[no-redef]
        yield

from graphrag.llm.base import (
    ChatMessage,
    LLMClient,
    expect_json_array,
    expect_json_object,
)
from graphrag.types.models import Chunk, ChunkAnnotation, Entity, FAQEntry, AnswerWithCitations, Citation
from graphrag.graph.graph_rag import GraphRag
from graphrag.storage.neo4j_client import Neo4jClient


SplitMode = Literal["context", "token"]

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def _parse_env_bool(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def _resolve_tracing_enabled(explicit_enabled: Optional[bool]) -> bool:
    if explicit_enabled is not None:
        return explicit_enabled
    for key in (
        "LANGSMITH_TRACING_V2",
        "LANGSMITH_TRACING",
        "LANGCHAIN_TRACING_V2",
        "LANGCHAIN_TRACING",
    ):
        parsed = _parse_env_bool(os.environ.get(key))
        if parsed is not None:
            return parsed
    return False


def _split_csv_env(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item and item.strip()]


def _trace_process_inputs(inputs: Any) -> Any:
    if isinstance(inputs, dict):
        return {k: v for k, v in inputs.items() if k != "self"}
    return inputs


def _trace_process_answer_output(output: Any) -> Any:
    if isinstance(output, AnswerWithCitations):
        return {
            "answer_preview": output.answer[:300],
            "citation_count": len(output.citations),
            "debug_keys": sorted(output.debug.keys()),
        }
    return output


_QUERY_ENTITY_STOPWORDS = {
    "what",
    "which",
    "where",
    "when",
    "who",
    "why",
    "how",
    "about",
    "know",
    "tell",
    "more",
    "there",
    "they",
    "them",
    "this",
    "that",
    "with",
    "from",
    "into",
    "по",
    "про",
    "что",
    "там",
    "знаем",
    "какая",
    "какой",
    "какие",
    "где",
    "когда",
    "сейчас",
    "сегодня",
    "мне",
    "тебе",
    "для",
    "или",
    "как",
}


@dataclass(frozen=True)
class ChunkSplitConfig:
    """
    Chunk splitting configuration for LangChain splitters.

    mode:
        "context" uses RecursiveCharacterTextSplitter (separator-aware).
        "token" uses TokenTextSplitter (token count based).
    """

    mode: SplitMode = "context"
    chunk_size: int = 1200
    chunk_overlap: int = 200
    separators: Optional[List[str]] = None
    encoding_name: str = "cl100k_base"


def _simple_char_split(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    if chunk_size <= 0:
        return [text]
    overlap = max(0, min(chunk_overlap, chunk_size - 1))
    chunks: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        chunks.append(text[start:end])
        if end >= n:
            break
        start = max(0, end - overlap)
    return chunks


@dataclass(frozen=True)
class LMStudioConfig:
    """
    LM Studio REST server configuration.

    LM Studio provides OpenAI-compatible endpoints; commonly you point a client at
    http://localhost:1234/v1 and call /chat/completions. :contentReference[oaicite:0]{index=0}
    """
    base_url: str = "http://localhost:1234"
    model: str = "local-model"
    embedding_model: Optional[str] = None
    embedding_fallback: bool = True
    local_embedding_dimensions: int = 384
    api_key: Optional[str] = None  # LM Studio typically ignores it, but some clients require it.


class LMStudioClient(LLMClient):
    """
    OpenAI-compatible chat client for LM Studio.

    Default endpoint:
      POST {base_url}/v1/chat/completions
    (LM Studio docs show OpenAI-compatible usage and default port 1234). :contentReference[oaicite:1]{index=1}
    """

    def __init__(self, cfg: LMStudioConfig):
        self.cfg = cfg
        self._chat_url = self._normalize_chat_url(cfg.base_url)
        self._embeddings_url = self._normalize_embeddings_url(cfg.base_url)
        self.embedding_model = (cfg.embedding_model or cfg.model).strip()
        self.local_embedding_dimensions = max(16, int(cfg.local_embedding_dimensions))
        self.active_embedding_backend = "lmstudio"

    def split_text(self, text: str, cfg: Optional[ChunkSplitConfig] = None) -> List[str]:
        """
        Split raw text into chunks using LangChain splitters.

        If LangChain is unavailable, falls back to a simple character window.
        """
        cfg = cfg or ChunkSplitConfig()
        cleaned = (text or "").strip()
        if not cleaned:
            return []

        if cfg.chunk_size <= 0:
            return [cleaned]
        overlap = max(0, min(cfg.chunk_overlap, cfg.chunk_size - 1))

        mode = (cfg.mode or "context").strip().lower()
        if mode == "token":
            if TokenTextSplitter is None:
                raise RuntimeError(
                    "TokenTextSplitter not available. Install langchain-text-splitters and tiktoken."
                )
            splitter = TokenTextSplitter(
                chunk_size=cfg.chunk_size,
                chunk_overlap=overlap,
                encoding_name=cfg.encoding_name,
            )
            chunks = splitter.split_text(cleaned)
        else:
            if RecursiveCharacterTextSplitter is None:
                return _simple_char_split(cleaned, cfg.chunk_size, overlap)
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=cfg.chunk_size,
                chunk_overlap=overlap,
                separators=cfg.separators or DEFAULT_SEPARATORS,
            )
            chunks = splitter.split_text(cleaned)

        return [c.strip() for c in chunks if c and c.strip()]

    def split_document(
        self,
        doc_id: str,
        text: str,
        cfg: Optional[ChunkSplitConfig] = None,
        *,
        heading_path: Optional[str] = None,
    ) -> List[Chunk]:
        """
        Split a document into Chunk objects with stable IDs.
        """
        parts = self.split_text(text, cfg)
        chunks: List[Chunk] = []
        for idx, part in enumerate(parts):
            chunk_id = f"{doc_id}_c{idx:03d}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    chunk_index=idx,
                    text=part,
                    heading_path=heading_path,
                )
            )
        return chunks

    @staticmethod
    def _normalize_chat_url(base_url: str) -> str:
        base = base_url.rstrip("/")
        # allow either "...:1234" or "...:1234/v1"
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        return f"{base}/v1/chat/completions"

    @staticmethod
    def _normalize_embeddings_url(base_url: str) -> str:
        base = base_url.rstrip("/")
        if base.endswith("/v1"):
            return f"{base}/embeddings"
        return f"{base}/v1/embeddings"

    def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 1500,
        timeout_s: int = 60,
    ) -> str:
        return self._chat_with_format(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_s=timeout_s,
            response_format=None,
        )

    def _chat_with_format(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float,
        max_tokens: int,
        timeout_s: int,
        response_format: Optional[Dict[str, Any]],
    ) -> str:
        return self._chat_with_format_traced(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_s=timeout_s,
            response_format=response_format,
        )

    @traceable(
        run_type="llm",
        name="lmstudio.chat_completion",
        process_inputs=_trace_process_inputs,
    )
    def _chat_with_format_traced(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float,
        max_tokens: int,
        timeout_s: int,
        response_format: Optional[Dict[str, Any]],
    ) -> str:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.cfg.api_key:
            headers["Authorization"] = f"Bearer {self.cfg.api_key}"

        payload: Dict[str, Any] = {
            "model": self.cfg.model,
            "messages": list(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.95,
        }
        if response_format:
            payload["response_format"] = response_format

        resp = requests.post(self._chat_url, json=payload, headers=headers, timeout=timeout_s)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _local_hash_embedding(self, text: str) -> List[float]:
        """
        Deterministic local embedding fallback when /v1/embeddings is unavailable.
        """
        dims = self.local_embedding_dimensions
        vec = [0.0] * dims
        tokens = re.findall(r"[\w-]+", (text or "").lower())
        if not tokens:
            return vec

        for token in tokens:
            h = int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16)
            idx = h % dims
            sign = 1.0 if ((h >> 1) & 1) else -1.0
            weight = 1.0 + ((h % 997) / 9970.0)
            vec[idx] += sign * weight

        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def _local_hash_embeddings(self, texts: Sequence[str]) -> List[List[float]]:
        self.active_embedding_backend = "local_hash"
        return [self._local_hash_embedding(text) for text in texts]

    @traceable(
        run_type="llm",
        name="lmstudio.embeddings",
        process_inputs=_trace_process_inputs,
    )
    def embed_texts(
        self,
        texts: Sequence[str],
        *,
        batch_size: int = 16,
        timeout_s: int = 90,
    ) -> List[List[float]]:
        cleaned: List[str] = [" ".join((t or "").split()) for t in texts]
        if not cleaned:
            return []

        step = max(1, int(batch_size))
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.cfg.api_key:
            headers["Authorization"] = f"Bearer {self.cfg.api_key}"

        try:
            vectors: List[List[float]] = []
            for start in range(0, len(cleaned), step):
                batch = cleaned[start : start + step]
                payload: Dict[str, Any] = {
                    "model": self.embedding_model,
                    "input": batch,
                }
                resp = requests.post(self._embeddings_url, json=payload, headers=headers, timeout=timeout_s)
                resp.raise_for_status()
                data = resp.json()
                rows = data.get("data") or []
                if not isinstance(rows, list):
                    raise RuntimeError("LM Studio embeddings response has invalid 'data' field.")

                rows_sorted = sorted(rows, key=lambda x: int(x.get("index", 0)))
                for row in rows_sorted:
                    embedding = row.get("embedding")
                    if not isinstance(embedding, list) or not embedding:
                        raise RuntimeError("LM Studio embeddings response has empty/invalid embedding.")
                    vectors.append([float(x) for x in embedding])

            if len(vectors) != len(cleaned):
                raise RuntimeError(
                    f"LM Studio embeddings count mismatch: expected {len(cleaned)}, got {len(vectors)}."
                )
            self.active_embedding_backend = "lmstudio"
            return vectors
        except Exception:
            if not self.cfg.embedding_fallback:
                raise
            return self._local_hash_embeddings(cleaned)

    def embed_query(self, text: str, *, timeout_s: int = 90) -> List[float]:
        vectors = self.embed_texts([text], timeout_s=timeout_s)
        return vectors[0] if vectors else []

    @property
    def embedding_model_id(self) -> str:
        if self.active_embedding_backend == "lmstudio":
            return self.embedding_model
        return f"local_hash_{self.local_embedding_dimensions}"

    def extract_query_entities(self, question: str, max_entities: int = 3) -> List[str]:
        prompt = (
            "Extract up to {n} key entities/topics from this question.\n"
            "Return ONLY a JSON array of strings, no extra text.\n\n"
            "Question:\n{q}\n"
        ).format(n=max_entities, q=question)
        out: List[str] = []
        try:
            raw = self.chat([{"role": "user", "content": prompt}], temperature=0.1, max_tokens=200)
            arr = expect_json_array(raw)
            for x in arr:
                if isinstance(x, str) and x.strip():
                    out.append(x.strip())
            if out:
                return out[:max_entities]
        except Exception:
            pass

        # Fallback for models that occasionally return plain text instead of JSON.
        tokens = re.findall(r"[\w-]+", (question or ""), flags=re.UNICODE)
        seen: set[str] = set()
        for token in tokens:
            term = token.strip()
            if len(term) < 3:
                continue
            term_l = term.lower()
            if term_l in _QUERY_ENTITY_STOPWORDS:
                continue
            if term_l in seen:
                continue
            seen.add(term_l)
            out.append(term)
            if len(out) >= max_entities:
                break

        if out:
            return out[:max_entities]
        return [question.strip()[:80]] if question.strip() else []

    def extract_keywords(
        self,
        text: str,
        *,
        min_keywords: int = 6,
        max_keywords: int = 12,
    ) -> List[str]:
        """
        Extract keywords/keyphrases from text using a dedicated prompt.
        """
        cleaned = (text or "").strip()
        if not cleaned:
            return []

        min_n = max(1, int(min_keywords))
        max_n = max(1, int(max_keywords))
        if min_n > max_n:
            max_n = min_n

        schema = {
            "name": "keyword_extraction",
            "schema": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": min_n,
                        "maxItems": max_n,
                    }
                },
                "required": ["keywords"],
                "additionalProperties": False,
            },
            "strict": True,
        }

        system = (
            "Extract concise keywords/keyphrases from the text. "
            "Use 1-4 words per keyword and prefer specific entities and domain terms."
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Text:\n{cleaned}\n"},
        ]

        out: List[str] = []
        try:
            raw = self._chat_with_format(
                messages,
                temperature=0.1,
                max_tokens=350,
                timeout_s=60,
                response_format={"type": "json_schema", "json_schema": schema},
            )
            try:
                obj = expect_json_object(raw)
                arr = obj.get("keywords", [])
            except Exception:
                arr = expect_json_array(raw)
        except Exception:
            try:
                prompt_fallback = (
                    f"Return ONLY a JSON object like {{\"keywords\": [\"...\", \"...\"]}}.\n"
                    f"Provide {min_n}-{max_n} keywords.\n"
                    f"Text:\n{cleaned}\n"
                )
                raw = self.chat(
                    [{"role": "user", "content": prompt_fallback}],
                    temperature=0.1,
                    max_tokens=350,
                )
                try:
                    obj = expect_json_object(raw)
                    arr = obj.get("keywords", [])
                except Exception:
                    arr = expect_json_array(raw)
            except Exception:
                arr = []

        seen: set[str] = set()
        for x in arr or []:
            if not isinstance(x, str):
                continue
            kw = " ".join(x.strip().split())
            if not kw:
                continue
            key = kw.lower()
            if key in seen:
                continue
            out.append(kw)
            seen.add(key)

        if len(out) > max_n:
            return out[:max_n]
        return out

    def annotate_chunk(self, chunk: Chunk) -> ChunkAnnotation:
        schema = {
            "name": "chunk_annotation",
            "schema": {
                "type": "object",
                "properties": {
                    "chunk_type": {"type": "string"},
                    "summary": {"type": "string"},
                    "entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                            },
                            "required": ["name", "type"],
                            "additionalProperties": False,
                        },
                        "maxItems": 12,
                    },
                    "relationships": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                                "target": {"type": "string"},
                                "type": {"type": "string"},
                            },
                            "required": ["source", "target", "type"],
                            "additionalProperties": False,
                        },
                        "maxItems": 10,
                    },
                    "candidate_qas": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question": {"type": "string"},
                                "answer": {"type": "string"},
                            },
                            "required": ["question", "answer"],
                            "additionalProperties": False,
                        },
                        "maxItems": 3,
                    },
                },
                "required": ["chunk_type", "summary", "entities", "relationships", "candidate_qas"],
                "additionalProperties": False,
            },
            "strict": True,
        }

        system = (
            "Analyze the chunk and return JSON that matches the schema. "
            "Focus on accurate entities and relationships."
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Chunk:\n{chunk.text}\n"},
        ]

        try:
            raw = self._chat_with_format(
                messages,
                temperature=0.2,
                max_tokens=1200,
                timeout_s=60,
                response_format={"type": "json_schema", "json_schema": schema},
            )
            obj = expect_json_object(raw)
        except Exception:
            prompt = f"""
Analyze the following chunk and return STRICT JSON only (no markdown, no commentary).

Chunk:
{chunk.text}

Return JSON with this shape:
{{
  "chunk_type": "definition|procedure|requirement|background|risk|architecture|other",
  "summary": "1-2 sentence summary",
  "entities": [{{"name": "...", "type": "CONCEPT|TECHNOLOGY|ORGANIZATION|CONDITION|POPULATION|OTHER"}}],
  "relationships": [{{"source": "...", "target": "...", "type": "RELATED_TO|USES|REQUIRES|PART_OF"}}],
  "candidate_qas": [{{"question":"...","answer":"..."}}]
}}

Constraints:
- entities: 5-12 max
- relationships: 3-10 max
- candidate_qas: 0-3 max
"""
            raw = self.chat([{"role": "user", "content": prompt}], temperature=0.2, max_tokens=1200)
            obj = expect_json_object(raw)

        entities: List[Entity] = []
        for e in obj.get("entities", []) or []:
            if not isinstance(e, dict):
                continue
            name = str(e.get("name", "")).strip()
            etype = str(e.get("type", "OTHER")).strip().upper()
            if name:
                entities.append(Entity(name=name, type=etype))

        relationships: List[Dict[str, str]] = []
        for r in obj.get("relationships", []) or []:
            if not isinstance(r, dict):
                continue
            src = str(r.get("source", "")).strip()
            tgt = str(r.get("target", "")).strip()
            rtype = str(r.get("type", "RELATED_TO")).strip().upper()
            if src and tgt:
                relationships.append({"source": src, "target": tgt, "type": rtype})

        tags = self.extract_keywords(chunk.text)

        cqa: List[Dict[str, str]] = []
        for qa in obj.get("candidate_qas", []) or []:
            if not isinstance(qa, dict):
                continue
            q = str(qa.get("question", "")).strip()
            a = str(qa.get("answer", "")).strip()
            if q and a:
                cqa.append({"question": q, "answer": a})

        return ChunkAnnotation(
            chunk_type=str(obj.get("chunk_type", "other")).strip(),
            summary=str(obj.get("summary", "")).strip() if obj.get("summary") is not None else None,
            entities=entities,
            relationships=relationships,
            tags=tags,
            candidate_qas=cqa,
        )

    def generate_answer(self, question: str, context: str, system_prompt: Optional[str] = None) -> str:
        sys = system_prompt or (
            "You are a technical assistant. Use ONLY the provided context.\n"
            "If the context is insufficient, say what is missing.\n"
            "When referring to facts, cite the document titles explicitly.\n"
        )
        def _messages(ctx: str) -> List[ChatMessage]:
            return [
                {"role": "system", "content": sys},
                {"role": "user", "content": f"Context:\n{ctx}\n\nQuestion:\n{question}\n\nAnswer:"},
            ]

        base_context = context or ""
        try:
            return self.chat(_messages(base_context), temperature=0.3, max_tokens=1500)
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status != 400:
                raise

            # Retry with reduced context for local models that reject large prompts.
            for limit in (8000, 5000, 3000, 1800):
                if len(base_context) <= limit:
                    continue
                compact = base_context[:limit] + "\n...[context truncated due model limits]..."
                try:
                    return self.chat(_messages(compact), temperature=0.3, max_tokens=1200)
                except requests.HTTPError as retry_exc:
                    retry_status = retry_exc.response.status_code if retry_exc.response is not None else None
                    if retry_status != 400:
                        raise
                    exc = retry_exc

            # Last-resort answer without full context, preserving user question handling.
            fallback_ctx = "Context omitted because model rejected oversized prompt."
            return self.chat(_messages(fallback_ctx), temperature=0.3, max_tokens=800)


class GraphRagQAAgent:
    """
    Inference-time GraphRAG agent with hybrid retrieval (vector + graph).

    Retrieval strategy:
      1) Use LLM to extract entity/topic strings from the question
      2) Seed chunks from graph matches (Entity/Tag) in Neo4j
      3) Seed chunks from Neo4j vector kNN over Chunk embeddings
      4) Union seeds and expand neighborhood with GraphRag.expand_from_seeds()
      5) Generate answer with LM Studio from assembled context

    This works with the ingestion pipeline shown in the demo script.
    """

    def __init__(
        self,
        neo4j: Neo4jClient,
        graph: GraphRag,
        llm: LMStudioClient,
        *,
        default_hops: int = 2,
        seed_limit: int = 8,
        expansion_limit: int = 50,
        vector_top_k: int = 6,
        vector_index_name: Optional[str] = None,
        seed_rrf_k: int = 60,
        context_seed_limit: int = 16,
        context_neighbor_limit: int = 24,
        rerank_vector_weight: float = 0.55,
        rerank_graph_weight: float = 0.25,
        rerank_term_weight: float = 0.20,
        rerank_seed_boost: float = 0.10,
        tracing_enabled: Optional[bool] = None,
        tracing_project: Optional[str] = None,
        tracing_tags: Optional[List[str]] = None,
    ):
        self.neo4j = neo4j
        self.graph = graph
        self.llm = llm
        self.default_hops = default_hops
        self.seed_limit = seed_limit
        self.expansion_limit = expansion_limit
        self.vector_top_k = max(1, int(vector_top_k))
        self.vector_index_name = (
            vector_index_name
            or os.environ.get("NEO4J_VECTOR_INDEX", "chunk_embedding_index")
        )
        self.seed_rrf_k = max(1, int(seed_rrf_k))
        self.context_seed_limit = max(1, int(context_seed_limit))
        self.context_neighbor_limit = max(1, int(context_neighbor_limit))
        self.rerank_vector_weight = max(0.0, float(rerank_vector_weight))
        self.rerank_graph_weight = max(0.0, float(rerank_graph_weight))
        self.rerank_term_weight = max(0.0, float(rerank_term_weight))
        self.rerank_seed_boost = max(0.0, float(rerank_seed_boost))
        self.tracing_enabled = _resolve_tracing_enabled(tracing_enabled)
        self.tracing_project = (
            tracing_project
            or os.environ.get("LANGSMITH_PROJECT")
            or os.environ.get("LANGCHAIN_PROJECT")
        )
        self.tracing_tags = tracing_tags or _split_csv_env(
            os.environ.get("LANGSMITH_TAGS") or os.environ.get("LANGCHAIN_TAGS")
        )

    @contextmanager
    def _tracing_scope(self, *, question: str) -> Iterator[None]:
        metadata = {
            "agent": "GraphRagQAAgent",
            "llm_provider": "lm_studio",
            "llm_model": self.llm.cfg.model,
            "embedding_model": self.llm.embedding_model_id,
            "embedding_backend": self.llm.active_embedding_backend,
            "llm_base_url": self.llm.cfg.base_url,
            "default_hops": self.default_hops,
            "seed_limit": self.seed_limit,
            "expansion_limit": self.expansion_limit,
            "vector_top_k": self.vector_top_k,
            "vector_index_name": self.vector_index_name,
            "seed_rrf_k": self.seed_rrf_k,
            "context_seed_limit": self.context_seed_limit,
            "context_neighbor_limit": self.context_neighbor_limit,
            "rerank_vector_weight": self.rerank_vector_weight,
            "rerank_graph_weight": self.rerank_graph_weight,
            "rerank_term_weight": self.rerank_term_weight,
            "rerank_seed_boost": self.rerank_seed_boost,
            "question_chars": len(question or ""),
        }
        with tracing_context(
            enabled=self.tracing_enabled,
            project_name=self.tracing_project,
            tags=self.tracing_tags,
            metadata=metadata,
        ):
            yield

    @traceable(
        run_type="retriever",
        name="graph_rag.extract_query_entities",
        process_inputs=_trace_process_inputs,
    )
    def _extract_query_terms(self, question: str) -> List[str]:
        return self.llm.extract_query_entities(question, max_entities=3)

    @traceable(
        run_type="retriever",
        name="graph_rag.expand_from_seeds",
        process_inputs=_trace_process_inputs,
    )
    def _expand_graph_context(self, seeds: List[str]) -> Dict[str, Any]:
        return self.graph.expand_from_seeds(
            seed_chunk_ids=seeds,
            hops=self.default_hops,
            limit=self.expansion_limit,
            include_faq=True,
        )

    @traceable(
        run_type="llm",
        name="graph_rag.generate_answer",
        process_inputs=_trace_process_inputs,
    )
    def _generate_answer_text(self, question: str, context_text: str) -> str:
        return self.llm.generate_answer(question, context_text)

    @staticmethod
    def _merge_context(
        graph_context_text: str,
        supplemental_context: Optional[str],
    ) -> str:
        extra = (supplemental_context or "").strip()
        if not extra:
            return graph_context_text

        max_extra_chars = max(200, int(os.environ.get("SUPPLEMENTAL_CONTEXT_MAX_CHARS", "2200")))
        if len(extra) > max_extra_chars:
            extra = extra[: max_extra_chars - 3] + "..."
        return (
            f"{graph_context_text}\n\n"
            "EXTERNAL TOOL CONTEXT:\n"
            f"{extra}"
        )

    @traceable(
        run_type="retriever",
        name="graph_rag.seed_chunks",
        process_inputs=_trace_process_inputs,
    )
    def _seed_chunks(self, terms: List[str]) -> List[str]:
        if not terms:
            return []

        # 1) seed by entity name match
        cypher_ent = """
        MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)
        WHERE coalesce(c.active, true)
        WITH c, collect(toLower(e.name)) AS entity_names
        WITH c, size([term IN $terms WHERE any(name IN entity_names WHERE name CONTAINS toLower(term))]) AS match_count
        WHERE match_count > 0
        RETURN c.chunk_id AS chunk_id
        ORDER BY match_count DESC, c.chunk_index ASC
        LIMIT $limit
        """
        rows = self.neo4j.run(cypher_ent, {"terms": terms, "limit": self.seed_limit})
        seeds = [r["chunk_id"] for r in rows if r.get("chunk_id")]

        if seeds:
            return seeds

        # 2) fallback: seed by tag match
        cypher_tag = """
        MATCH (c:Chunk)-[:HAS_TAG]->(t:Tag)
        WHERE coalesce(c.active, true)
        WITH c, collect(toLower(t.name)) AS tag_names
        WITH c, size([term IN $terms WHERE any(name IN tag_names WHERE name CONTAINS toLower(term))]) AS match_count
        WHERE match_count > 0
        RETURN c.chunk_id AS chunk_id
        ORDER BY match_count DESC, c.chunk_index ASC
        LIMIT $limit
        """
        rows = self.neo4j.run(cypher_tag, {"terms": terms, "limit": self.seed_limit})
        return [r["chunk_id"] for r in rows if r.get("chunk_id")]

    @traceable(
        run_type="retriever",
        name="graph_rag.vector_seed_chunks",
        process_inputs=_trace_process_inputs,
    )
    def _vector_seed_chunks(self, question: str) -> List[Dict[str, Any]]:
        if not question.strip():
            return []
        query_embedding = self.llm.embed_query(question)
        if not query_embedding:
            return []
        return self.graph.vector_search_chunks(
            query_embedding,
            top_k=self.vector_top_k,
            index_name=self.vector_index_name,
        )

    @staticmethod
    def _minmax_normalize(values: Dict[str, float]) -> Dict[str, float]:
        if not values:
            return {}
        lo = min(values.values())
        hi = max(values.values())
        if math.isclose(lo, hi):
            return {k: 1.0 for k in values}
        span = hi - lo
        return {k: (v - lo) / span for k, v in values.items()}

    @traceable(
        run_type="retriever",
        name="graph_rag.merge_hybrid_seeds",
        process_inputs=_trace_process_inputs,
    )
    def _merge_seed_candidates(
        self,
        graph_seed_ids: List[str],
        vector_hits: List[Dict[str, Any]],
    ) -> Tuple[List[str], List[str], Dict[str, Dict[str, Any]]]:
        graph_seed_ids = [cid for cid in graph_seed_ids if cid]
        graph_seed_ids = list(dict.fromkeys(graph_seed_ids))

        vector_ranked: List[Tuple[str, float]] = []
        for hit in vector_hits:
            chunk_id = str(hit.get("chunk_id") or "").strip()
            if not chunk_id:
                continue
            try:
                score = float(hit.get("score", 0.0) or 0.0)
            except Exception:
                score = 0.0
            vector_ranked.append((chunk_id, score))

        vector_ranked.sort(key=lambda x: x[1], reverse=True)
        vector_seed_ids = list(dict.fromkeys([cid for cid, _ in vector_ranked]))

        vector_score_raw: Dict[str, float] = {}
        for cid, score in vector_ranked:
            prev = vector_score_raw.get(cid)
            if prev is None or score > prev:
                vector_score_raw[cid] = score
        vector_norm = self._minmax_normalize(vector_score_raw)

        graph_rank = {cid: idx + 1 for idx, cid in enumerate(graph_seed_ids)}
        vector_rank = {cid: idx + 1 for idx, cid in enumerate(vector_seed_ids)}

        candidate_ids = list(dict.fromkeys(vector_seed_ids + graph_seed_ids))
        seed_signals: Dict[str, Dict[str, Any]] = {}
        for cid in candidate_ids:
            rrf_score = 0.0
            if cid in vector_rank:
                rrf_score += 1.0 / (self.seed_rrf_k + vector_rank[cid])
            if cid in graph_rank:
                rrf_score += 1.0 / (self.seed_rrf_k + graph_rank[cid])

            seed_signals[cid] = {
                "chunk_id": cid,
                "rrf_score": rrf_score,
                "vector_score": vector_score_raw.get(cid, 0.0),
                "vector_norm": vector_norm.get(cid, 0.0),
                "vector_rank": vector_rank.get(cid),
                "graph_rank": graph_rank.get(cid),
            }

        rrf_norm = self._minmax_normalize(
            {cid: float(meta.get("rrf_score", 0.0)) for cid, meta in seed_signals.items()}
        )
        for cid, meta in seed_signals.items():
            meta["rrf_norm"] = rrf_norm.get(cid, 0.0)
            meta["merge_score"] = meta["rrf_score"] + 0.15 * meta["vector_norm"]

        merged_seed_ids = sorted(
            candidate_ids,
            key=lambda cid: (
                float(seed_signals[cid].get("merge_score", 0.0)),
                float(seed_signals[cid].get("vector_score", 0.0)),
                1.0 if seed_signals[cid].get("graph_rank") is not None else 0.0,
                cid,
            ),
            reverse=True,
        )
        return merged_seed_ids, vector_seed_ids, seed_signals

    def _score_chunk_for_rerank(
        self,
        chunk: Dict[str, Any],
        terms_lower: List[str],
        seed_signals: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        chunk_id = str(chunk.get("chunk_id") or "")
        signal = seed_signals.get(chunk_id, {})

        vector_signal = float(signal.get("vector_norm", 0.0) or 0.0)
        graph_signal = 1.0 if signal.get("graph_rank") is not None else 0.0
        seed_signal = 1.0 if signal else 0.0
        hybrid_rank_signal = float(signal.get("rrf_norm", 0.0) or 0.0)

        text_lower = str(chunk.get("text") or "").lower()
        term_signal = 0.0
        if terms_lower:
            matched = sum(1 for term in terms_lower if term and term in text_lower)
            term_signal = matched / float(len(terms_lower))

        score = (
            self.rerank_vector_weight * vector_signal
            + self.rerank_graph_weight * max(graph_signal, hybrid_rank_signal)
            + self.rerank_term_weight * term_signal
            + self.rerank_seed_boost * seed_signal
        )
        return {
            "score": float(score),
            "vector_signal": vector_signal,
            "graph_signal": graph_signal,
            "term_signal": term_signal,
            "seed_signal": seed_signal,
            "hybrid_rank_signal": hybrid_rank_signal,
        }

    @traceable(
        run_type="retriever",
        name="graph_rag.rerank_context",
        process_inputs=_trace_process_inputs,
    )
    def _rerank_enriched_context(
        self,
        ctx: Dict[str, Any],
        terms: List[str],
        seed_signals: Dict[str, Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        terms_lower = [t.strip().lower() for t in terms if isinstance(t, str) and t.strip()]

        def _rerank_chunks(chunks: List[Dict[str, Any]], limit: int, source: str) -> List[Dict[str, Any]]:
            ranked: List[Dict[str, Any]] = []
            for chunk in chunks:
                item = dict(chunk)
                score_meta = self._score_chunk_for_rerank(item, terms_lower, seed_signals)
                item["retrieval_score"] = round(float(score_meta["score"]), 6)
                item["retrieval_components"] = {
                    "vector": round(float(score_meta["vector_signal"]), 6),
                    "graph": round(float(score_meta["graph_signal"]), 6),
                    "term": round(float(score_meta["term_signal"]), 6),
                    "seed": round(float(score_meta["seed_signal"]), 6),
                    "hybrid_rank": round(float(score_meta["hybrid_rank_signal"]), 6),
                    "source": source,
                }
                ranked.append(item)
            ranked.sort(
                key=lambda c: (
                    float(c.get("retrieval_score", 0.0) or 0.0),
                    str(c.get("chunk_id") or ""),
                ),
                reverse=True,
            )
            return ranked[: max(1, int(limit))]

        seed_chunks = _rerank_chunks(
            list(ctx.get("seed_chunks", []) or []),
            self.context_seed_limit,
            "seed",
        )
        neighbor_chunks = _rerank_chunks(
            list(ctx.get("chunks", []) or []),
            self.context_neighbor_limit,
            "neighbor",
        )

        reranked_debug: List[Dict[str, Any]] = []
        for chunk in seed_chunks + neighbor_chunks:
            comps = chunk.get("retrieval_components") or {}
            reranked_debug.append(
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "doc_id": chunk.get("doc_id"),
                    "retrieval_score": chunk.get("retrieval_score"),
                    "source": comps.get("source"),
                    "vector": comps.get("vector"),
                    "graph": comps.get("graph"),
                    "term": comps.get("term"),
                    "seed": comps.get("seed"),
                    "hybrid_rank": comps.get("hybrid_rank"),
                }
            )

        updated = dict(ctx)
        updated["seed_chunks"] = seed_chunks
        updated["chunks"] = neighbor_chunks
        return updated, reranked_debug

    @staticmethod
    def _enrich_context(ctx: Dict[str, Any], seed_chunk_ids: List[str]) -> Dict[str, Any]:
        nodes = ctx.get("nodes", []) or []
        chunks = ctx.get("chunks", []) or []
        seed_set = set(seed_chunk_ids or [])

        seed_chunks: List[Dict[str, Any]] = []
        neighbor_chunks: List[Dict[str, Any]] = []
        for c in chunks:
            if c.get("chunk_id") in seed_set:
                seed_chunks.append(c)
            else:
                neighbor_chunks.append(c)

        docs: List[Dict[str, Any]] = []
        seen_docs: set[str] = set()
        for c in chunks:
            doc_id = c.get("doc_id") or c.get("document_id")
            if not doc_id or doc_id in seen_docs:
                continue
            docs.append({"doc_id": doc_id, "title": c.get("title") or ""})
            seen_docs.add(doc_id)

        tags: List[str] = []
        seen_tags: set[str] = set()
        entities: List[Dict[str, Any]] = []
        seen_entities: set[str] = set()
        faqs: List[Dict[str, Any]] = []
        seen_faqs: set[str] = set()

        for node in nodes:
            labels = node.get("labels") or []
            props = node.get("properties") or {}

            if "Tag" in labels:
                name = props.get("name")
                if name:
                    tag = str(name)
                    if tag not in seen_tags:
                        tags.append(tag)
                        seen_tags.add(tag)

            if "Entity" in labels:
                name = props.get("name")
                if name:
                    etype = str(props.get("type") or "")
                    key = f"{name}::{etype}"
                    if key not in seen_entities:
                        entities.append({"name": str(name), "type": etype})
                        seen_entities.add(key)

            if "FAQ" in labels:
                faq_id = str(props.get("faq_id") or "")
                question = str(props.get("question") or "")
                answer = str(props.get("answer") or "")
                key = faq_id or question
                if key and key not in seen_faqs:
                    faqs.append({"faq_id": faq_id, "question": question, "answer": answer})
                    seen_faqs.add(key)

        enriched = dict(ctx)
        enriched["documents"] = docs
        enriched["tags"] = tags
        enriched["entities"] = entities
        enriched["faqs"] = faqs
        enriched["seed_chunks"] = seed_chunks
        enriched["chunks"] = neighbor_chunks
        enriched["seed_chunk_ids"] = seed_chunk_ids
        return enriched

    @staticmethod
    def _render_context(ctx: Dict[str, Any]) -> str:
        docs = ctx.get("documents", []) or []
        seed_chunks = ctx.get("seed_chunks", []) or []
        chunks = ctx.get("chunks", []) or []
        tags = ctx.get("tags", []) or []
        entities = ctx.get("entities", []) or []
        faqs = ctx.get("faqs", []) or []

        lines: List[str] = []
        if docs:
            lines.append("DOCUMENTS:")
            for d in docs:
                title = d.get("title", "")
                doc_id = d.get("doc_id", "")
                lines.append(f"- {title} (doc_id={doc_id})")
            lines.append("")

        if tags:
            lines.append("TAGS:")
            lines.append(", ".join(tags[:30]))
            lines.append("")

        if entities:
            lines.append("ENTITIES:")
            lines.append(", ".join([f"{e.get('name')}[{e.get('type')}]" for e in entities[:30]]))
            lines.append("")

        def _fmt_chunk(c: Dict[str, Any]) -> str:
            txt = (c.get("text") or "").strip().replace("\n", " ")
            if len(txt) > 800:
                txt = txt[:800] + "…"
            return f"- chunk_id={c.get('chunk_id')} doc_id={c.get('doc_id')} :: {txt}"

        if seed_chunks:
            lines.append("SEED CHUNKS:")
            for c in seed_chunks[:20]:
                lines.append(_fmt_chunk(c))
            lines.append("")

        if chunks:
            lines.append("NEIGHBOR CHUNKS:")
            for c in chunks[:20]:
                lines.append(_fmt_chunk(c))
            lines.append("")

        if faqs:
            lines.append("FAQ (linked):")
            for f in faqs[:10]:
                q = (f.get("question") or "").strip()
                a = (f.get("answer") or "").strip()
                if len(a) > 300:
                    a = a[:300] + "…"
                lines.append(f"- Q: {q}\n  A: {a}")
            lines.append("")

        return "\n".join(lines).strip() or "No graph context found."

    @staticmethod
    def _build_citations(ctx: Dict[str, Any]) -> List[Citation]:
        doc_title = {d.get("doc_id"): d.get("title") for d in (ctx.get("documents", []) or [])}
        citations: List[Citation] = []

        for c in (ctx.get("seed_chunks", []) or [])[:10]:
            doc_id = c.get("doc_id")
            score = c.get("retrieval_score")
            citation_score = float(score) if score is not None else None
            citations.append(
                Citation(
                    doc_id=doc_id or "",
                    chunk_id=c.get("chunk_id") or "",
                    title=doc_title.get(doc_id, "") or "",
                    url=None,
                    score=citation_score,
                )
            )
        return citations

    @traceable(
        run_type="chain",
        name="graph_rag.answer",
        process_inputs=_trace_process_inputs,
        process_outputs=_trace_process_answer_output,
    )
    def answer(
        self,
        question: str,
        *,
        include_trace: bool = False,
        supplemental_context: Optional[str] = None,
    ) -> AnswerWithCitations:
        with self._tracing_scope(question=question):
            terms = self._extract_query_terms(question)
            graph_seed_ids = self._seed_chunks(terms)

            vector_hits: List[Dict[str, Any]] = []
            vector_seed_error: Optional[str] = None
            try:
                vector_hits = self._vector_seed_chunks(question)
            except Exception as exc:
                vector_seed_error = str(exc)

            merged_seed_ids, vector_seed_ids, seed_signals = self._merge_seed_candidates(
                graph_seed_ids,
                vector_hits,
            )

            raw_ctx = self._expand_graph_context(merged_seed_ids)
            ctx = self._enrich_context(raw_ctx, merged_seed_ids)
            ctx, reranked_chunks = self._rerank_enriched_context(ctx, terms, seed_signals)
            graph_context_text = self._render_context(ctx)
            context_text = self._merge_context(graph_context_text, supplemental_context)
            answer_text = self._generate_answer_text(question, context_text)

            debug: Dict[str, Any] = {
                "terms": terms,
                "seed_chunk_ids": merged_seed_ids,
                "graph_seed_chunk_ids": graph_seed_ids,
                "vector_seed_chunk_ids": vector_seed_ids,
                "seed_merge_signals": list(seed_signals.values()),
            }
            if include_trace:
                debug["graph_context"] = {
                    "nodes": ctx.get("nodes", []),
                    "edges": ctx.get("edges", []),
                    "documents": ctx.get("documents", []),
                    "tags": ctx.get("tags", []),
                    "entities": ctx.get("entities", []),
                    "faqs": ctx.get("faqs", []),
                    "seed_chunks": ctx.get("seed_chunks", []),
                    "neighbor_chunks": ctx.get("chunks", []),
                }
                debug["context_text"] = context_text
                if supplemental_context:
                    debug["supplemental_context"] = supplemental_context
                debug["vector_hits"] = vector_hits
                debug["reranked_chunks"] = reranked_chunks
                if vector_seed_error:
                    debug["vector_seed_error"] = vector_seed_error
                debug["observability"] = {
                    "langsmith_enabled": self.tracing_enabled,
                    "langsmith_project": self.tracing_project or "",
                    "langsmith_tags": list(self.tracing_tags or []),
                    "embedding_backend": self.llm.active_embedding_backend,
                    "embedding_model": self.llm.embedding_model_id,
                    "vector_top_k": self.vector_top_k,
                    "seed_rrf_k": self.seed_rrf_k,
                    "context_seed_limit": self.context_seed_limit,
                    "context_neighbor_limit": self.context_neighbor_limit,
                    "rerank_vector_weight": self.rerank_vector_weight,
                    "rerank_graph_weight": self.rerank_graph_weight,
                    "rerank_term_weight": self.rerank_term_weight,
                    "rerank_seed_boost": self.rerank_seed_boost,
                }

            return AnswerWithCitations(
                answer=answer_text,
                citations=self._build_citations(ctx),
                debug=debug,
            )

    def invoke(self, payload: str | Dict[str, Any]) -> Dict[str, Any]:
        """
        LangChain-style invoke entrypoint.

        Accepts either:
          - plain string question
          - {"question": "...", "include_trace": bool, "supplemental_context": "..."}
        """
        if isinstance(payload, str):
            question = payload.strip()
            include_trace = False
            supplemental_context = None
        elif isinstance(payload, dict):
            question = str(payload.get("question", "")).strip()
            include_trace = bool(payload.get("include_trace", False))
            supplemental_context = payload.get("supplemental_context")
            if supplemental_context is not None:
                supplemental_context = str(supplemental_context)
        else:
            raise TypeError("payload must be str or dict")

        if not question:
            raise ValueError("question must be non-empty")

        result = self.answer(
            question,
            include_trace=include_trace,
            supplemental_context=supplemental_context,
        )
        return {
            "answer": result.answer,
            "citations": [
                {
                    "doc_id": c.doc_id,
                    "chunk_id": c.chunk_id,
                    "title": c.title,
                    "url": c.url,
                    "score": c.score,
                }
                for c in result.citations
            ],
            "debug": result.debug,
        }

    def as_langchain_runnable(self) -> Any:
        """
        Build a Runnable adapter for LangChain/LangGraph pipelines.
        """
        try:
            from langchain_core.runnables import RunnableLambda
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("langchain_core is required for runnable adapter.") from exc

        return RunnableLambda(self.invoke).with_config(run_name="graph_rag_qa_agent")
