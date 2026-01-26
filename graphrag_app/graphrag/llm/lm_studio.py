from __future__ import annotations

import time
import requests
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from graphrag.llm.base import (
    ChatMessage,
    LLMClient,
    expect_json_array,
    expect_json_object,
)
from graphrag.types.models import Chunk, ChunkAnnotation, Entity, FAQEntry, AnswerWithCitations, Citation
from graphrag.graph.graph_rag import GraphRag
from graphrag.storage.neo4j_client import Neo4jClient


@dataclass(frozen=True)
class LMStudioConfig:
    """
    LM Studio REST server configuration.

    LM Studio provides OpenAI-compatible endpoints; commonly you point a client at
    http://localhost:1234/v1 and call /chat/completions. :contentReference[oaicite:0]{index=0}
    """
    base_url: str = "http://localhost:1234"
    model: str = "local-model"
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

    @staticmethod
    def _normalize_chat_url(base_url: str) -> str:
        base = base_url.rstrip("/")
        # allow either "...:1234" or "...:1234/v1"
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        return f"{base}/v1/chat/completions"

    def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 1500,
        timeout_s: int = 60,
    ) -> str:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.cfg.api_key:
            headers["Authorization"] = f"Bearer {self.cfg.api_key}"

        payload = {
            "model": self.cfg.model,
            "messages": list(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.95,
        }

        resp = requests.post(self._chat_url, json=payload, headers=headers, timeout=timeout_s)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def extract_query_entities(self, question: str, max_entities: int = 3) -> List[str]:
        prompt = (
            "Extract up to {n} key entities/topics from this question.\n"
            "Return ONLY a JSON array of strings, no extra text.\n\n"
            "Question:\n{q}\n"
        ).format(n=max_entities, q=question)

        raw = self.chat([{"role": "user", "content": prompt}], temperature=0.1, max_tokens=200)
        arr = expect_json_array(raw)
        out: List[str] = []
        for x in arr:
            if isinstance(x, str) and x.strip():
                out.append(x.strip())
        return out[:max_entities]

    def annotate_chunk(self, chunk: Chunk) -> ChunkAnnotation:
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
  "tags": ["...","..."],
  "candidate_qas": [{{"question":"...","answer":"..."}}]
}}

Constraints:
- entities: 5-12 max
- relationships: 3-10 max
- tags: 5-15 max
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

        tags: List[str] = []
        for t in obj.get("tags", []) or []:
            if isinstance(t, str) and t.strip():
                tags.append(t.strip())

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
        messages: List[ChatMessage] = [
            {"role": "system", "content": sys},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{question}\n\nAnswer:"},
        ]
        return self.chat(messages, temperature=0.3, max_tokens=1500)


class GraphRagQAAgent:
    """
    Minimal inference-time GraphRAG agent (graph-only retrieval).

    Retrieval strategy (no vector store required):
      1) Use LLM to extract entity/topic strings from the question
      2) Use those strings to find seed chunks via Entity/Tag matches in Neo4j
      3) Expand neighborhood with GraphRag.expand_from_seeds()
      4) Generate answer with LM Studio from assembled context

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
    ):
        self.neo4j = neo4j
        self.graph = graph
        self.llm = llm
        self.default_hops = default_hops
        self.seed_limit = seed_limit
        self.expansion_limit = expansion_limit

    def _seed_chunks(self, terms: List[str]) -> List[str]:
        if not terms:
            return []

        # 1) seed by entity name match
        cypher_ent = """
        MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)
        WHERE any(t IN $terms WHERE toLower(e.name) CONTAINS toLower(t))
          AND coalesce(c.active, true)
        RETURN DISTINCT c.chunk_id AS chunk_id
        LIMIT $limit
        """
        rows = self.neo4j.run(cypher_ent, {"terms": terms, "limit": self.seed_limit})
        seeds = [r["chunk_id"] for r in rows if r.get("chunk_id")]

        if seeds:
            return seeds

        # 2) fallback: seed by tag match
        cypher_tag = """
        MATCH (c:Chunk)-[:HAS_TAG]->(t:Tag)
        WHERE any(x IN $terms WHERE toLower(t.name) CONTAINS toLower(x))
          AND coalesce(c.active, true)
        RETURN DISTINCT c.chunk_id AS chunk_id
        LIMIT $limit
        """
        rows = self.neo4j.run(cypher_tag, {"terms": terms, "limit": self.seed_limit})
        return [r["chunk_id"] for r in rows if r.get("chunk_id")]

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
            citations.append(
                Citation(
                    doc_id=doc_id or "",
                    chunk_id=c.get("chunk_id") or "",
                    title=doc_title.get(doc_id, "") or "",
                    url=None,
                    score=None,
                )
            )
        return citations

    def answer(self, question: str) -> AnswerWithCitations:
        terms = self.llm.extract_query_entities(question, max_entities=3)
        seeds = self._seed_chunks(terms)

        ctx = self.graph.expand_from_seeds(
            seed_chunk_ids=seeds,
            hops=self.default_hops,
            limit=self.expansion_limit,
            include_faq=True,
        )
        context_text = self._render_context(ctx)
        answer_text = self.llm.generate_answer(question, context_text)

        return AnswerWithCitations(
            answer=answer_text,
            citations=self._build_citations(ctx),
            debug={"terms": terms, "seed_chunk_ids": seeds},
        )
