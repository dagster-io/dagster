#!/bin/bash

set -euo pipefail

MAX_RETRIES=5
DELAY=3

for ((i=1; i<=MAX_RETRIES; i++)); do
  LOG=$(mktemp)
  if uv pip install "$@" &> "$LOG"; then
    rm "$LOG"
    exit 0
  elif grep -q "stream closed because of a broken pipe" "$LOG"; then
    sleep $DELAY
  else
    cat "$LOG"
    rm "$LOG"
    exit 1
  fi
done

exit 1
