#!/bin/sh
# Starts the Ollama server, then pulls the configured models if they
# aren't already present locally. Without this, a fresh `docker compose
# up` gives you a running Ollama server with zero models and every
# generation/embedding call fails with "model not found" until someone
# manually docker exec's in.
set -e

ollama serve &
server_pid=$!

until ollama list >/dev/null 2>&1; do
  sleep 1
done

model="${OLLAMA_MODEL:-llama3.1:8b}"
if ! ollama list | grep -q "${model%%:*}"; then
  echo "Pulling model: ${model}"
  ollama pull "${model}"
fi

# Embedding-capable model — a different model family from the chat/
# generation model above (see docs/architecture/rag-engine-v1.md); the
# RAG Knowledge Engine's ingestion-side embedding step and query-time
# embedding both fail until this is pulled.
embedding_model="${OLLAMA_EMBEDDING_MODEL:-nomic-embed-text}"
if ! ollama list | grep -q "${embedding_model%%:*}"; then
  echo "Pulling embedding model: ${embedding_model}"
  ollama pull "${embedding_model}"
fi

wait "${server_pid}"
