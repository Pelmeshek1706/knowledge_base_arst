from __future__ import annotations

import pytest
from pydantic import ValidationError

from personal_kb.core.config_loader import ConfigLoader
from personal_kb.schemas import (
    AnswerQuestionRequest,
    AnswerQuestionResponse,
    AppConfig,
    ChunkRecord,
    DocumentRecord,
    DocumentRelationship,
    EntityRecord,
    Manifest,
    ManifestDocumentEntry,
    ProcessingMetadata,
    ProcessedDocument,
    ProjectConfig,
    MatchedChunk,
    ScoreBreakdown,
    SearchDocumentResult,
    SearchDocumentsRequest,
    SearchDocumentsResponse,
    SearchFilters,
    SearchPlan,
    SourceDocumentRef,
    SourceRef,
    TagRecord,
)


def test_schema_payloads_validate_successfully() -> None:
    entity = EntityRecord(
        entity_id="",
        entity_key="",
        name="Penelope",
        normalized_name=" Penelope ",
        type="Person",
    )
    tag = TagRecord(tag_id="", name=" Budget  Review ", normalized_name="Budget Review")
    source_ref = SourceRef(file_path="data/budget.xlsx", sheet="Budget", cell_range="A1:F4")
    chunk = ChunkRecord(
        chunk_id="",
        document_id="doc-1",
        chunk_index=0,
        text="Budget planning",
        source_ref=source_ref,
        tags=[tag],
        entities=[entity],
    )
    document = DocumentRecord(
        document_id="doc-1",
        source_id="data/budget.xlsx",
        file_path="data/budget.xlsx",
        file_name="budget.xlsx",
        file_extension="xlsx",
        document_type="spreadsheet",
        title="Budget 2025",
        normalized_title="budget 2025",
        ingested_at="2026-05-09T12:00:00Z",
        raw_bytes_hash="raw-hash",
        extracted_text_hash="text-hash",
        content_hash="content-hash",
        tags=[tag],
        entities=[entity],
    )
    processed = ProcessedDocument(
        document=document,
        raw_text="Budget planning",
        chunks=[chunk],
        relationships=[
            DocumentRelationship(
                type="RELATED_TO",
                source_document_id="doc-1",
                target_document_id="doc-2",
                source="rule_based",
            )
        ],
        processing=ProcessingMetadata(
            parser="openpyxl",
            chunker="xlsx_chunker",
            processed_at="2026-05-09T12:05:00Z",
        ),
    )
    manifest = Manifest(
        documents=[
            ManifestDocumentEntry(
                document_id="doc-1",
                source_id="data/budget.xlsx",
                file_path="data/budget.xlsx",
                file_name="budget.xlsx",
                file_extension="xlsx",
                raw_bytes_hash="raw-hash",
                extracted_text_hash="text-hash",
                content_hash="content-hash",
                processed_json_path="kb_storage/documents/doc-1.json",
                status="processed",
            )
        ]
    )
    search_plan = SearchPlan(filters=SearchFilters(document_ids=["doc-1"]))
    search_request = SearchDocumentsRequest(query="budget", search_plan=search_plan)
    search_response = SearchDocumentsResponse(
        query="budget",
        search_plan_used=search_plan,
        search_mode=["keyword", "vector"],
        results=[
            SearchDocumentResult(
                document_id="doc-1",
                title="Budget 2025",
                file_path="data/budget.xlsx",
                document_type="spreadsheet",
                confidence=0.93,
                score_breakdown=ScoreBreakdown(final_score=0.93),
            )
        ],
    )
    answer_request = AnswerQuestionRequest(question="Where is the budget?")
    answer_response = AnswerQuestionResponse(
        question="Where is the budget?",
        answer="In the spreadsheet.",
        confidence=0.9,
        source_documents=[
            SourceDocumentRef(
                document_id="doc-1",
                title="Budget 2025",
                file_path="data/budget.xlsx",
                source_refs=[source_ref],
            )
        ],
        supporting_chunks=[
            MatchedChunk(
                chunk_id=chunk.chunk_id,
                source_ref=source_ref,
                text="Budget planning",
            )
        ],
    )
    app_config = AppConfig(project=ProjectConfig())

    assert document.document_type == "spreadsheet"
    assert processed.document.document_id == "doc-1"
    assert manifest.documents[0].status == "processed"
    assert search_request.query == "budget"
    assert search_response.search_plan_used == search_plan
    assert answer_request.top_k_chunks == 8
    assert answer_response.confidence == 0.9
    assert app_config.project.name == "personal_kb"
    assert app_config.models.llm.default_thinking_mode == "non_thinking"
    assert app_config.models.llm.allow_structured_output_reasoning_fallback is True
    assert (
        app_config.models.llm.model_name
        == "mlx-qwen3.5-9b-claude-4.6-opus-reasoning-distilled-v2"
    )
    assert app_config.models.extraction.model_name == "qwen2.5-1.5b-instruct"
    assert app_config.models.extraction.role == "extraction_default"


