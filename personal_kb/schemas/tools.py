from __future__ import annotations

from typing import Literal, TypeAlias

from personal_kb.schemas.qa import AnswerQuestionRequest, AnswerQuestionResponse
from personal_kb.schemas.search import SearchDocumentsRequest, SearchDocumentsResponse

ToolName: TypeAlias = Literal["search_documents", "answer_question"]
ToolRequest: TypeAlias = SearchDocumentsRequest | AnswerQuestionRequest
ToolResponse: TypeAlias = SearchDocumentsResponse | AnswerQuestionResponse
