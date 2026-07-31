from functools import lru_cache

from app.core.config import get_settings
from app.modules.llm_gateway.graph import build_graph
from app.modules.llm_gateway.providers.base import LLMProvider
from app.modules.llm_gateway.providers.ollama_provider import OllamaProvider

settings = get_settings()


def _build_provider() -> LLMProvider:
    if settings.llm_provider == "ollama":
        return OllamaProvider()
    raise ValueError(
        f"Unknown LLM_PROVIDER '{settings.llm_provider}'. Add a provider under "
        "app/modules/llm_gateway/providers/ and register it here."
    )


class LLMGateway:
    """The single choke point every module goes through to call a model
    (ARCHITECTURE.md Section 3, "LLM Orchestration Gateway"). No module
    outside this one should import a provider or LangGraph directly.
    """

    def __init__(self) -> None:
        self._provider = _build_provider()
        self._graph = build_graph(self._provider)

    async def generate(self, operation: str, prompt: str) -> str:
        # `operation` isn't used for routing yet (single provider/model),
        # but stays in the signature now so future cost-based model
        # routing (cheap model for hints, strongest model for full
        # reviews) is a change inside this class, not at every call site.
        result = await self._graph.ainvoke(
            {"operation": operation, "prompt": prompt, "context": "", "response": ""}
        )
        return result["response"]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # No graph involved — embedding is a single model call with no
        # context-assembly step of its own (the RAG Knowledge Engine's
        # retrieval/context_builder.py is what *uses* embeddings; it
        # isn't a stage inside producing one). Goes straight to the
        # provider, same as `generate` would if it had no graph either.
        return await self._provider.embed(texts)


@lru_cache
def get_llm_gateway() -> LLMGateway:
    return LLMGateway()
