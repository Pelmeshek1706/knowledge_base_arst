"""Ingestion package for personal_kb."""

from personal_kb.ingestion.document_aggregation_service import (
    DocumentAggregationService,
)
from personal_kb.ingestion.duplicate_detector import DuplicateDetector
from personal_kb.ingestion.embedding_service import EmbeddingService
from personal_kb.ingestion.extraction_service import ExtractionService
from personal_kb.ingestion.file_discovery import FileDiscoveryService
from personal_kb.ingestion.processing_planner import ProcessingPlanner

__all__ = [
    "DocumentAggregationService",
    "DuplicateDetector",
    "EmbeddingService",
    "ExtractionService",
    "FileDiscoveryService",
    "ProcessingPlanner",
]
