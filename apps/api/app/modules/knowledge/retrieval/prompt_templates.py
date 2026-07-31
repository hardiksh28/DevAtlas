"""Prompt templates for the RAG Knowledge Engine.

Plain, versioned string templates — kept as data, deliberately separate
from prompt_builder.py's assembly logic, so that changing wording or
grounding strategy (e.g. stricter citation requirements, a different
refusal phrasing) is a template edit here, never a change to the code
that calls the LLM. See docs/architecture/rag-engine-v1.md Section 7
("Hallucination Prevention") for why every instruction below exists.
"""

# Every clause here maps directly to one hallucination-prevention
# mechanism: "ONLY the... passages" forbids outside knowledge, "cite the
# passage number(s)" forces traceability (an ungrounded sentence has no
# citation to point to), and the explicit permission to say "I don't
# know" removes the model's incentive to fill a gap with something
# plausible-sounding instead of admitting the corpus doesn't cover it.
SYSTEM_PROMPT = (
    "You are a documentation assistant. Answer the user's question using ONLY "
    "the numbered context passages below. Every claim in your answer must be "
    "traceable to at least one passage — cite the passage number(s) you used "
    "in square brackets, e.g. [1] or [2][3]. "
    "If the passages don't contain enough information to answer confidently, "
    "say so explicitly instead of guessing or relying on outside knowledge. "
    "Be concise: answer the question directly, then add supporting detail only "
    "if it's useful."
)

RAG_PROMPT_TEMPLATE = """{system}

Context:
{context}

Question: {question}

Answer:"""

# Used by rag_service.py when retrieval returns zero chunks — no LLM
# call happens in that case at all (see rag_service.py's docstring),
# so this is only ever surfaced as the literal answer text, never sent
# to Ollama as a prompt.
NO_RESULTS_ANSWER = (
    "I couldn't find anything in this project's ingested documentation that "
    "answers this question. Try rephrasing it, or ingest documentation that "
    "covers this topic."
)
