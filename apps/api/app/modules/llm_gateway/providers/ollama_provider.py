from ollama import AsyncClient

from app.core.config import get_settings
from app.modules.llm_gateway.providers.base import LLMProvider

settings = get_settings()


class OllamaProvider(LLMProvider):
    """Local inference via Ollama's HTTP API. Chosen for local dev so the
    mentoring loop can be built and tested at zero API cost with no
    external dependency. Swapping in a hosted provider later is a config
    change (LLM_PROVIDER=anthropic + a new provider class here) — never a
    rewrite of call sites, because every caller only ever talks to
    LLMGateway, never to this class directly.
    """

    def __init__(self) -> None:
        self._client = AsyncClient(host=settings.ollama_base_url)

    async def generate(self, prompt: str, *, model: str | None = None) -> str:
        response = await self._client.generate(
            model=model or settings.ollama_model,
            prompt=prompt,
        )
        return response["response"]

    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        # Ollama's /api/embed is already batch-capable (input: str |
        # Sequence[str]) — one HTTP call regardless of len(texts),
        # not len(texts) round-trips.
        response = await self._client.embed(
            model=model or settings.ollama_embedding_model,
            input=texts,
        )
        return response["embeddings"]
