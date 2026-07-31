"""The one number apps/api and services/ingestion_worker must never
disagree on: the embedding vector's dimensionality. apps/api's
`project_embeddings.embedding` pgvector column (declared via the ORM,
see apps/api/app/modules/knowledge/models.py) and the worker's raw
`CREATE TABLE`-equivalent write path (services/ingestion_worker/db.py)
both read this constant rather than hardcoding `768` independently in
two places that could silently drift the moment the embedding model
changes.

768 matches `nomic-embed-text` (the default OLLAMA_EMBEDDING_MODEL —
see apps/api/app/core/config.py and services/ingestion_worker/settings.py).
Changing the embedding model to one with a different output size means
changing this constant *and* writing a migration to alter the column
and re-embed every existing chunk — there is no way to mix dimensions
in one pgvector column.
"""

EMBEDDING_DIMENSIONS = 768
