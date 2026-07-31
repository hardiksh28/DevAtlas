from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Every LLM backend (Ollama today, Anthropic Claude later — see
    ARCHITECTURE.md's model-routing-by-cost design) implements these two
    methods. No module outside llm_gateway is allowed to depend on a
    concrete provider; they depend on LLMGateway instead (gateway.py).
    """

    @abstractmethod
    async def generate(self, prompt: str, *, model: str | None = None) -> str: ...

    @abstractmethod
    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        """Returns one vector per input text, same order. Batched rather
        than one-text-at-a-time in the signature itself — the RAG
        Knowledge Engine's dominant embedding workload (the ingestion
        worker embedding hundreds of chunks) needs batching to be
        efficient, and a batched-first signature means query-time
        single-text embedding (`embed([query])`) is just the
        batch-size-1 case, not a second code path."""
        ...
