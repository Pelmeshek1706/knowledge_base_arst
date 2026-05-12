# Architecture Map

Runtime flow:

```text
User
→ LangGraph personal_kb agent
→ LangChain StructuredTools
→ KnowledgeToolService
→ RetrievalService / QAService / GraphService
→ Neo4j + kb_storage + local models
```

Forbidden MVP changes:

- Do not make MCP the primary internal path.
- Do not let runtime agent control ingestion.
- Do not place business logic in tools.
- Do not treat Neo4j as primary document storage.
- Do not bypass KnowledgeToolService from tools.
