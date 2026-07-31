"""Prompt Builder — the last assembly step before an Ollama call:
combines the system instructions and the built context (context_builder.py)
with the user's question into the single string the LLM Gateway sends
to the model.

Deliberately trivial. Keeping it this thin is the point: every actual
policy decision (what the model is allowed to do, how strict the
grounding requirement is) lives in prompt_templates.py's data, not here
— so changing that policy never means reading or changing this
function.
"""

from app.modules.knowledge.retrieval.context_builder import BuiltContext
from app.modules.knowledge.retrieval.prompt_templates import RAG_PROMPT_TEMPLATE, SYSTEM_PROMPT


def build_prompt(context: BuiltContext, question: str) -> str:
    return RAG_PROMPT_TEMPLATE.format(system=SYSTEM_PROMPT, context=context.text, question=question)
