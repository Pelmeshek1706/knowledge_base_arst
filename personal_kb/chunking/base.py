from __future__ import annotations

from abc import ABC, abstractmethod

from personal_kb.schemas.chunk import ChunkRecord
from personal_kb.schemas.document import ParsedDocument


class BaseChunker(ABC):
    """Base contract for deterministic document chunkers."""

    supported_extensions: tuple[str, ...] = ()

    @abstractmethod
    def chunk(self, document: ParsedDocument, *, document_id: str) -> list[ChunkRecord]:
        """Chunk a parsed document for retrieval."""
