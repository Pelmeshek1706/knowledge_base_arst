from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from personal_kb.core.errors import IdError
from personal_kb.core.normalization import normalize_entity_name, normalize_tag_name

_DEFAULT_NAMESPACE = NAMESPACE_URL


def stable_uuid(*parts: str, namespace: UUID = _DEFAULT_NAMESPACE) -> str:
    """Generate a stable UUID5 from ordered string parts."""

    if not parts:
        raise IdError("at least one identifier part is required")
    key = "::".join(parts)
    return str(uuid5(namespace, key))


def new_uuid() -> str:
    """Generate a random UUID4 string."""

    return str(uuid4())


def make_document_id(source_id: str, raw_bytes_hash: str) -> str:
    """Generate a stable document UUID from the source and raw hash."""

    if not source_id or not raw_bytes_hash:
        raise IdError("source_id and raw_bytes_hash are required for document IDs")
    return stable_uuid("document", source_id, raw_bytes_hash)


def make_chunk_id(document_id: str, chunk_index: int) -> str:
    """Generate a stable chunk UUID from the parent document and chunk index."""

    if not document_id:
        raise IdError("document_id is required for chunk IDs")
    if chunk_index < 0:
        raise IdError("chunk_index must be >= 0")
    return stable_uuid("chunk", document_id, str(chunk_index))


def make_entity_key(entity_type: str, normalized_name: str) -> str:
    """Create the canonical entity key used in the graph."""

    normalized = normalize_entity_name(normalized_name)
    if not entity_type or not normalized:
        raise IdError("entity_type and normalized_name are required for entity keys")
    return f"{entity_type}::{normalized}"


def make_entity_id(entity_type: str, normalized_name: str) -> str:
    """Create the deterministic entity identifier used in the graph."""

    normalized = normalize_entity_name(normalized_name)
    if not entity_type or not normalized:
        raise IdError("entity_type and normalized_name are required for entity IDs")
    return f"entity::{entity_type}::{normalized}"


def make_tag_id(normalized_name: str) -> str:
    """Create the deterministic tag identifier used in the graph."""

    normalized = normalize_tag_name(normalized_name)
    if not normalized:
        raise IdError("normalized_name is required for tag IDs")
    return f"tag::{normalized}"
