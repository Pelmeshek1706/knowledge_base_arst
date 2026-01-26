How to run
1) Run Neo4j
<bash>
docker run \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/<password> \
  neo4j:5
</bash>

2) Configure environment
- Create `.env` in the project root (see example in `.env`).
- Update `NEO4J_PASSWORD` and optionally `LMSTUDIO_URL`, `LMSTUDIO_MODEL`.
- (Optional) set `DATA_JSON` to your data file path.

3) Start LM Studio
- Run the local server (default `http://localhost:1234`).
- Ensure the model name matches `LMSTUDIO_MODEL`.

4) Run the GraphRAG demo script
<bash>
python3 graphrag_app/demo_agent_on_data_json.py
</bash>

What the script does (short)
- Loads documents from `data/data.json` (or `DATA_JSON`).
- Creates `Document`, `Chunk`, `Entity`, `Tag` nodes and relationships in Neo4j.
- Uses LM Studio to extract entities/relationships/tags from each document chunk.
- Starts an interactive Q&A loop using graph retrieval + LM Studio generation.

Interactive commands
- `help` / `?`          Show commands
- `stats`              Show graph stats
- `docs <topic>`       Find documents by topic
- `entity <name>`      Show entity context
- `find <e1> <e2>`      Find path between entities
- `clear`              Clear chat history (stateless in this demo)
- `exit` / `quit`       Exit the session
