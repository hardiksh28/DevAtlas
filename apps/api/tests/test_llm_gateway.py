"""Unit tests for app.modules.llm_gateway.gateway.LLMGateway.

Swaps in a fake provider rather than talking to real Ollama — same
"fake the boundary, test the orchestration" approach as
tests/test_rag_service.py's FakeLLMGateway, just one layer down (this
tests LLMGateway itself, which is what FakeLLMGateway stands in for
everywhere else).
"""

from app.modules.llm_gateway.gateway import LLMGateway


class FakeProvider:
    def __init__(self) -> None:
        self.generate_calls: list[str] = []
        self.embed_calls: list[list[str]] = []

    async def generate(self, prompt: str, *, model: str | None = None) -> str:
        self.generate_calls.append(prompt)
        return f"echo: {prompt}"

    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        self.embed_calls.append(texts)
        return [[float(len(t))] for t in texts]


def _make_gateway_with_fake_provider() -> tuple[LLMGateway, FakeProvider]:
    # LLMGateway.__init__ builds its own provider from settings.llm_provider
    # and compiles a LangGraph around it — neither is needed for this
    # test, so the object is constructed via __new__ and wired directly,
    # bypassing __init__ entirely rather than monkeypatching module-level
    # provider-selection logic just to inject a fake.
    gateway = LLMGateway.__new__(LLMGateway)
    provider = FakeProvider()
    gateway._provider = provider
    from app.modules.llm_gateway.graph import build_graph

    gateway._graph = build_graph(provider)
    return gateway, provider


class TestEmbed:
    async def test_delegates_to_provider_and_returns_vectors(self):
        gateway, provider = _make_gateway_with_fake_provider()

        result = await gateway.embed(["hello", "hi"])

        assert result == [[5.0], [2.0]]
        assert provider.embed_calls == [["hello", "hi"]]

    async def test_single_text_is_the_batch_size_one_case(self):
        gateway, _ = _make_gateway_with_fake_provider()
        result = await gateway.embed(["question"])
        assert len(result) == 1


class TestGenerate:
    async def test_delegates_to_provider_via_the_graph(self):
        gateway, provider = _make_gateway_with_fake_provider()

        result = await gateway.generate("rag_answer", "What is X?")

        assert result == "echo: What is X?"
        assert provider.generate_calls == ["What is X?"]
