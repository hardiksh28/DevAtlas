#!/bin/sh
# Starts the Ollama server, then pulls the configured model if it isn't
# already present locally. Without this, a fresh `docker compose up` gives
# you a running Ollama server with zero models and every generation call
# fails with "model not found" until someone manually docker exec's in.
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

wait "${server_pid}"
