from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

try:
    from langsmith import traceable
except Exception:  # pragma: no cover - optional dependency
    def traceable(*decorator_args: Any, **decorator_kwargs: Any):  # type: ignore[no-redef]
        if (
            decorator_args
            and callable(decorator_args[0])
            and len(decorator_args) == 1
            and not decorator_kwargs
        ):
            return decorator_args[0]

        def _decorator(func: Any) -> Any:
            return func

        return _decorator

from graphrag.llm.base import expect_json_object
from graphrag.llm.lm_studio import LMStudioClient
from graphrag.tools import AgentToolRegistry, ToolCallResult, ToolExecutionError


@dataclass(frozen=True)
class PlannedToolCall:
    tool_name: str
    arguments: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolAgentResult:
    answer: str
    planned_calls: List[PlannedToolCall]
    executed_results: List[ToolCallResult]
    context: str
    planning_raw: str = ""


def _trace_process_inputs(inputs: Any) -> Any:
    if isinstance(inputs, dict):
        return {k: v for k, v in inputs.items() if k != "self"}
    return inputs


def _preview_value(value: Any, *, max_chars: int = 1200) -> str:
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    if len(text) > max_chars:
        return text[: max_chars - 3] + "..."
    return text


def _trace_process_plan_output(output: Any) -> Any:
    if not (isinstance(output, tuple) and len(output) == 2):
        return output
    calls_raw, planning_raw = output
    calls: List[Dict[str, Any]] = []
    if isinstance(calls_raw, list):
        for item in calls_raw:
            tool_name = str(getattr(item, "tool_name", "")).strip()
            arguments = getattr(item, "arguments", {})
            if not tool_name:
                continue
            calls.append(
                {
                    "tool_name": tool_name,
                    "arguments": arguments if isinstance(arguments, dict) else {},
                }
            )
    return {
        "calls": calls,
        "planning_raw_preview": _preview_value(planning_raw, max_chars=600),
    }


def _trace_process_tool_call_output(output: Any) -> Any:
    if isinstance(output, ToolCallResult):
        return {
            "tool_name": output.tool_name,
            "provider": output.provider,
            "arguments": output.arguments,
            "output_preview": _preview_value(output.output, max_chars=900),
        }
    return output


def _trace_process_text_output(output: Any) -> Any:
    if isinstance(output, str):
        return _preview_value(output, max_chars=1500)
    return output


def _trace_process_agent_output(output: Any) -> Any:
    if isinstance(output, ToolAgentResult):
        return {
            "answer_preview": _preview_value(output.answer, max_chars=900),
            "planned_calls": [
                {"tool_name": item.tool_name, "arguments": item.arguments}
                for item in output.planned_calls
            ],
            "executed_calls": [
                {
                    "tool_name": item.tool_name,
                    "provider": item.provider,
                    "arguments": item.arguments,
                }
                for item in output.executed_results
            ],
            "context_preview": _preview_value(output.context, max_chars=1200),
        }
    return output


