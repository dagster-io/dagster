#!/usr/bin/env bash

set -euo pipefail

models=(
  "qwen2.5:0.5b"
  "qwen2.5:1.5b"
)

docker compose up -d ollama

for model in "${models[@]}"; do
  echo "Pulling ${model}..."
  docker compose exec -T ollama ollama pull "${model}"
done

docker compose exec -T ollama ollama list
