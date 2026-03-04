from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from pydantic import BaseModel, Field

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from graphrag.orchestrator.state import (
    AgentState,
    CompletenessDecision,
    PlannerDecision,
    SourceRef,
    StateGraphAgentResult,
    ToolTraceEntry,
)
from graphrag.tools import AgentToolRegistry
from graphrag.tools.langchain_tools import (
    build_langchain_tools,
    extract_urls,
    is_fetch_content_tool,
    is_web_search_tool,
)


class _CompletenessOutput(BaseModel):
    is_complete: bool = Field(..., description="Whether context is sufficient")
    reason: str = Field(default="", description="Short reason")


class _FollowupOutput(BaseModel):
    query: str = Field(..., min_length=1)


class StateGraphKnowledgeAgent:
    """StateGraph-based orchestrator for graph/web tool usage."""

    def __init__(
        self,
        model: BaseChatModel,
        tool_registry: AgentToolRegistry,
        *,
        max_tool_calls: int = 2,
        context_max_chars: int = 12000,
        allowed_tools: Optional[List[str]] = None,
        max_deep_links: int = 1,
        max_research_iterations: int = 2,
        web_budget: int = 2,
    ):
        self.model = model
        self.tool_registry = tool_registry
        self.max_tool_calls = max(1, int(max_tool_calls))
        self.context_max_chars = max(1000, int(context_max_chars))
        self.max_deep_links = max(0, int(max_deep_links))
        self.max_research_iterations = max(1, int(max_research_iterations))
        self.default_web_budget = max(0, int(web_budget))

        self.toolset = build_langchain_tools(tool_registry, allowed_tools=allowed_tools)
        self.tool_node = ToolNode(self.toolset.tools)
        self.model_with_tools = model.bind_tools(self.toolset.tools)

        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(AgentState)
        builder.add_node("plan_node", self._plan_node)
        builder.add_node("tool_node", self.tool_node)
        builder.add_node("research_gate_node", self._research_gate_node)
        builder.add_node("deep_fetch_node", self._deep_fetch_node)
        builder.add_node("followup_search_node", self._followup_search_node)
        builder.add_node("finalize_node", self._finalize_node)

        builder.add_edge(START, "plan_node")
        builder.add_conditional_edges(
            "plan_node",
            tools_condition,
            {
                "tools": "tool_node",
                "__end__": "research_gate_node",
            },
        )
        builder.add_edge("tool_node", "research_gate_node")
        builder.add_conditional_edges(
            "research_gate_node",
            self._route_after_gate,
            {
                "deep_fetch": "deep_fetch_node",
                "followup_search": "followup_search_node",
                "finalize": "finalize_node",
            },
        )
        builder.add_conditional_edges(
            "deep_fetch_node",
            self._route_after_generated_tool_call,
            {
                "tool_node": "tool_node",
                "research_gate_node": "research_gate_node",
            },
        )
        builder.add_conditional_edges(
            "followup_search_node",
            self._route_after_generated_tool_call,
            {
                "tool_node": "tool_node",
                "research_gate_node": "research_gate_node",
            },
        )
        builder.add_edge("finalize_node", END)
        return builder.compile()

    @staticmethod
    def _coerce_content_to_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: List[str] = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict):
                    text = block.get("text")
                    if isinstance(text, str):
                        parts.append(text)
            return "\n".join(parts)
        if isinstance(content, (dict, tuple)):
            try:
                return json.dumps(content, ensure_ascii=False)
            except Exception:
                return str(content)
        return str(content)

    @classmethod
    def _coerce_content_to_data(cls, content: Any) -> Dict[str, Any]:
        if isinstance(content, dict):
            return content
        text = cls._coerce_content_to_text(content).strip()
        if not text:
            return {"output": "", "preview": ""}
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
            return {"output": parsed, "preview": text}
        except Exception:
            return {"output": text, "preview": text}

    @staticmethod
    def _strip_think_blocks(text: str) -> str:
        if not text:
            return ""
        cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    @staticmethod
    def _question_terms(text: str) -> List[str]:
        tokens = re.findall(r"[a-zA-Zа-яА-ЯёЁіІїЇєЄ0-9]+", (text or "").lower())
        stop = {
            "the",
            "and",
            "or",
            "to",
            "in",
            "on",
            "for",
            "with",
            "what",
            "how",
            "which",
            "about",
            "что",
            "как",
            "или",
            "про",
            "для",
            "последние",
            "новости",
            "today",
            "latest",
            "news",
        }
        return [t for t in tokens if len(t) > 2 and t not in stop]

    def _render_context(self, question: str, tool_trace: List[ToolTraceEntry | Dict[str, Any]]) -> str:
        parts = [f"QUESTION:\n{question}\n"]
        for row in tool_trace:
            if isinstance(row, ToolTraceEntry):
                item = row
            else:
                item = ToolTraceEntry(
                    tool_name=str(row.get("tool_name", "")),
                    provider=str(row.get("provider", "")),
                    arguments=row.get("arguments") if isinstance(row.get("arguments"), dict) else {},
                    output_preview=str(row.get("output_preview", "")),
                )
            args_text = json.dumps(item.arguments, ensure_ascii=False)
            parts.append(f"TOOL: {item.tool_name} ({item.provider}) args={args_text}")
            parts.append(item.output_preview)
            parts.append("")
        merged = "\n".join(parts).strip()
        if len(merged) > self.context_max_chars:
            return merged[: self.context_max_chars - 3] + "..."
        return merged

    @staticmethod
    def _append_sources_if_missing(answer: str, sources: List[SourceRef]) -> str:
        text = (answer or "").strip()
        if not sources:
            return text
        if "http://" in text or "https://" in text:
            return text
        lines = [text, "", "Sources:"]
        for idx, source in enumerate(sources, start=1):
            lines.append(f"{idx}. {source.title} — {source.url}")
        return "\n".join(lines).strip()

    def _plan_node(self, state: AgentState) -> Dict[str, Any]:
        messages = list(state.get("messages") or [HumanMessage(content=state.get("question", ""))])
        ai = self.model_with_tools.invoke(messages)
        if not isinstance(ai, AIMessage):
            ai = AIMessage(content=self._coerce_content_to_text(getattr(ai, "content", ai)))

        raw_calls = list(getattr(ai, "tool_calls", []) or [])
        tool_calls = raw_calls[: self.max_tool_calls]
        if tool_calls != raw_calls:
            ai = AIMessage(content=ai.content, tool_calls=tool_calls)

        planned_rows = [
            {
                "tool_name": str(call.get("name", "") or "").strip(),
                "arguments": call.get("args") if isinstance(call.get("args"), dict) else {},
            }
            for call in tool_calls
        ]
        planned_calls = list(state.get("planned_calls") or []) + planned_rows

        return {
            "messages": [ai],
            "planned_calls": planned_calls,
            "planning_meta": {
                "next_step": "tools" if tool_calls else "research_gate",
                "reason": "initial_plan",
                "planned_calls": planned_rows,
            },
        }

    def _trace_from_tool_messages(self, state: AgentState) -> Dict[str, Any]:
        messages = list(state.get("messages") or [])
        processed_count = int(state.get("processed_message_count", 0) or 0)
        tool_trace: List[ToolTraceEntry] = []
        for item in state.get("tool_trace") or []:
            if isinstance(item, ToolTraceEntry):
                tool_trace.append(item)
            elif isinstance(item, dict):
                tool_trace.append(
                    ToolTraceEntry(
                        tool_name=str(item.get("tool_name", "")),
                        provider=str(item.get("provider", "")),
                        arguments=item.get("arguments") if isinstance(item.get("arguments"), dict) else {},
                        output_preview=str(item.get("output_preview", "")),
                    )
                )

        sources: List[SourceRef] = []
        for item in state.get("sources") or []:
            if isinstance(item, SourceRef):
                sources.append(item)
            elif isinstance(item, dict):
                url = str(item.get("url", "")).strip()
                if not url:
                    continue
                sources.append(SourceRef(title=str(item.get("title", "")).strip() or url, url=url))
        fetched_urls = set(state.get("fetched_urls") or [])

        seen_source_urls = {item.url for item in sources}
        for msg in messages[processed_count:]:
            if not isinstance(msg, ToolMessage):
                continue
            data = self._coerce_content_to_data(msg.content)
            tool_name = str(data.get("tool") or getattr(msg, "name", "") or "tool")
            provider = str(data.get("provider") or "")
            arguments = data.get("arguments") if isinstance(data.get("arguments"), dict) else {}
            preview = str(data.get("preview") or self._coerce_content_to_text(data.get("output") or ""))
            trace_row = ToolTraceEntry(
                tool_name=tool_name,
                provider=provider,
                arguments=arguments,
                output_preview=preview,
            )
            tool_trace.append(trace_row)

            output = data.get("output")
            urls = data.get("urls") if isinstance(data.get("urls"), list) else extract_urls(output)
            for raw_url in urls:
                url = str(raw_url).strip()
                if not url or url in seen_source_urls:
                    continue
                seen_source_urls.add(url)
                title = str(data.get("tool") or tool_name)
                sources.append(SourceRef(title=title, url=url))

            if tool_name == "fetch_content":
                url = str(arguments.get("url", "")).strip()
                if url:
                    fetched_urls.add(url)

        return {
            "tool_trace": tool_trace,
            "sources": sources,
            "processed_message_count": len(messages),
            "fetched_urls": sorted(fetched_urls),
        }

    def _validate_completeness(self, question: str, tool_trace: List[ToolTraceEntry]) -> CompletenessDecision:
        if not tool_trace:
            return CompletenessDecision(is_complete=False, reason="no_tool_context")

        context = self._render_context(question, tool_trace)
        prompt = (
            "Decide if tool context is sufficient to answer the user question.\n"
            "Respond with JSON: {\"is_complete\": true|false, \"reason\": \"...\"}.\n"
            "Mark false if critical facts are missing.\n\n"
            f"Question:\n{question}\n\n"
            f"Tool context:\n{context[:5000]}\n"
        )
        try:
            structured_model = self.model.with_structured_output(_CompletenessOutput)
            out = structured_model.invoke([HumanMessage(content=prompt)])
            if isinstance(out, _CompletenessOutput):
                return CompletenessDecision(is_complete=bool(out.is_complete), reason=str(out.reason))
            if isinstance(out, dict):
                return CompletenessDecision(
                    is_complete=bool(out.get("is_complete", False)),
                    reason=str(out.get("reason", "")),
                )
        except Exception:
            pass

        has_graph = any(row.tool_name == "graph_search" for row in tool_trace)
        has_web = any(row.tool_name == "web_search" for row in tool_trace)
        return CompletenessDecision(is_complete=has_graph and has_web, reason="heuristic")

    def _plan_followup_query(self, question: str, tool_trace: List[ToolTraceEntry]) -> str:
        context = self._render_context(question, tool_trace)
        prompt = (
            "Generate ONE follow-up web search query for missing information.\n"
            "Return JSON: {\"query\": \"...\"}.\n"
            "Keep the query close to the original question and prefer current-events wording when relevant.\n\n"
            f"Question:\n{question}\n\n"
            f"Current context:\n{context[:4000]}\n"
        )
        try:
            structured_model = self.model.with_structured_output(_FollowupOutput)
            out = structured_model.invoke([HumanMessage(content=prompt)])
            if isinstance(out, _FollowupOutput):
                q = out.query.strip()
                if q:
                    return q
            if isinstance(out, dict):
                q = str(out.get("query", "")).strip()
                if q:
                    return q
        except Exception:
            pass
        return question

    def _research_gate_node(self, state: AgentState) -> Dict[str, Any]:
        updates = self._trace_from_tool_messages(state)
        tool_trace: List[ToolTraceEntry] = updates["tool_trace"]
        sources: List[SourceRef] = updates["sources"]
        fetched_urls: List[str] = updates["fetched_urls"]

        question = str(state.get("question", ""))
        web_budget = int(state.get("web_budget", self.default_web_budget))
        deep_budget = int(state.get("deep_link_budget", self.max_deep_links))
        iterations = int(state.get("research_iterations", 0)) + 1

        next_decision = PlannerDecision(next_step="finalize", reason="default")

        has_web = any(
            item.tool_name == "web_search" or is_web_search_tool(item.tool_name)
            for item in tool_trace
        )
        has_fetch = any(
            item.tool_name == "fetch_content" or is_fetch_content_tool(item.tool_name)
            for item in tool_trace
        )

        if not tool_trace:
            if self.toolset.web_tool and web_budget > 0:
                next_decision = PlannerDecision(next_step="followup_search", reason="no_tool_output")
            else:
                next_decision = PlannerDecision(next_step="finalize", reason="no_tools_available")
        elif iterations > self.max_research_iterations:
            next_decision = PlannerDecision(next_step="finalize", reason="max_iterations_reached")
        elif has_web and not has_fetch and self.toolset.fetch_tool and deep_budget > 0:
            pending_urls = [src.url for src in sources if src.url not in set(fetched_urls)]
            if pending_urls:
                next_decision = PlannerDecision(next_step="deep_fetch", reason="search_needs_depth")
        else:
            completeness = self._validate_completeness(question, tool_trace)
            if not completeness.is_complete and self.toolset.web_tool and web_budget > 0:
                next_decision = PlannerDecision(next_step="followup_search", reason=completeness.reason)
            else:
                next_decision = PlannerDecision(next_step="finalize", reason=completeness.reason or "complete")

        return {
            **updates,
            "research_iterations": iterations,
            "planning_meta": {
                "next_step": next_decision.next_step,
                "reason": next_decision.reason,
                "iterations": iterations,
            },
        }

    @staticmethod
    def _tool_call(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "name": name,
            "args": args,
            "id": f"call_{uuid.uuid4().hex[:10]}",
            "type": "tool_call",
        }

    def _deep_fetch_node(self, state: AgentState) -> Dict[str, Any]:
        deep_budget = int(state.get("deep_link_budget", self.max_deep_links))
        if deep_budget <= 0 or not self.toolset.fetch_tool:
            return {
                "planning_meta": {
                    "next_step": "followup_search" if int(state.get("web_budget", self.default_web_budget)) > 0 else "finalize",
                    "reason": "no_deep_fetch_budget",
                }
            }

        fetched = set(state.get("fetched_urls") or [])
        candidate_urls = []
        for item in state.get("sources") or []:
            url = item.url if isinstance(item, SourceRef) else str(item.get("url", "")).strip()
            if not url or url in fetched:
                continue
            candidate_urls.append(url)

        if not candidate_urls:
            return {
                "planning_meta": {
                    "next_step": "followup_search" if int(state.get("web_budget", self.default_web_budget)) > 0 else "finalize",
                    "reason": "no_new_urls",
                }
            }

        urls = candidate_urls[:deep_budget]
        tool_calls = [self._tool_call("fetch_content", {"url": url}) for url in urls]
        message = AIMessage(content="Fetching full content for selected sources.", tool_calls=tool_calls)

        planned_calls = list(state.get("planned_calls") or [])
        planned_calls.extend({"tool_name": "fetch_content", "arguments": {"url": url}} for url in urls)

        return {
            "messages": [message],
            "deep_link_budget": max(0, deep_budget - len(urls)),
            "planned_calls": planned_calls,
            "planning_meta": {
                "next_step": "tools",
                "reason": "deep_fetch_urls",
                "planned_calls": [{"tool_name": "fetch_content", "arguments": {"url": u}} for u in urls],
            },
        }

    def _followup_search_node(self, state: AgentState) -> Dict[str, Any]:
        web_budget = int(state.get("web_budget", self.default_web_budget))
        if web_budget <= 0 or not self.toolset.web_tool:
            return {
                "planning_meta": {
                    "next_step": "finalize",
                    "reason": "no_web_budget",
                }
            }

        question = str(state.get("question", ""))
        tool_trace = list(state.get("tool_trace") or [])
        query = self._plan_followup_query(question, tool_trace)

        message = AIMessage(
            content="Running a follow-up web search for missing details.",
            tool_calls=[self._tool_call("web_search", {"query": query, "max_results": 8})],
        )

        planned_calls = list(state.get("planned_calls") or [])
        planned_calls.append({"tool_name": "web_search", "arguments": {"query": query, "max_results": 8}})

        return {
            "messages": [message],
            "web_budget": max(0, web_budget - 1),
            "planned_calls": planned_calls,
            "planning_meta": {
                "next_step": "tools",
                "reason": "followup_search",
                "planned_calls": [{"tool_name": "web_search", "arguments": {"query": query, "max_results": 8}}],
            },
        }

    @staticmethod
    def _route_after_gate(state: AgentState) -> str:
        planning_meta = state.get("planning_meta") or {}
        step = str(planning_meta.get("next_step") or "finalize")
        if step not in {"deep_fetch", "followup_search", "finalize"}:
            return "finalize"
        return step

    @staticmethod
    def _route_after_generated_tool_call(state: AgentState) -> str:
        messages = list(state.get("messages") or [])
        if not messages:
            return "research_gate_node"
        last = messages[-1]
        if isinstance(last, AIMessage) and list(getattr(last, "tool_calls", []) or []):
            return "tool_node"
        return "research_gate_node"

    def _finalize_node(self, state: AgentState) -> Dict[str, Any]:
        question = str(state.get("question", ""))
        tool_trace = list(state.get("tool_trace") or [])
        sources: List[SourceRef] = []
        for item in state.get("sources") or []:
            if isinstance(item, SourceRef):
                sources.append(item)
            elif isinstance(item, dict):
                url = str(item.get("url", "")).strip()
                if url:
                    title = str(item.get("title", "")).strip() or url
                    sources.append(SourceRef(title=title, url=url))
        context = self._render_context(question, tool_trace)

        system_prompt = (
            "You are a technical assistant.\n"
            "Use only the provided tool context and do not invent facts.\n"
            "If context is insufficient, explicitly state what is missing.\n"
            "Answer in the same language as the user question.\n"
        )
        prompt = (
            f"Tool context:\n{context}\n\n"
            f"Question:\n{question}\n\n"
            "Provide the final answer."
        )
        response = self.model.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt),
            ]
        )
        answer = self._coerce_content_to_text(getattr(response, "content", response))
        answer = self._strip_think_blocks(answer)
        answer = self._append_sources_if_missing(answer, sources)

        return {
            "final_answer": answer,
            "context_snippets": [context],
            "planning_meta": {
                **(state.get("planning_meta") or {}),
                "next_step": "finalize",
            },
        }

    def answer(self, question: str) -> StateGraphAgentResult:
        initial_state: AgentState = {
            "question": question,
            "messages": [HumanMessage(content=question)],
            "tool_trace": [],
            "sources": [],
            "web_budget": self.default_web_budget,
            "deep_link_budget": self.max_deep_links,
            "planning_meta": {"next_step": "plan", "reason": "start", "planned_calls": []},
            "context_snippets": [],
            "processed_message_count": 0,
            "fetched_urls": [],
            "planned_calls": [],
            "research_iterations": 0,
        }
        out = self.graph.invoke(initial_state)

        tool_trace = list(out.get("tool_trace") or [])
        if tool_trace and isinstance(tool_trace[0], dict):
            normalized_trace = [ToolTraceEntry(**item) for item in tool_trace]
        else:
            normalized_trace = tool_trace

        context_snippets = out.get("context_snippets") or []
        context = context_snippets[0] if context_snippets else ""

        return StateGraphAgentResult(
            answer=str(out.get("final_answer") or ""),
            planned_calls=list(out.get("planned_calls") or []),
            executed_results=normalized_trace,
            context=context,
            planning_meta=dict(out.get("planning_meta") or {}),
        )

    def invoke(self, payload: str | Dict[str, Any]) -> Dict[str, Any]:
        question = payload if isinstance(payload, str) else str(payload.get("question", "")).strip()
        result = self.answer(question)
        return {
            "answer": result.answer,
            "planned_calls": result.planned_calls,
            "executed_results": [asdict(item) for item in result.executed_results],
            "context": result.context,
            "planning_meta": result.planning_meta,
        }
