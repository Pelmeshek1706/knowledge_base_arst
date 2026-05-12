from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from personal_kb.core.errors import HashingError

_CHUNK_SIZE = 1024 * 1024


def compute_file_sha256(path: Path) -> str:
    """Compute a SHA-256 hash for a file's bytes."""

    digest = sha256()
    try:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(_CHUNK_SIZE)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError as exc:  # pragma: no cover - filesystem failure is defensive
        raise HashingError(f"failed to hash file bytes for {path}") from exc
    return digest.hexdigest()


def compute_text_sha256(text: str) -> str:
    """Compute a deterministic SHA-256 hash for text content."""

    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
    return sha256(normalized_text.encode("utf-8")).hexdigest()


def make_content_hash(raw_bytes_hash: str, extracted_text_hash: str | None) -> str:
    """Derive a content hash that prefers the raw-bytes hash for duplicates."""

    if not extracted_text_hash:
        return raw_bytes_hash
    digest = sha256()
    digest.update(raw_bytes_hash.encode("utf-8"))
    digest.update(b":")
    digest.update(extracted_text_hash.encode("utf-8"))
    return digest.hexdigest()


class HashingService:
    """Thin convenience wrapper around deterministic hashing helpers."""

    def hash_file_bytes(self, path: Path) -> str:
        return compute_file_sha256(path)

    def hash_text(self, text: str) -> str:
        return compute_text_sha256(text)

    def make_content_hash(
        self, raw_bytes_hash: str, extracted_text_hash: str | None
    ) -> str:
        return make_content_hash(raw_bytes_hash, extracted_text_hash)

