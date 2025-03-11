#!/bin/bash
#
# Builds and synchronizes mdx API docs, and objects.inv using Sphinx
#
# USAGE
#
#     yarn build-api-docs
#

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

# https://vercel.com/docs/projects/environment-variables/system-environment-variables#VERCEL
if [ "$VERCEL" = "1" ]; then
  echo "Detected Vercel environment. Running Vercel-specific commands and configurations."
  # Required to resolve `locale.Error: unsupported locale setting`
  export LC_ALL=C.UTF-8
  uv_install
  uv_activate_venv

  # Parallelize production sphinx-mdx build -- see tox.ini
  echo "Running sphinx-mdx and copying files to \`docs/api/python-api\`"
  tox -e sphinx-mdx-vercel
  cp -rf sphinx/_build/mdx/sections/api/apidocs/* docs/api/python-api/

  # Parallelize production sphinx-inv build -- see tox.ini
  echo "Running sphinx and copying \`object.inv\` to \`static/\`"
  tox -e sphinx-inv-vercel
  cp sphinx/_build/json/objects.inv static/.
else
  # Do not parallelize local sphinx-mdx build -- see tox.ini
  echo "Running sphinx-mdx and copying files to \`docs/api/python-api\`"
  tox -e sphinx-mdx-local
  cp -rf sphinx/_build/mdx/sections/api/apidocs/* docs/api/python-api/
  
  # Do not parallelize local sphinx-inv build -- see tox.ini
  echo "Running sphinx and copying \`object.inv\` to \`static/\`"
  tox -e sphinx-inv-local
  cp sphinx/_build/json/objects.inv static/.
fi

# generate kinds tags partial
uv run --no-project scripts/rebuild-kinds-tags.py
