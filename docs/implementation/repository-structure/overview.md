# Repository Structure Overview

## Purpose

This file explains the high-level repository structure for `personal_kb` and preserves the original repository-wide design rule.

## When to read this

Read this when you need the project-wide layout, the MVP runtime flow, or the top-level rule for where business logic belongs.

## Related files

- [project-root-and-runtime-data.md](project-root-and-runtime-data.md)
- [package-boundaries-and-import-rules.md](package-boundaries-and-import-rules.md)
- [../class-design/index.md](../class-design/index.md)
- [../../architecture/index.md](../../architecture/index.md)

## Source of truth

This file is authoritative for the high-level repository layout and the main repository-structure design rule. Focused files in this folder own the detailed responsibilities for each area.

## Content

Original document metadata:

```text
Status: Draft v0.1
Project: Local-First Agentic Document GraphRAG System
Package name: personal_kb
Python version: 3.11
Package manager: uv
CLI framework: argparse
Primary runtime: local machine
Primary database: Neo4j
Primary storage: kb_storage/ processed JSON
```

The repository structure supports the agreed MVP architecture:

```text
User
-> LangGraph personal_kb agent
-> LangChain StructuredTools
-> KnowledgeToolService
-> RetrievalService / QAService / GraphService
-> Neo4j + kb_storage + local models
```

The repository must support:

1. deterministic local document ingestion;
2. manifest and per-document JSON storage;
3. local parsing, chunking, extraction, embedding, and reranking;
4. Neo4j graph schema setup and graph sync;
5. hybrid GraphRAG retrieval;
6. source-grounded Q&A;
7. LangGraph internal agent orchestration;
8. LangChain `StructuredTool` wrappers;
9. future MCP server adapter;
10. benchmark-driven validation.

The main rule is:

```text
core business logic must live in plain Python services, not inside CLI handlers, LangChain tools, LangGraph nodes, or MCP adapters.
```

Original high-level repository layout:

```text
personal-kb/
  README.md
  pyproject.toml
  uv.lock
  .python-version
  .env.example
  .gitignore

  configs/
    default.yaml
    local.example.yaml
    logging.yaml

  data/
    .gitkeep

  benchmark/
    README.md
    questions.example.jsonl
    expected_documents.example.jsonl

  kb_storage/
    .gitkeep

  docs/
    architecture/
      Technical_Architecture_Personal_KB_v0.3.md
      Product_Requirements_Document_Personal_KB_v0.2.md
      Neo4j_Graph_Schema_Personal_KB_v0.1.md
      Python_Class_Design_Personal_KB_v0.1.md
      MCP_Tool_Contracts_Personal_KB_v0.3.md
      Implementation_Roadmap_Personal_KB_v0.1.md
      Repository_Structure_Personal_KB_v0.1.md
    diagrams/
      README.md
      component_diagram.svg
      ingestion_activity.svg
      search_activity.svg
      ingestion_sequence.svg
      graph_schema.svg

  personal_kb/
    __init__.py
    __main__.py

    cli/
      __init__.py
      main.py
      commands/
        __init__.py
        setup_db.py
        ingest.py
        search.py
        ask.py
        related.py
        duplicates.py
        status.py
        evaluate.py
      formatters/
        __init__.py
        human.py
        json.py

    core/
      __init__.py
      config.py
      config_loader.py
      constants.py
      exceptions.py
      logging.py
      paths.py
      hashing.py
      normalization.py
      time.py
      ids.py

    schemas/
      __init__.py
      base.py
      config.py
      source.py
      document.py
      chunk.py
      entity.py
      tag.py
      manifest.py
      processing.py
      graph.py
      search.py
      qa.py
      tools.py
      evaluation.py
      errors.py

    storage/
      __init__.py
      manifest_store.py
      processed_document_store.py
      file_state_store.py
      storage_paths.py

    parsers/
      __init__.py
      base.py
      registry.py
      pdf_parser.py
      docx_parser.py
      markdown_parser.py
      text_parser.py
      xlsx_parser.py

    chunking/
      __init__.py
      base.py
      registry.py
      pdf_chunker.py
      docx_chunker.py
      markdown_chunker.py
      text_chunker.py
      xlsx_chunker.py

    models/
      __init__.py
      llm_client.py
      embedding_client.py
      reranker_client.py
      structured_extraction_client.py
      prompts/
        chunk_extraction.md
        document_summary.md
        qa_answer.md
        query_rewrite.md

    ingestion/
      __init__.py
      file_discovery.py
      ingestion_planner.py
      ingestion_service.py
      document_processor.py
      extraction_service.py
      embedding_service.py
      duplicate_service.py
      versioning_service.py

    graph/
      __init__.py
      neo4j_driver.py
      schema_manager.py
      graph_service.py
      graph_sync_service.py
      queries.py
      cypher/
        constraints.cypher
        indexes.cypher
        vector_index.cypher
        cleanup.cypher

    retrieval/
      __init__.py
      retrieval_service.py
      query_understanding.py
      search_plan_builder.py
      keyword_search.py
      entity_search.py
      tag_search.py
      vector_search.py
      graph_expansion.py
      scoring.py
      reranking.py

    qa/
      __init__.py
      qa_service.py
      context_builder.py
      answer_generator.py
      citation_builder.py
      answer_validator.py

    tools/
      __init__.py
      knowledge_tool_service.py
      structured_tools.py
      tool_registry.py
      tool_errors.py

    agent/
      __init__.py
      state.py
      graph.py
      nodes.py
      routing.py
      prompts.py

    adapters/
      __init__.py
      langchain/
        __init__.py
        structured_tools.py
      langgraph/
        __init__.py
        agent_factory.py
      mcp/
        __init__.py
        server.py
        schemas.py
        README.md
      api/
        __init__.py
        README.md

    evaluation/
      __init__.py
      benchmark_loader.py
      retrieval_metrics.py
      qa_metrics.py
      evaluator.py
      report_writer.py

    utils/
      __init__.py
      json.py
      text.py
      collections.py
      validation.py

  scripts/
    bootstrap_project.py
    run_ingestion.py
    run_evaluation.py
    export_graph_sample.py

  tests/
    __init__.py
    unit/
      test_hashing.py
      test_normalization.py
      test_manifest_store.py
      test_search_plan.py
      test_scoring.py
    integration/
      test_neo4j_schema.py
      test_graph_sync.py
      test_txt_md_ingestion.py
      test_search_documents.py
      test_answer_question.py
    fixtures/
      documents/
        sample.md
        sample.txt
      benchmark/
        questions.jsonl
      configs/
        test.yaml
```

Conflict / Review needed:

The original draft placed large versioned design documents under `docs/architecture/`. The current repository documentation strategy uses focused folders with `index.md` routers under `docs/architecture/`, `docs/implementation/`, `docs/roadmap/`, and related folders. Treat the package and runtime layout above as useful repository-structure guidance, but use the current focused docs indexes for documentation navigation.

Final recommendation:

```text
1. deterministic ingestion
2. processed JSON storage
3. Neo4j graph/vector retrieval
4. agent/tool orchestration
```

The most important design rule is:

```text
Business logic lives in services.
Framework-specific code lives in adapters.
Schemas are shared contracts.
Runtime data lives outside source code.
```

This allows the MVP to start with CLI + LangGraph tools and later add MCP, API, Telegram, or external connectors without rewriting the core system.

## Dependencies

- [package-boundaries-and-import-rules.md](package-boundaries-and-import-rules.md)
- [../class-design/index.md](../class-design/index.md)
- [../tool-contracts/index.md](../tool-contracts/index.md)
- [../../architecture/index.md](../../architecture/index.md)

## Failure modes / risks

- Business logic can drift into CLI handlers, LangChain tools, LangGraph nodes, or MCP adapters.
- Documentation navigation can conflict if old versioned files and focused documentation folders are both treated as authoritative.
- Runtime data can be accidentally committed if `data/` and `kb_storage/` rules are not enforced.

## Validation

- Confirm package directories follow the high-level layout or have a documented reason for divergence.
- Confirm implementation docs point to focused indexes, not old oversized Markdown files.
- Confirm `kb_storage/`, `data/`, and local config are excluded from Git except required placeholders.

## Update rules

Update this file when the repository-wide layout, MVP flow, package name, runtime assumptions, or main design rule changes.
