import httpx

from app.core.config import get_settings
from app.modules.llm_gateway.providers.base import LLMProvider
from app.modules.llm_gateway.providers.ollama_provider import OllamaProvider

settings = get_settings()

GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqProvider(LLMProvider):
    """Hosted inference via Groq's OpenAI-compatible chat completions API
    (called directly with httpx — already a project dependency, and one
    POST endpoint doesn't justify the `groq` SDK). Chosen over Ollama when
    the caller wants fast hosted generation without running a local
    model.

    Groq has no embeddings endpoint, so `embed()` delegates to a plain
    `OllamaProvider` regardless — RAG search/ask still needs a local
    Ollama running for `nomic-embed-text` even with LLM_PROVIDER=groq;
    only generation (mentor, lesson content, code review) moves to Groq.
    """

    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise ValueError(
                "LLM_PROVIDER=groq requires GROQ_API_KEY to be set "
                "(get one at https://console.groq.com/keys)"
            )
        self._api_key = settings.groq_api_key
        self._embed_fallback = OllamaProvider()

    async def generate(self, prompt: str, *, model: str | None = None) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GROQ_CHAT_COMPLETIONS_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": model or settings.groq_model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        return await self._embed_fallback.embed(texts, model=model)
