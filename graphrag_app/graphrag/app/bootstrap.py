from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

from graphrag.app.cli_commands import build_tool_registry, env_bool
from graphrag.config import Neo4jConfig
from graphrag.graph.graph_rag import GraphRag
from graphrag.llm import LangChainRuntime, LMStudioClient, LMStudioConfig
from graphrag.orchestrator import ToolOrchestratedAgent
from graphrag.storage.neo4j_client import Neo4jClient
from graphrag.tools import AgentToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class AppRuntime:
    client: Neo4jClient
    graph: GraphRag
    llm_ingest: LMStudioClient
    tool_registry: AgentToolRegistry
    web_search_tool: Optional[str]
    orchestrated_agent: ToolOrchestratedAgent


def print_banner(title: str, lines: list[str]) -> None:
    if not lines:
        logger.info(title)
        return
    width = max([len(title), *[len(line) for line in lines]])
    rule = "=" * width
    logger.info(rule)
    logger.info(title)
    for line in lines:
        logger.info(line)
    logger.info(rule)


def build_runtime() -> AppRuntime:
    neo4j_cfg = Neo4jConfig(
        uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        username=os.environ.get("NEO4J_USER", "neo4j"),
        password=os.environ.get("NEO4J_PASSWORD", "airestairest"),
    )

    lm_cfg = LMStudioConfig(
        base_url=os.environ.get("LMSTUDIO_URL", "http://localhost:1234"),
        model=os.environ.get("LMSTUDIO_MODEL", "qwen2.5-1.5b-instruct"),
        embedding_model=os.environ.get("LMSTUDIO_EMBED_MODEL"),
        embedding_fallback=env_bool("LMSTUDIO_EMBED_FALLBACK", True),
        local_embedding_dimensions=int(os.environ.get("LOCAL_EMBED_DIMENSIONS", "384")),
    )

    client = Neo4jClient(neo4j_cfg)
    client.connect()
    logger.info("Connected to Neo4j at %s", neo4j_cfg.uri)

    llm_ingest = LMStudioClient(lm_cfg)
    logger.info(
        "LM Studio: %s | chat_model=%s | embedding_model=%s | fallback=%s | local_dim=%s",
        lm_cfg.base_url,
        lm_cfg.model,
        lm_cfg.embedding_model or lm_cfg.model,
        lm_cfg.embedding_fallback,
        lm_cfg.local_embedding_dimensions,
    )

    graph = GraphRag(client)
    graph.allowed_relationship_types = {"RELATED_TO", "USES", "REQUIRES", "PART_OF"}

    tool_registry, web_search_tool = build_tool_registry(graph)

    planner_tools = ["graph_search"]
    if web_search_tool:
        planner_tools.append(web_search_tool)
    for spec in tool_registry.list_tools():
        name = spec.name.strip().lower()
        if name == "fetch_content" or name.endswith(".fetch_content"):
            planner_tools.append(spec.name)
    planner_tools = list(dict.fromkeys(planner_tools))

    langchain_runtime = LangChainRuntime.from_env()
    agent_model = langchain_runtime.build_chat_model()
    logger.info(
        "Agent runtime: %s model=%s base_url=%s",
        os.environ.get("AGENT_RUNTIME", "stategraph"),
        langchain_runtime.cfg.model,
        langchain_runtime.cfg.base_url or "<default>",
    )

    orchestrated_agent = ToolOrchestratedAgent(
        agent_model,
        tool_registry,
        max_tool_calls=int(os.environ.get("TOOL_AGENT_MAX_CALLS", "2")),
        context_max_chars=int(os.environ.get("TOOL_AGENT_CONTEXT_MAX_CHARS", "12000")),
        allowed_tools=planner_tools,
        max_deep_links=int(os.environ.get("AGENT_DEEP_LINK_BUDGET", os.environ.get("TOOL_AGENT_DEEP_LINKS", "1"))),
        max_research_iterations=int(os.environ.get("TOOL_AGENT_RESEARCH_ITERATIONS", "2")),
        legacy_llm=llm_ingest,
        web_budget=int(os.environ.get("AGENT_WEB_BUDGET", "2")),
    )

    return AppRuntime(
        client=client,
        graph=graph,
        llm_ingest=llm_ingest,
        tool_registry=tool_registry,
        web_search_tool=web_search_tool,
        orchestrated_agent=orchestrated_agent,
    )
