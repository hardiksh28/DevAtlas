from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.modules.llm_gateway.providers.base import LLMProvider


class GatewayState(TypedDict):
    operation: str
    prompt: str
    context: str
    response: str


def build_graph(provider: LLMProvider):
    """A minimal two-node graph: assemble context, then generate.

    Kept small deliberately — the real payoff of using LangGraph here
    shows up once branches are added for ARCHITECTURE.md's hint-ladder /
    effort-gate flows (e.g. a conditional edge routing to "reveal" vs.
    "ask for more evidence" based on the Effort Evaluator's verdict). The
    graph *shape* is the point: it's what lets that branching be added
    later without changing how every other module calls the gateway.
    """

    async def assemble_context(state: GatewayState) -> GatewayState:
        # Real implementation pulls structured project state + global
        # corpus docs per ARCHITECTURE.md Section 4's retrieval order.
        # Passthrough here — no module has retrieval-worthy data yet.
        return {**state, "context": ""}

    async def generate(state: GatewayState) -> GatewayState:
        full_prompt = f"{state['context']}\n\n{state['prompt']}".strip()
        result = await provider.generate(full_prompt)
        return {**state, "response": result}

    graph = StateGraph(GatewayState)
    graph.add_node("assemble_context", assemble_context)
    graph.add_node("generate", generate)
    graph.set_entry_point("assemble_context")
    graph.add_edge("assemble_context", "generate")
    graph.add_edge("generate", END)

    return graph.compile()
