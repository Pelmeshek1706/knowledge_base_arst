# LLM/RAG Evaluation Rubric

Use when task touches retrieval, QA, agents, model clients, extraction, prompts, structured outputs, or tool behavior.

## Metrics / Checks

- Faithfulness: answer uses only retrieved/allowed context.
- Relevance: answer addresses the user query.
- Citation correctness: citations point to supporting chunks/docs.
- JSON validity: structured output validates against schema.
- Fallback behavior: insufficient context produces safe refusal/fallback.
- Hallucination risk: model is not asked to invent missing data.
- Retrieval debugability: scores, document IDs, chunk IDs are inspectable.
- Determinism boundary: deterministic pipeline logic is not delegated to LLM unnecessarily.

## Recommended Future Benchmarks

- Recall@K
- Precision@K
- MRR
- nDCG
- Faithfulness score
- Citation correctness
- JSON validity rate
- Human review agreement
