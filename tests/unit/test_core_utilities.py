from __future__ import annotations

from datetime import UTC, datetime

import pytest

from personal_kb.core.errors import PathTraversalError
from personal_kb.core.hashing import compute_file_sha256, compute_text_sha256, make_content_hash
from personal_kb.core.ids import make_chunk_id, make_document_id, make_entity_id, make_entity_key, make_tag_id, stable_uuid
from personal_kb.core.normalization import normalize_entity_name, normalize_label, normalize_tag_name
from personal_kb.core.paths import PathResolver
from personal_kb.core.time import parse_utc_datetime, to_utc_datetime, to_utc_iso, utc_now_iso


def test_path_resolver_blocks_traversal_and_returns_relative_paths(tmp_path) -> None:
    resolver = PathResolver(project_root=tmp_path)
    inside = tmp_path / "data" / "budget.xlsx"
    inside.parent.mkdir()
    inside.write_text("x", encoding="utf-8")

    assert resolver.to_storage_path(inside) == "data/budget.xlsx"
    assert resolver.resolve_documents_dir() == tmp_path / "data"
    assert resolver.resolve_storage_dir() == tmp_path / "kb_storage"

    with pytest.raises(PathTraversalError):
        resolver.to_storage_path(tmp_path.parent / "outside.txt")


def test_hashing_helpers_are_deterministic(tmp_path) -> None:
    path = tmp_path / "sample.txt"
    path.write_text("hello", encoding="utf-8")

    raw_hash = compute_file_sha256(path)
    assert raw_hash == compute_file_sha256(path)
    assert compute_text_sha256("hello\r\nworld") == compute_text_sha256("hello\nworld")
    assert make_content_hash(raw_hash, None) == raw_hash
    assert make_content_hash(raw_hash, "abc") != raw_hash


def test_normalization_helpers_collapse_whitespace_and_lowercase() -> None:
    assert normalize_label("  Hello   World  ") == "hello world"
    assert normalize_entity_name("  Penelope ") == "penelope"
    assert normalize_tag_name("Budget   Review") == "budget review"


def test_identifier_helpers_are_stable() -> None:
    first = stable_uuid("document", "source", "hash")
    second = stable_uuid("document", "source", "hash")

    assert first == second
    assert make_document_id("source", "hash") == make_document_id("source", "hash")
    assert make_chunk_id("doc-id", 0) == make_chunk_id("doc-id", 0)
    assert make_entity_key("Person", "penelope") == "Person::penelope"
    assert make_entity_id("Person", "Penelope") == "entity::Person::penelope"
    assert make_tag_id("Budget Review") == "tag::budget review"


def test_time_helpers_use_utc() -> None:
    now_iso = utc_now_iso()
    parsed = parse_utc_datetime(now_iso)

    assert parsed.tzinfo == UTC
    assert to_utc_iso(parsed).endswith("Z")
    assert to_utc_datetime(datetime(2026, 1, 1, 12, 0, 0)).tzinfo == UTC

