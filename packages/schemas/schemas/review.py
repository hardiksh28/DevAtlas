from enum import StrEnum

from pydantic import BaseModel, Field


class ConceptTag(StrEnum):
    """Closed-set concept identifiers (ARCHITECTURE.md: "Closed-set concept
    taxonomy" — the LLM tags evidence against these, it never invents a
    new one). This enum is intentionally tiny right now; it grows as the
    Taxonomy Service's real concept list is authored, not by LLM output.
    """

    PYTHON_ASYNC_AWAIT = "python.async_await"
    SQL_NORMALIZATION = "sql.normalization"
    REACT_STATE_LIFTING = "react.state_lifting"


class ReviewComment(BaseModel):
    """One inline comment produced by the Code Review Engine. Shared here
    because both apps/api (writes it to Postgres, serves it to the
    client) and, eventually, the ingestion worker's evaluation tooling
    need to agree on this exact shape — defining it twice is how the two
    drift out of sync.
    """

    file_path: str
    line_start: int
    line_end: int
    body: str = Field(..., description="Socratic by default — a question, not an answer.")
    concept_tags: list[ConceptTag] = Field(default_factory=list)
