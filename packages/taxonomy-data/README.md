# Taxonomy Data

Versioned concept-taxonomy content — the curated curriculum itself (ARCHITECTURE.md Section 6). This is data, not code: the Taxonomy & Concept Graph Service module loads these files into the `concepts` table; it does not generate them and the LLM never writes to this directory.

Each file under `concepts/` is one stack's concept graph. `concepts/example-python-basics.yaml` shows the shape a real curated file follows — replace it as real curriculum content is authored, don't extend it programmatically.
