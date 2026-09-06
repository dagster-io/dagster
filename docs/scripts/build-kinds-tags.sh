#!/usr/bin/env bash

set -e

uv_install() {
  # Always install a current uv rather than trusting one already on the PATH.
  # Vercel's build image rotates and has shipped uv versions that cannot
  # resolve CPython downloads.
  curl -LsSf https://astral.sh/uv/install.sh | sh
  source "$HOME/.local/bin/env"
}

uv_activate_venv() {
  export UV_PYTHON_DOWNLOADS=automatic
  # Vercel's build image ships its own uv setup; log which uv runs and any
  # UV_* configuration it injects, then neutralize overrides that can point
  # Python downloads at an incomplete mirror.
  command -v uv
  uv --version
  env | grep -i '^UV' || true
  unset UV_PYTHON_INSTALL_MIRROR UV_PYTHON_DOWNLOADS_JSON_URL UV_NO_MANAGED_PYTHON UV_PYTHON_PREFERENCE
  uv python install 3.11 --no-config
  uv venv --python 3.11 --clear
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
