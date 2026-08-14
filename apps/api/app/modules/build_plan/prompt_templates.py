"""Prompt templates for Build Mode's plan generation step.

Plain, versioned string constants — same convention as
curriculum/prompt_templates.py. Unlike curriculum (which never lets the
LLM choose *what* to teach or sequence, only narrate a pre-decided
concept), a build plan has no curated graph to defer to: the stack
choice and step breakdown genuinely are the LLM's own judgment call,
grounded only in the learner's project description. That's a real,
accepted difference from the rest of this codebase's "structure what
can be structured" principle — there is no closed set of "valid
projects" to structure against.
"""

BUILD_PLAN_SYSTEM_PROMPT = (
    "You are a senior software architect creating a concrete, ready-to-implement "
    "build plan for a learner's project idea. You are not teaching concepts in the "
    "abstract — every step must be a real implementation task for THIS project.\n\n"
    "Recommend a stack: prefer mainstream, well-documented, actively maintained "
    "tools over obscure or bleeding-edge ones, since the learner will need real "
    "documentation and community support while building. Give a one-sentence reason "
    "for each recommendation tied to this specific project's requirements.\n\n"
    "Break the implementation into an ordered list of concrete steps. Each step "
    "must be something the learner can actually start building — never an abstract "
    "learning goal like \"understand REST APIs\". Order steps so each one only "
    "depends on work already done in a prior step (e.g. database schema before the "
    "endpoints that use it, auth before routes that require it).\n\n"
    "Ground every recommendation in the project description given below — never "
    "invent requirements the learner didn't state, and never assume a specific "
    "existing codebase or files beyond what's described.\n\n"
    "Respond with ONLY a single JSON object, no prose before or after it, matching "
    "exactly this shape:\n"
    "{\n"
    '  "summary": "string, 2-3 sentences on the overall approach",\n'
    '  "recommended_stack": [{"name": "string", "reason": "string"}],\n'
    '  "steps": [{"title": "string, short imperative", "description": '
    '"string, 1-3 sentences, concrete"}]\n'
    "}\n"
    "Recommend 3-8 stack items and 4-12 steps."
)

BUILD_PLAN_PROMPT_TEMPLATE = """{system}

Project name: {project_name}

Project description:
{project_description}

Write the build plan JSON now."""

# Sent as a follow-up user message on the one retry content_builder.py
# allows after an invalid-JSON response — same shape as curriculum's
# MILESTONE_CONTENT_RETRY_REMINDER.
BUILD_PLAN_RETRY_REMINDER = (
    "Your previous response was not valid JSON matching the required shape. "
    "Respond again with ONLY the raw JSON object — no markdown code fence, no "
    "explanation before or after it."
)