class ToolOrchestratedAgent:
    """
    Agent that decides which tools to call, executes them, then composes final answer.
    """

    def __init__(
        self,
        llm: LMStudioClient,
        tool_registry: AgentToolRegistry,
        *,
        max_tool_calls: int = 2,
        context_max_chars: int = 12000,
        allowed_tools: List[str] | None = None,
        max_deep_links: int = 1,
        max_research_iterations: int = 2,
    ):
        self.llm = llm
        self.tool_registry = tool_registry
        self.max_tool_calls = max(1, int(max_tool_calls))
        self.context_max_chars = max(1000, int(context_max_chars))
        self.allowed_tools = {t.strip() for t in (allowed_tools or []) if t and t.strip()}
        self.max_deep_links = max(0, int(max_deep_links))
        self.max_research_iterations = max(1, int(max_research_iterations))

    def _is_allowed_tool(self, name: str) -> bool:
        if not self.allowed_tools:
            return True
        return name in self.allowed_tools

    def _tool_manifest(self) -> List[Dict[str, Any]]:
        specs = self.tool_registry.list_tools(refresh=True)
        manifest: List[Dict[str, Any]] = []
        for spec in specs:
            if not self._is_allowed_tool(spec.name):
                continue
            usage_hint = ""
            if spec.name == "graph_search":
                usage_hint = (
                    "Local project knowledge only. Not suitable for latest news, today's events, "
                    "live weather, prices, or other real-time internet questions."
                )
            elif self._is_web_search_tool(spec.name):
                usage_hint = (
                    "Internet search. Use for latest/current/today/news/weather/public web info."
                )
            manifest.append(
                {
                    "name": spec.name,
                    "description": spec.description,
                    "input_schema": spec.input_schema,
                    "usage_hint": usage_hint,
                }
            )
        return manifest

    @staticmethod
    def _is_web_search_tool(name: str) -> bool:
        n = (name or "").strip().lower()
        if not n:
            return False
        if n == "graph_search":
            return False
        return n == "search" or n.endswith(".search") or ("duckduckgo" in n and "search" in n)

    @staticmethod
    def _extract_json_object_loose(raw: str) -> Optional[Dict[str, Any]]:
        text = (raw or "").strip()
        if not text:
            return None

        try:
            obj = expect_json_object(text)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

        fenced = re.findall(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, flags=re.IGNORECASE)
        for candidate in fenced:
            try:
                parsed = json.loads(candidate)
            except Exception:
                continue
            if isinstance(parsed, dict):
                return parsed

        decoder = json.JSONDecoder()
        for idx, ch in enumerate(text):
            if ch != "{":
                continue
            try:
                parsed, end = decoder.raw_decode(text[idx:])
            except Exception:
                continue
            if isinstance(parsed, dict) and end > 0:
                return parsed
        return None

    def _fallback_plan(self, question: str) -> List[PlannedToolCall]:
        tools = [t for t in self.tool_registry.list_tools(refresh=False) if self._is_allowed_tool(t.name)]
        if not tools:
            return []

        graph_name = self.tool_registry.resolve_tool_name("graph_search")
        web_name = None
        for spec in tools:
            if self._is_web_search_tool(spec.name):
                web_name = spec.name
                break

        planned: List[PlannedToolCall] = []
        if web_name:
            planned.append(
                PlannedToolCall(
                    tool_name=web_name,
                    arguments={"query": question, "max_results": 8},
                )
            )
        if graph_name and self._is_allowed_tool(graph_name):
            planned.append(
                PlannedToolCall(
                    tool_name=graph_name,
                    arguments={"query": question, "limit": 12},
                )
            )
        if planned:
            return planned[: self.max_tool_calls]
        return [PlannedToolCall(tool_name=tools[0].name, arguments={"query": question})]

    @traceable(
        run_type="chain",
        name="tool_agent.plan",
        process_inputs=_trace_process_inputs,
        process_outputs=_trace_process_plan_output,
    )
    def _plan_tool_calls(self, question: str) -> tuple[List[PlannedToolCall], str]:
        tool_manifest = self._tool_manifest()
        if not tool_manifest:
            return [], ""

        planner_prompt = (
            "You are a tool-selection planner for a QA agent.\n"
            "Pick the best tool or tools to answer the user question.\n"
            "Use local graph search for project knowledge and web search for current/public internet info.\n"
            "Decision rules:\n"
            "- Use web search for latest/current/today/news/weather/public events.\n"
            "- Use graph_search for local project/domain knowledge stored in Neo4j.\n"
            "- If uncertain, call both tools.\n"
            "Return STRICT JSON only with shape:\n"
            "{\n"
            '  "calls": [\n'
            '    {"tool": "<tool_name>", "arguments": {"...": "..."}}\n'
            "  ]\n"
            "}\n"
            f"Use at most {self.max_tool_calls} calls.\n\n"
            f"Available tools:\n{json.dumps(tool_manifest, ensure_ascii=False, indent=2)}\n\n"
            f"User question:\n{question}\n"
        )
        raw = self.llm.chat([{"role": "user", "content": planner_prompt}], temperature=0.1, max_tokens=700)

        obj = self._extract_json_object_loose(raw)
        if not obj:
            return self._fallback_plan(question), raw

        rows = obj.get("calls", [])
        if not isinstance(rows, list):
            return self._fallback_plan(question), raw

        planned: List[PlannedToolCall] = []
        for row in rows[: self.max_tool_calls]:
            if not isinstance(row, dict):
                continue
            name = str(row.get("tool", "")).strip()
            if not name:
                continue
            resolved = self.tool_registry.resolve_tool_name(name) or name
            if not self._is_allowed_tool(resolved):
                continue
            args = row.get("arguments", {})
            if not isinstance(args, dict):
                args = {}
            planned.append(PlannedToolCall(tool_name=resolved, arguments=args))

        if planned:
            return planned, raw
        return self._fallback_plan(question), raw

    def _resolve_web_tool_name(self) -> str | None:
        specs = self.tool_registry.list_tools(refresh=False)
        for spec in specs:
            if not self._is_allowed_tool(spec.name):
                continue
            if self._is_web_search_tool(spec.name):
                return spec.name
        return None

    @staticmethod
    def _is_fetch_content_tool(name: str) -> bool:
        n = (name or "").strip().lower()
        return n == "fetch_content" or n.endswith(".fetch_content")

    def _resolve_fetch_content_tool_name(self) -> str | None:
        specs = self.tool_registry.list_tools(refresh=False)
        for spec in specs:
            if self._is_fetch_content_tool(spec.name):
                return spec.name
        return None

    @staticmethod
    def _is_empty_tool_output(output: Any) -> bool:
        if output is None:
            return True
        if isinstance(output, str):
            text = output.strip()
            if not text:
                return True
            lowered = text.lower()
            if "found 0 search results" in lowered:
                return True
            return False
        if isinstance(output, (list, dict, tuple, set)):
            return len(output) == 0
        return False

    def _should_retry_with_web(self, executed: List[ToolCallResult]) -> bool:
        if not executed:
            return True
        if any(self._is_web_search_tool(item.tool_name) for item in executed):
            return False
        return all(self._is_empty_tool_output(item.output) for item in executed)

    @staticmethod
    def _extract_urls_from_text(text: str) -> List[str]:
        if not text:
            return []
        matches = re.findall(r"https?://[^\s<>\]\"')]+", text)
        out: List[str] = []
        seen: Set[str] = set()
        for url in matches:
            cleaned = url.rstrip(".,;:)]}>")
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            out.append(cleaned)
        return out

    @staticmethod
    def _query_terms(text: str) -> Set[str]:
        terms = re.findall(r"[a-zA-Zа-яА-ЯёЁіІїЇєЄ0-9]+", (text or "").lower())
        stop = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "to",
            "in",
            "on",
            "for",
            "что",
            "как",
            "про",
            "последние",
            "новости",
            "today",
            "latest",
            "news",
        }
        return {t for t in terms if len(t) > 2 and t not in stop}

    @staticmethod
    def _parse_search_text_entries(text: str) -> List[Dict[str, str]]:
        raw = (text or "").strip()
        if not raw:
            return []
        pattern = re.compile(
            r"\d+\.\s*(?P<title>.+?)\n\s*URL:\s*(?P<url>https?://\S+)\n\s*Summary:\s*(?P<summary>.+?)(?=\n\d+\.|\Z)",
            flags=re.DOTALL,
        )
        out: List[Dict[str, str]] = []
        for m in pattern.finditer(raw):
            out.append(
                {
                    "title": " ".join((m.group("title") or "").split()),
                    "url": (m.group("url") or "").strip().rstrip(".,;:)]}>"),
                    "summary": " ".join((m.group("summary") or "").split()),
                }
            )
        return out

    def _score_url_entry(self, question: str, title: str, summary: str, url: str) -> float:
        q_terms = self._query_terms(question)
        text = f"{title} {summary} {url}".lower()
        score = 0.0

        for term in q_terms:
            if term in text:
                score += 1.0

        news_hints = [
            "news",
            "новост",
            "последн",
            "latest",
            "today",
            "сьогодні",
            "update",
            "breaking",
        ]
        for hint in news_hints:
            if hint in text:
                score += 1.5

        low_url = (url or "").lower()
        if any(
            x in low_url
            for x in [
                "wikipedia.org",
                "tripadvisor",
                "visitkyiv",
                "visitukraine",
                "booking.com",
                "airbnb.",
            ]
        ):
            score -= 2.0
        if any(x in low_url for x in ["unian", "ria.ru", "kyivpost", "tsn.ua", "rbc.ua", "24tv", "news"]):
            score += 2.0
        if any(x in text for x in ["tour", "attraction", "guide", "things to do", "музей", "екскурс", "тур"]):
            score -= 1.5

        return score

    def _prioritize_urls(self, question: str, output: Any, limit: int) -> List[str]:
        if not isinstance(output, str):
            urls = self._extract_urls_from_output(output)
            return urls[:limit]

        entries = self._parse_search_text_entries(output)
        if not entries:
            urls = self._extract_urls_from_text(output)
            return urls[:limit]

        ranked = sorted(
            entries,
            key=lambda e: self._score_url_entry(
                question,
                e.get("title", ""),
                e.get("summary", ""),
                e.get("url", ""),
            ),
            reverse=True,
        )
        out: List[str] = []
        seen: Set[str] = set()
        for row in ranked:
            url = row.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            out.append(url)
            if len(out) >= limit:
                break
        return out

    def _extract_urls_from_output(self, output: Any) -> List[str]:
        found: List[str] = []
        seen: Set[str] = set()

        def _add(url: str) -> None:
            if not url or url in seen:
                return
            seen.add(url)
            found.append(url)

        def _walk(value: Any) -> None:
            if value is None:
                return
            if isinstance(value, str):
                for u in self._extract_urls_from_text(value):
                    _add(u)
                return
            if isinstance(value, dict):
                for key, v in value.items():
                    key_l = str(key).lower()
                    if key_l in {"url", "href", "link", "source"} and isinstance(v, str):
                        for u in self._extract_urls_from_text(v):
                            _add(u)
                    else:
                        _walk(v)
                return
            if isinstance(value, list):
                for item in value:
                    _walk(item)
                return

        _walk(output)
        return found

    def _candidate_deep_urls(self, question: str, executed: List[ToolCallResult], *, limit: int) -> List[str]:
        urls: List[str] = []
        seen: Set[str] = set()
        for item in executed:
            if not self._is_web_search_tool(item.tool_name):
                continue
            prioritized = self._prioritize_urls(question, item.output, limit)
            if not prioritized:
                prioritized = self._extract_urls_from_output(item.output)
            for url in prioritized:
                if url in seen:
                    continue
                seen.add(url)
                urls.append(url)
                if len(urls) >= limit:
                    return urls
        return urls

    @staticmethod
    def _already_fetched_urls(executed: List[ToolCallResult]) -> Set[str]:
        out: Set[str] = set()
        for item in executed:
            name = (item.tool_name or "").lower()
            if not (name == "fetch_content" or name.endswith(".fetch_content")):
                continue
            url = str((item.arguments or {}).get("url", "")).strip()
            if url:
                out.add(url)
        return out

    def _extract_source_entries(self, executed: List[ToolCallResult], *, limit: int = 8) -> List[Dict[str, str]]:
        entries: List[Dict[str, str]] = []
        seen: Set[str] = set()
        for item in executed:
            if not self._is_web_search_tool(item.tool_name):
                continue
            output = item.output
            if isinstance(output, str):
                parsed = self._parse_search_text_entries(output)
                if parsed:
                    for row in parsed:
                        url = row.get("url", "")
                        title = row.get("title", "") or url
                        if not url or url in seen:
                            continue
                        seen.add(url)
                        entries.append({"title": title, "url": url})
                        if len(entries) >= limit:
                            return entries
                else:
                    for url in self._extract_urls_from_text(output):
                        if url in seen:
                            continue
                        seen.add(url)
                        entries.append({"title": url, "url": url})
                        if len(entries) >= limit:
                            return entries
            else:
                for url in self._extract_urls_from_output(output):
                    if url in seen:
                        continue
                    seen.add(url)
                    entries.append({"title": url, "url": url})
                    if len(entries) >= limit:
                        return entries
        return entries

    @staticmethod
    def _append_sources_if_missing(answer: str, entries: List[Dict[str, str]]) -> str:
        text = (answer or "").strip()
        if not entries:
            return text
        if "http://" in text or "https://" in text:
            return text
        lines = [text, "", "Sources:"]
        for idx, row in enumerate(entries, start=1):
            title = row.get("title", "").strip() or row.get("url", "")
            url = row.get("url", "").strip()
            if not url:
                continue
            lines.append(f"{idx}. {title} — {url}")
        return "\n".join(lines).strip()

    @traceable(
        run_type="chain",
        name="tool_agent.validate_completeness",
        process_inputs=_trace_process_inputs,
        process_outputs=_trace_process_plan_output,
    )
    def _validate_completeness(
        self,
        question: str,
        executed: List[ToolCallResult],
    ) -> Dict[str, Any]:
        has_search = any(self._is_web_search_tool(item.tool_name) for item in executed)
        has_fetch = any(self._is_fetch_content_tool(item.tool_name) for item in executed)
        if not has_search:
            return {"is_complete": True, "reason": "no_web_search_context"}
        if has_search and not has_fetch:
            # Search snippets are usually shallow; default to one deep fetch.
            return {"is_complete": False, "reason": "search_snippets_need_depth"}

        compact_context = self._render_context(question, executed)
        prompt = (
            "You validate if tool context is sufficient to answer the user.\n"
            "Return STRICT JSON: {\"is_complete\": true|false, \"reason\": \"...\"}\n"
            "Mark is_complete=false if important facts are missing.\n\n"
            f"Question:\n{question}\n\n"
            f"Tool context:\n{compact_context[:5000]}\n"
        )
        raw = self.llm.chat([{"role": "user", "content": prompt}], temperature=0.0, max_tokens=220)
        obj = self._extract_json_object_loose(raw)
        if not obj:
            return {"is_complete": False, "reason": "validator_parse_failed"}
        complete = bool(obj.get("is_complete", False))
        reason = str(obj.get("reason", "") or "")
        return {"is_complete": complete, "reason": reason}

    @traceable(
        run_type="chain",
        name="tool_agent.deepen_web_context",
        process_inputs=_trace_process_inputs,
        process_outputs=_trace_process_plan_output,
    )
    def _deepen_web_context(
        self,
        question: str,
        effective_plan: List[PlannedToolCall],
        executed: List[ToolCallResult],
    ) -> None:
        _ = question
        if self.max_deep_links <= 0:
            return
        fetch_tool = self._resolve_fetch_content_tool_name()
        if not fetch_tool:
            return

        urls = self._candidate_deep_urls(question, executed, limit=self.max_deep_links)
        for url in urls:
            call = PlannedToolCall(tool_name=fetch_tool, arguments={"url": url})
            try:
                result = self._execute_tool_call(call.tool_name, call.arguments)
            except ToolExecutionError:
                continue
            effective_plan.append(call)
            executed.append(result)

    @traceable(
        run_type="chain",
        name="tool_agent.plan_followup_search",
        process_inputs=_trace_process_inputs,
        process_outputs=_trace_process_text_output,
    )
    def _plan_followup_search_query(
        self,
        question: str,
        executed: List[ToolCallResult],
    ) -> str:
        context_preview = self._render_context(question, executed)
        prompt = (
            "You are a research planner.\n"
            "Given the user question and current tool context, return ONE follow-up web search query.\n"
            "Output STRICT JSON: {\"query\": \"...\"}\n"
            "Rules:\n"
            "- Query must stay close to the original user intent.\n"
            "- Prefer news/current-events wording when the question asks latest/current/today.\n"
            "- Do not output empty query.\n\n"
            f"User question:\n{question}\n\n"
            f"Current context:\n{context_preview[:4500]}\n"
        )
        raw = self.llm.chat([{"role": "user", "content": prompt}], temperature=0.1, max_tokens=180)
        obj = self._extract_json_object_loose(raw)
        if isinstance(obj, dict):
            query = str(obj.get("query", "") or "").strip()
            if query:
                return query
        return question

    @traceable(
        run_type="chain",
        name="tool_agent.web_research_loop",
        process_inputs=_trace_process_inputs,
        process_outputs=_trace_process_plan_output,
    )
    def _run_web_research_loop(
        self,
        question: str,
        effective_plan: List[PlannedToolCall],
        executed: List[ToolCallResult],
    ) -> Dict[str, Any]:
        web_tool = self._resolve_web_tool_name()
        fetch_tool = self._resolve_fetch_content_tool_name()
        if not web_tool:
            return {"iterations": 0, "reason": "no_web_tool"}

        iterations = 0
        for _ in range(self.max_research_iterations):
            iterations += 1
            completeness = self._validate_completeness(question, executed)
            if bool(completeness.get("is_complete", False)):
                return {"iterations": iterations, "reason": "complete"}

            added_any = False
            if fetch_tool and self.max_deep_links > 0:
                fetched = self._already_fetched_urls(executed)
                remaining_fetch_budget = max(0, self.max_deep_links - len(fetched))
                if remaining_fetch_budget > 0:
                    urls = self._candidate_deep_urls(
                        question,
                        executed,
                        limit=max(1, remaining_fetch_budget * 3),
                    )
                    urls = [u for u in urls if u not in fetched][:remaining_fetch_budget]
                else:
                    urls = []
                for url in urls:
                    call = PlannedToolCall(tool_name=fetch_tool, arguments={"url": url})
                    try:
                        result = self._execute_tool_call(call.tool_name, call.arguments)
                    except ToolExecutionError:
                        continue
                    effective_plan.append(call)
                    executed.append(result)
                    added_any = True

            if added_any:
                continue

            followup_query = self._plan_followup_search_query(question, executed)
            call = PlannedToolCall(
                tool_name=web_tool,
                arguments={"query": followup_query, "max_results": 8},
            )
            try:
                result = self._execute_tool_call(call.tool_name, call.arguments)
            except ToolExecutionError:
                return {"iterations": iterations, "reason": "followup_search_failed"}
            effective_plan.append(call)
            executed.append(result)

        return {"iterations": iterations, "reason": "max_iterations_reached"}

    @staticmethod
    def _rows_to_preview(rows: List[Dict[str, Any]], *, row_limit: int = 10) -> str:
        lines: List[str] = []
        for row in rows[:row_limit]:
            chunk_id = row.get("chunk_id")
            title = row.get("title") or row.get("document_id") or row.get("doc_id") or ""
            score = row.get("score")
            text = str(row.get("text") or "").strip().replace("\n", " ")
            if len(text) > 280:
                text = text[:277] + "..."
            prefix = f"- chunk_id={chunk_id}" if chunk_id else "- result"
            if score is not None:
                try:
                    prefix += f" score={float(score):.4f}"
                except Exception:
                    pass
            if title:
                prefix += f" title={title}"
            lines.append(f"{prefix} :: {text}")
        return "\n".join(lines)

    @traceable(
        run_type="chain",
        name="tool_agent.render_context",
        process_inputs=_trace_process_inputs,
        process_outputs=_trace_process_text_output,
    )
    def _render_context(self, question: str, results: List[ToolCallResult]) -> str:
        parts: List[str] = [f"QUESTION:\n{question}\n"]
        for item in results:
            parts.append(f"TOOL: {item.tool_name} ({item.provider})")
            out = item.output
            if isinstance(out, list) and all(isinstance(x, dict) for x in out):
                parts.append(self._rows_to_preview(out))
            elif isinstance(out, (dict, list)):
                parts.append(json.dumps(out, ensure_ascii=False, indent=2)[:2500])
            else:
                text = str(out or "").strip()
                parts.append(text[:2500])
            parts.append("")
        merged = "\n".join(parts).strip()
        if len(merged) > self.context_max_chars:
            return merged[: self.context_max_chars - 3] + "..."
        return merged

    @staticmethod
    def _normalize_tool_arguments(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        args = dict(arguments)
        if tool_name.lower().endswith("search"):
            if "query" not in args and "q" in args:
                args["query"] = args.get("q")
            if "max_results" not in args and "limit" in args:
                args["max_results"] = args.get("limit")
        return args

    def _normalize_planned_call(self, question: str, call: PlannedToolCall) -> PlannedToolCall:
        args = self._normalize_tool_arguments(call.tool_name, call.arguments)
        if self._is_web_search_tool(call.tool_name):
            planned_q = str(args.get("query", "") or "").strip()
            question_terms = self._query_terms(question)
            planned_terms = self._query_terms(planned_q)
            # Prevent planner from collapsing rich user query into too-short keyword.
            if not planned_q or len(planned_terms) < max(2, len(question_terms) // 2):
                args["query"] = question
            if "max_results" not in args:
                args["max_results"] = 8
        return PlannedToolCall(tool_name=call.tool_name, arguments=args)

    @staticmethod
    def _strip_think_blocks(text: str) -> str:
        if not text:
            return ""
        cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    @traceable(
        run_type="tool",
        name="tool_agent.call_tool",
        process_inputs=_trace_process_inputs,
        process_outputs=_trace_process_tool_call_output,
    )
    def _execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> ToolCallResult:
        normalized = self._normalize_tool_arguments(tool_name, arguments)
        return self.tool_registry.call_tool(tool_name, normalized)

    @traceable(
        run_type="chain",
        name="tool_agent.finalize_answer",
        process_inputs=_trace_process_inputs,
        process_outputs=_trace_process_text_output,
    )
    def _finalize_answer(self, question: str, context: str) -> str:
        system_prompt = (
            "You are a technical assistant.\n"
            "Use ONLY tool results in context. Do not invent facts.\n"
            "Do not output placeholders like '[Article 1]' or generic templates.\n"
            "For web/search results, include concrete items and URLs from context when available.\n"
            "If data is insufficient, explicitly say what is missing.\n"
            "Answer in the same language as the user question.\n"
        )
        answer = self.llm.generate_answer(question, context, system_prompt=system_prompt)
        return self._strip_think_blocks(answer)

    @traceable(
        run_type="chain",
        name="tool_agent.answer",
        process_inputs=_trace_process_inputs,
        process_outputs=_trace_process_agent_output,
    )
    def answer(self, question: str) -> ToolAgentResult:
        planned, raw = self._plan_tool_calls(question)
        executed: List[ToolCallResult] = []
        effective_plan: List[PlannedToolCall] = []
        for call in planned:
            normalized_call = self._normalize_planned_call(question, call)
            effective_plan.append(normalized_call)
            try:
                result = self._execute_tool_call(normalized_call.tool_name, normalized_call.arguments)
                executed.append(result)
            except ToolExecutionError:
                continue

        if self._should_retry_with_web(executed):
            web_tool = self._resolve_web_tool_name()
            if web_tool:
                retry_call = PlannedToolCall(
                    tool_name=web_tool,
                    arguments={"query": question, "max_results": 8},
                )
                try:
                    retry_result = self._execute_tool_call(retry_call.tool_name, retry_call.arguments)
                    effective_plan.append(retry_call)
                    executed.append(retry_result)
                except ToolExecutionError:
                    pass

        self._run_web_research_loop(question, effective_plan, executed)

        context = self._render_context(question, executed)
        answer = self._finalize_answer(question, context)
        answer = self._append_sources_if_missing(answer, self._extract_source_entries(executed))
        return ToolAgentResult(
            answer=answer,
            planned_calls=effective_plan,
            executed_results=executed,
            context=context,
            planning_raw=raw,
        )
