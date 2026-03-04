# Knowledge Agent — Developer README

This project builds a lightweight GraphRAG pipeline on top of **Neo4j** and a local LLM served by **LM Studio**. It ingests local documents listed in `data/data.json`, splits them into chunks, extracts entities/relationships/tags via the LLM, and stores everything in Neo4j for graph‑based retrieval.

---

## What’s implemented

- **Local file ingestion** from `data/data.json` using `file_path` (supports `.docx`, `.rtf`, `.txt`, `.md`).
- **Chunking** via LangChain text splitters (context‑aware or token‑based).
- **LLM annotation** per chunk (entities, relationships, summary, candidate Q&A) using LM Studio.
- **Keyword/tag extraction** using structured JSON output.
- **Neo4j graph schema** creation and upserts for `Document`, `Chunk`, `Entity`, `Tag` and relationships.
- **Hybrid GraphRAG retrieval** (vector kNN seeding + entity/tag seeding + graph expansion + answer generation).
- **CLI commands** in the demo app (`stats`, `docs`, `entity`, `find`, `trace`).
- **LLM result caching** to `processed_docs/llm_annotations.json` to avoid re‑processing unchanged documents.

---

## Requirements

### Runtime
- **Python 3.11+** (see `pyproject.toml`)
- **Neo4j 5/6** running locally (Bolt + Browser)
- **LM Studio** running in OpenAI‑compatible server mode (`/v1/chat/completions`)

### Python packages
From `pyproject.toml`:
- `langchain`
- `langgraph`
- `neo4j`
- `openai`
- `python-dotenv`

Additional packages used in code (install manually if missing):
- `requests` (LM Studio client)
- `langchain-text-splitters` (chunking)
- `tiktoken` (only required for `CHUNK_MODE=token`)

---

## Models used

The demo app uses **LM Studio** with an OpenAI‑compatible endpoint. Default model in code:

- `qwen2.5-1.5b-instruct`

Override via env var:

- `LMSTUDIO_MODEL`

---

## How to run

### 1) Start Neo4j
Ensure Neo4j is running locally (default Bolt on `neo4j://localhost:7687`, Browser on `http://localhost:7474`).

Docker example:

```bash
docker run \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/<password> \
  neo4j:5
```

### 2) Start LM Studio
Start LM Studio server with OpenAI‑compatible endpoints (default `http://localhost:1234/v1`).

### 3) Configure environment
Configure these environment variables (override as needed). A ready template is in `env_sample`:

```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="airestairest"

export LMSTUDIO_URL="http://localhost:1234"
export LMSTUDIO_MODEL="qwen2.5-1.5b-instruct"
export LMSTUDIO_EMBED_MODEL="text-embedding-nomic-embed-text-v1.5"
export LMSTUDIO_EMBED_FALLBACK="true"     # fallback to local hash embeddings if /v1/embeddings is unsupported
export LOCAL_EMBED_DIMENSIONS="384"       # used only for local hash fallback

export DATA_JSON="/Users/pelmeshek1706/Desktop/projects/knowledge_agent/data/data.json"

# Chunking config
export CHUNK_MODE="context"   # or "token"
export CHUNK_SIZE="1200"
export CHUNK_OVERLAP="200"

# Cache location
export PROCESSED_DOCS_DIR="processed_docs"

# Hybrid retrieval (Neo4j vector + graph)
export NEO4J_VECTOR_INDEX="chunk_embedding_index"
export NEO4J_VECTOR_SIMILARITY="cosine"
export VECTOR_TOP_K="6"

# LangSmith tracing (optional, for LangChain/LangGraph observability)
export LANGSMITH_TRACING="true"
export LANGSMITH_API_KEY="<your_langsmith_key>"
export LANGSMITH_PROJECT="knowledge-agent-local"
# export LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
# export LANGSMITH_WORKSPACE_ID="<workspace_id>"
# export LANGSMITH_TAGS="local,lmstudio,graphrag"
```

### 4) Run the demo app

```bash
PYTHONPATH=graphrag_app python graphrag_app/demo_agent_on_data_json.py
```

On first run, it ingests documents, annotates chunks with the LLM, and writes results into Neo4j. Later runs reuse cached annotations if the document text and chunking config are unchanged.

---

## How caching works (faster startup)

- Cache file: `processed_docs/llm_annotations.json`
- Cache key = file path (or doc_id) + **content hash** + **chunk config signature**
- If the file content or chunk settings change, the document is reprocessed.
- To force full re‑processing, delete `processed_docs/llm_annotations.json`.

---

## How to verify updates in Neo4j

Open Neo4j Browser: `http://localhost:7474`

Useful Cypher queries:

```cypher
// List documents
MATCH (d:Document)
RETURN d.doc_id, d.title, d.file_path, d.updated_at
ORDER BY d.updated_at DESC;
```

```cypher
// Count chunks per document
MATCH (d:Document)-[:CONTAINS]->(c:Chunk)
RETURN d.doc_id, d.title, count(c) AS chunks
ORDER BY chunks DESC;
```

```cypher
// Recent tags
MATCH (c:Chunk)-[:HAS_TAG]->(t:Tag)
RETURN t.name, count(*) AS uses
ORDER BY uses DESC
LIMIT 20;
```

```cypher
// Entities and their connections
MATCH (e:Entity)-[r]->(e2:Entity)
RETURN e.name, type(r), e2.name
LIMIT 50;
```

If you see newly ingested docs/chunks in these queries, the update succeeded.

---

## Features by file

- `graphrag_app/demo_agent_on_data_json.py`
  - Ingests `data/data.json`
  - Reads real file content from `file_path`
  - Splits into chunks via `LMStudioClient.split_document`
  - Calls `LMStudioClient.annotate_chunk` per chunk
  - Writes graph data to Neo4j
  - Caches LLM results in `processed_docs/llm_annotations.json`
  - Prints LangSmith tracing status (ON/OFF) on startup

- `graphrag_app/graphrag/llm/lm_studio.py`
  - LM Studio OpenAI‑style client
  - Structured output for keyword extraction + chunk annotation
  - Embeddings via LM Studio `/v1/embeddings` with local hash fallback
  - Chunk splitting (context or token based)
  - Hybrid retrieval in QA agent (vector + graph)
  - LangSmith tracing hooks for GraphRAG pipeline spans
  - LangChain-compatible `invoke()` and `as_langchain_runnable()` adapter

---

## Future plans / TODO

- Add **PDF** ingestion and better **RTF** parsing.
- Add **vector embeddings** + Neo4j vector index for hybrid retrieval.
- Add **Notion / Google Drive** connectors.
- Add **document change detection** based on file mtime in addition to content hash.
- Add **tests** for ingestion and cache correctness.
- Improve **error handling** when LM Studio fails schema outputs.
- add telegram/streamlit/gradio integrations
- enchance document processing
- created question-answer sessions "faq" document for quick answers and add it to tool
- add tool calling to agent
- add web search for additional context from internet as "tool"
- add "wiki" for all documents by firstly implement mind map, then when user try to find some information - model generated an answer and add it to wiki
---

## Notes

- If you see JSON parsing errors from the LLM, ensure LM Studio supports `response_format` with `json_schema`.
- For token‑based chunking, install `tiktoken`.
- Default data is in `data/data.json`, and `description` is treated as metadata (not the chunk text).
