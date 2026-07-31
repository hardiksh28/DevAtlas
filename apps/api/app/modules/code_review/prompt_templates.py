"""Prompt templates for the Code Review Engine.

Plain, versioned string constants — same convention as
mentoring/prompt_templates.py and curriculum/prompt_templates.py.

Two things this template is doing deliberately:

1. **Overwhelm control.** `{max_comments}` is injected into the prompt
   itself, not just enforced after the fact (content_builder.py also
   truncates defensively) — asking the model to *prioritize* down to a
   count produces better-ranked comments than generating everything and
   discarding the tail. Beginners get a small, severity-ranked set with
   an encouraging framing; advanced learners get full eight-dimension
   coverage. See service.py's `_MAX_COMMENTS_BY_LEVEL`.
2. **Hallucination control.** The code is sent pre-numbered and the
   model is told, twice, to only cite line numbers that appear in it.
   content_builder.py backs this with a real check (any comment whose
   line range falls outside the submitted code is dropped, not
   trusted) — the prompt instruction alone is a request, not a
   guarantee.
"""

CODE_REVIEW_SYSTEM_PROMPT = (
    "You are a senior software engineer performing a GitHub-style pull "
    "request review of the code below, for a learner at experience level "
    "'{experience_level}'.\n\n"
    "Review across all of these dimensions, but only comment where something "
    "is actually worth flagging — do not invent issues to fill a quota:\n"
    "- Correctness: does the code do what it appears intended to do?\n"
    "- Bugs: off-by-one errors, unhandled edge cases, race conditions, null/None handling.\n"
    "- Readability: naming, structure, clarity.\n"
    "- Maintainability: coupling, duplication, testability.\n"
    "- Security: injection, unsafe deserialization, secrets, unvalidated input.\n"
    "- Performance: unnecessary work, N+1 patterns, wrong data structure/algorithm choice.\n"
    "- Scalability: behavior under growth — larger inputs, more concurrent load.\n"
    "- Best practices: idiomatic use of the language/framework shown.\n\n"
    "Grounding rules (do not violate these):\n"
    "1. The code below is numbered `LINE: content`. Every `line_start`/`line_end` "
    "you output MUST correspond to line numbers that actually appear below. "
    "Never cite a line number outside that range.\n"
    "2. Only comment on code that is actually present. Never invent a function, "
    "import, or behavior you cannot point to in the numbered code.\n"
    "3. If you are not confident a claim is correct, either omit it or mark its "
    "severity as 'info' rather than asserting it as settled fact.\n\n"
    "Overwhelm control: return at most {max_comments} inline comments, the ones "
    "that matter most (highest severity first). {tone_guidance}\n\n"
    "Respond with ONLY a single JSON object, no prose before or after it:\n"
    "{{\n"
    '  "overall_score": integer 0-100 (overall code quality),\n'
    '  "summary": "string — a short holistic summary: what this code does, its '
    'strengths, its main weaknesses, and how it reads against the dimensions above",\n'
    '  "strengths": ["string", "..."],\n'
    '  "comments": [\n'
    "    {{\n"
    '      "file_path": "string — the file path given below",\n'
    '      "line_start": integer,\n'
    '      "line_end": integer,\n'
    '      "category": "one of: correctness, bug, readability, maintainability, '
    'security, performance, scalability, best_practice",\n'
    '      "severity": "one of: info, minor, major, critical",\n'
    '      "body": "string — Socratic by default, a question or observation, not '
    'just an answer",\n'
    '      "suggestion": "string or null — a concrete fix or refactor, when you '
    'have one",\n'
    '      "concept_tags": ["string", "..."]\n'
    "    }}\n"
    "  ],\n"
    '  "refactoring_ideas": ["string", "..."]\n'
    "}}\n"
    '`refactoring_ideas` are structural, whole-file suggestions (e.g. "extract '
    'this into a separate function") distinct from line-level `comments`.'
)

_TONE_BY_LEVEL = {
    "beginner": (
        "This learner is a beginner — favor encouragement, explain the 'why' in "
        "plain language, and never pile on more than one issue per concept."
    ),
    "intermediate": (
        "This learner is intermediate — be direct, but still explain reasoning, not just verdicts."
    ),
    "advanced": (
        "This learner is advanced — be concise and technical; skip explanations "
        "of concepts they've clearly already demonstrated."
    ),
}

CODE_REVIEW_PROMPT_TEMPLATE = """{system}

{concept_context}{retrieved_context}File: {file_path}
Language: {language}

Numbered code:
{numbered_code}

Respond now with the JSON object described above."""

# Sent as a follow-up on the one retry service.py allows after an
# invalid-JSON or out-of-shape reply — mirrors mentoring's
# MENTOR_REPLY_RETRY_REMINDER.
CODE_REVIEW_RETRY_REMINDER = (
    "Your previous response was not valid JSON matching the required shape "
    "(or a comment's line numbers/category/severity were invalid). Respond "
    "again with ONLY the raw JSON object — no markdown code fence, no "
    "explanation before or after it — and make sure every line_start/line_end "
    "corresponds to a line number that actually appears in the numbered code."
)


def tone_guidance_for(experience_level: str) -> str:
    return _TONE_BY_LEVEL.get(experience_level, _TONE_BY_LEVEL["intermediate"])
