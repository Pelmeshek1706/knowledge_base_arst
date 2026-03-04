from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


def _normalize_base_url(raw: str) -> str:
    base = (raw or "").strip().rstrip("/")
    if not base:
        return ""
    if base.endswith("/v1"):
        return base
    return f"{base}/v1"


@dataclass(frozen=True)
class LangChainRuntimeConfig:
    model: str
    base_url: Optional[str]
    api_key: Optional[str]
    embedding_model: Optional[str]
    temperature: float = 0.1

    @classmethod
    def from_env(cls) -> "LangChainRuntimeConfig":
        model = (
            os.environ.get("AGENT_MODEL")
            or os.environ.get("LMSTUDIO_MODEL")
            or "qwen2.5-1.5b-instruct"
        )
        base_url = (
            os.environ.get("AGENT_BASE_URL")
            or os.environ.get("LMSTUDIO_URL")
            or os.environ.get("OPENAI_BASE_URL")
            or "http://localhost:1234"
        )
        api_key = (
            os.environ.get("AGENT_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("LMSTUDIO_API_KEY")
            or "lm-studio"
        )
        embedding_model = (
            os.environ.get("AGENT_EMBED_MODEL")
            or os.environ.get("LMSTUDIO_EMBED_MODEL")
            or model
        )
        temperature = float(os.environ.get("AGENT_TEMPERATURE", "0.1"))
        return cls(
            model=model,
            base_url=_normalize_base_url(base_url) if base_url else None,
            api_key=api_key,
            embedding_model=embedding_model,
            temperature=temperature,
        )


class LangChainRuntime:
    """Factory for LangChain chat and embeddings clients."""

    def __init__(self, cfg: LangChainRuntimeConfig):
        self.cfg = cfg

    @classmethod
    def from_env(cls) -> "LangChainRuntime":
        return cls(LangChainRuntimeConfig.from_env())

    def build_chat_model(self, *, temperature: Optional[float] = None) -> BaseChatModel:
        model_kwargs = {
            "model": self.cfg.model,
            "temperature": self.cfg.temperature if temperature is None else float(temperature),
            "api_key": self.cfg.api_key,
        }
        if self.cfg.base_url:
            model_kwargs["base_url"] = self.cfg.base_url
        return ChatOpenAI(**model_kwargs)

    def build_embeddings(self) -> OpenAIEmbeddings:
        model_kwargs = {
            "model": self.cfg.embedding_model or self.cfg.model,
            "api_key": self.cfg.api_key,
        }
        if self.cfg.base_url:
            model_kwargs["base_url"] = self.cfg.base_url
        return OpenAIEmbeddings(**model_kwargs)
