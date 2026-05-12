"""Ingestion package for personal_kb."""

from personal_kb.ingestion.duplicate_detector import DuplicateDetector
from personal_kb.ingestion.file_discovery import FileDiscoveryService
from personal_kb.ingestion.processing_planner import ProcessingPlanner

__all__ = [
    "DuplicateDetector",
    "FileDiscoveryService",
    "ProcessingPlanner",
]
