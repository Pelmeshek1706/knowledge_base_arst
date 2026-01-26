from __future__ import annotations

import os

from graphrag.config import Neo4jConfig
from graphrag.graph.graph_rag import GraphRag
from graphrag.storage.neo4j_client import Neo4jClient
from graphrag.types.models import Entity, FAQEntry


# Run with:
#   PYTHONPATH=graphrag_app python -m graphrag.examples.graph_rag_usage

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

    # --- Document and chunks ---
    doc_id = "doc:readme"
    graph.upsert_document(
        doc_id=doc_id,
        title="README",
        source_type="local",
        source_id="README.md",
        url="file:///README.md",
    )

    chunk_ids = ["doc:readme:chunk:0", "doc:readme:chunk:1"]
    chunk_props = {
        chunk_ids[0]: {"text": "GraphRAG connects vector search with graph context."},
        chunk_ids[1]: {"text": "Neo4j stores nodes, edges, and embeddings."},
    }
    graph.upsert_chunk_nodes(doc_id, chunk_ids, chunk_props=chunk_props)

    graph.upsert_tags(chunk_ids[0], ["graph rag", "neo4j"])
    graph.upsert_entities(
        chunk_ids[0],
        [Entity(name="Neo4j", type="TECHNOLOGY"), Entity(name="GraphRAG", type="CONCEPT")],
    )

    graph.upsert_entity_relationships(
        [
            {
                "source": "Neo4j",
                "source_type": "TECHNOLOGY",
                "target": "GraphRAG",
                "target_type": "CONCEPT",
                "type": "RELATED_TO",
                "confidence": 0.72,
            }
        ]
    )

    # --- FAQ ---
    faq = FAQEntry(
        faq_id="faq:graphrag:1",
        question="What is GraphRAG?",
        answer="GraphRAG combines vector retrieval with graph traversal to enrich context.",
        chunk_ids=[chunk_ids[0]],
        tags=["graph rag"],
        entities=[Entity(name="GraphRAG", type="CONCEPT")],
    )
    graph.upsert_faq_node(faq)
    graph.link_faq(faq.faq_id, faq.chunk_ids, faq.tags, faq.entities)

    # --- Expansion ---
    context = graph.expand_from_seeds([chunk_ids[0]], hops=2, limit=50)
    print("Expanded nodes:", len(context["nodes"]))
    print("Expanded edges:", len(context["edges"]))
    print("Chunk excerpts:", context["chunks"])

    client.close()


if __name__ == "__main__":
    main()
