from __future__ import annotations

from pathlib import Path
from typing import Literal

from personal_kb.core.errors import PathTraversalError

PathMode = Literal["relative", "absolute"]


class PathResolver:
    """Resolve project-relative paths and block traversal outside the root."""

    def __init__(self, project_root: Path, path_mode: PathMode = "relative") -> None:
        self.project_root = project_root.resolve()
        self.path_mode = path_mode

    def resolve_project_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.project_root / candidate
        resolved = candidate.resolve(strict=False)
        self._ensure_within_project_root(resolved)
        return resolved

    def to_storage_path(self, path: str | Path) -> str:
        resolved = self.resolve_project_path(path)
        if self.path_mode == "absolute":
            return resolved.as_posix()
        return resolved.relative_to(self.project_root).as_posix()

    def resolve_documents_dir(self, directory_name: str = "data") -> Path:
        return self.resolve_project_path(directory_name)

    def resolve_storage_dir(self, directory_name: str = "kb_storage") -> Path:
        return self.resolve_project_path(directory_name)

    def resolve_benchmark_dir(self, directory_name: str = "benchmark") -> Path:
        return self.resolve_project_path(directory_name)

    def _ensure_within_project_root(self, path: Path) -> None:
        try:
            path.relative_to(self.project_root)
        except ValueError as exc:
            raise PathTraversalError(path, self.project_root) from exc


def ensure_project_relative_path(
    project_root: Path, path: str | Path, path_mode: PathMode = "relative"
) -> str:
    """Convert a path to a project-relative storage path."""

    return PathResolver(project_root=project_root, path_mode=path_mode).to_storage_path(
        path
    )