def test_invalid_schema_payloads_fail_clearly() -> None:
    with pytest.raises(ValidationError):
        SearchPlan(top_k=0)

    with pytest.raises(ValidationError):
        SearchDocumentsRequest(query="   ")

    with pytest.raises(ValidationError):
        ManifestDocumentEntry(
            document_id="doc-1",
            source_id="data/budget.xlsx",
            file_path="data/budget.xlsx",
            file_name="budget.xlsx",
            file_extension="xlsx",
            raw_bytes_hash="raw-hash",
            extracted_text_hash="text-hash",
            content_hash="content-hash",
            status="failed",
        )

    with pytest.raises(ValidationError):
        EntityRecord(
            entity_id="",
            entity_key="",
            name="Penelope",
            normalized_name="penelope",
            type="Person",
            confidence=1.5,
        )


def test_config_loader_parses_yaml_and_applies_env_overrides(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    config_path = config_dir / "default.yaml"
    config_path.write_text(
        """
project:
  name: personal_kb
  config_path: configs/default.yaml
storage:
  data_dir: data
  kb_storage_dir: kb_storage
  benchmark_dir: benchmark
neo4j:
  uri: bolt://localhost:7687
  username: neo4j
  password: change-me
  database: knowledge_base3
  fallback_database: neo4j
lm_studio:
  base_url: http://localhost:1234/v1
  model: mlx-community/Qwen3.5-9B-OptiQ-4bit
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("PERSONAL_KB_CONFIG", "configs/default.yaml")
    monkeypatch.setenv("NEO4J_URI", "bolt://example:7687")
    monkeypatch.setenv("NEO4J_USER", "tester")
    monkeypatch.setenv("LMSTUDIO_URL", "http://example:1234/v1")
    monkeypatch.setenv("LMSTUDIO_MODEL", "test-model")
    monkeypatch.setenv("LOCAL_EMBED_DIMENSIONS", "256")
    monkeypatch.setenv("PERSONAL_KB_SEARCH_DEFAULT_TOP_K", "5")
    monkeypatch.setenv("PERSONAL_KB_MODEL_LLM_DEFAULT_THINKING_MODE", "thinking")
    monkeypatch.setenv(
        "PERSONAL_KB_MODEL_LLM_ALLOW_STRUCTURED_OUTPUT_REASONING_FALLBACK",
        "false",
    )
    monkeypatch.setenv("PERSONAL_KB_MODEL_LLM_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv(
        "PERSONAL_KB_MODEL_EXTRACTION_MODEL_NAME",
        "qwen2.5-1.5b-instruct",
    )
    monkeypatch.setenv(
        "PERSONAL_KB_MODEL_EXTRACTION_BASE_URL",
        "http://example:1234/v1",
    )
    monkeypatch.setenv("PERSONAL_KB_MODEL_EXTRACTION_TIMEOUT_SECONDS", "8.5")

    config = ConfigLoader(project_root=tmp_path).load()

    assert config.project.config_path == "configs/default.yaml"
    assert config.neo4j.uri == "bolt://example:7687"
    assert config.neo4j.username == "tester"
    assert config.models.llm.base_url == "http://example:1234/v1"
    assert config.models.llm.model_name == "test-model"
    assert config.models.llm.default_thinking_mode == "thinking"
    assert config.models.llm.allow_structured_output_reasoning_fallback is False
    assert config.models.llm.timeout_seconds == 12.5
    assert config.models.extraction.base_url == "http://example:1234/v1"
    assert config.models.extraction.model_name == "qwen2.5-1.5b-instruct"
    assert config.models.extraction.timeout_seconds == 8.5
    assert config.models.embedding.dimension == 256
    assert config.search.default_top_k == 5
