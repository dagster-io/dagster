#!/bin/bash

set -e

uv_install() {
  if command -v uv &>/dev/null; then
    echo "uv is already installed in this environment..."
  else
      curl -LsSf https://astral.sh/uv/install.sh | sh
      source "$HOME/.local/bin/env"
  fi
}

uv_activate_venv() {
  uv python install 3.11
  uv venv
  source .venv/bin/activate
  uv pip install tox
}

# TODO - refactor Vercel logic shared between `build-kinds-tags` and `build-api-docs` into single script
if [ "$VERCEL" = "1" ]; then
  echo "Detected Vercel environment. Running Vercel-specific commands and configurations."
  export LC_ALL=C.UTF-8
  uv_install
  uv_activate_venv
fi

uv run --no-project scripts/rebuild-kinds-tags.py
