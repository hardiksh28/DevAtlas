from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Every LLM backend (Ollama today, Anthropic Claude later — see
    ARCHITECTURE.md's model-routing-by-cost design) implements this one
    method. No module outside llm_gateway is allowed to depend on a
    concrete provider; they depend on LLMGateway instead (gateway.py).
    """

    @abstractmethod
    async def generate(self, prompt: str, *, model: str | None = None) -> str: ...
