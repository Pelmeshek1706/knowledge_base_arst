from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated, Any, Dict, List, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


@dataclass(frozen=True)
class SourceRef:
    title: str
    url: str


@dataclass(frozen=True)
class ToolTraceEntry:
    tool_name: str
    provider: str
    arguments: Dict[str, Any]
    output_preview: str


@dataclass(frozen=True)
class ResearchBudget:
    web_budget: int = 2
    deep_link_budget: int = 1


@dataclass(frozen=True)
class PlannerDecision:
    next_step: str
    reason: str = ""
    query: str = ""


@dataclass(frozen=True)
class CompletenessDecision:
    is_complete: bool
    reason: str = ""


class AgentPlanningMeta(TypedDict, total=False):
    next_step: str
    reason: str
    planned_calls: List[Dict[str, Any]]
    iterations: int


class AgentState(TypedDict, total=False):
    messages: Annotated[List[AnyMessage], add_messages]
    question: str
    route_hint: str
    tool_trace: List[ToolTraceEntry]
    sources: List[SourceRef]
    web_budget: int
    deep_link_budget: int
    final_answer: str
    planning_meta: AgentPlanningMeta
    context_snippets: List[str]
    processed_message_count: int
    fetched_urls: List[str]
    planned_calls: List[Dict[str, Any]]
    research_iterations: int


@dataclass
class StateGraphAgentResult:
    answer: str
    planned_calls: List[Dict[str, Any]] = field(default_factory=list)
    executed_results: List[ToolTraceEntry] = field(default_factory=list)
    context: str = ""
    planning_meta: Dict[str, Any] = field(default_factory=dict)
