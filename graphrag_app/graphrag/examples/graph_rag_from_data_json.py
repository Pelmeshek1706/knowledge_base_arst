from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from graphrag.config import Neo4jConfig
from graphrag.graph.graph_rag import GraphRag
from graphrag.storage.neo4j_client import Neo4jClient


# Run with:
#   PYTHONPATH=graphrag_app \
#   NEO4J_PASSWORD=your_password \
#   python -m graphrag.examples.graph_rag_from_data_json


def _stable_id(value: str, prefix: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:{digest}"


def _load_data(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    cfg = Neo4jConfig(
        uri=os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
        username=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password"),
    )

    client = Neo4jClient(cfg)
    client.connect()

    graph = GraphRag(client)
    graph.setup_graph_schema()

    data_path = Path("data/data.json")
    rows = _load_data(data_path)

    for row in rows:
        title = (row.get("title") or "").strip()
        file_path = (row.get("file_path") or "").strip()
        description = (row.get("description") or "").strip()
        keywords = row.get("keywords") or []

        if not file_path:
            continue

        doc_id = _stable_id(file_path, "doc")
        chunk_id = f"{doc_id}:chunk:0"

        graph.upsert_document(
            doc_id=doc_id,
            title=title or Path(file_path).name,
            source_type="local",
            source_id=file_path,
            file_path=file_path,
            description=description,
        )

        chunk_props = {chunk_id: {"text": description}}
        graph.upsert_chunk_nodes(doc_id, [chunk_id], chunk_props=chunk_props)
        graph.upsert_tags(chunk_id, keywords)

    client.close()


if __name__ == "__main__":
    main()
