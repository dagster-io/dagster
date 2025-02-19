#!/bin/bash
#
# Builds and synchronizes mdx API docs, and objects.inv using Sphinx
#
# USAGE
#
#     yarn build-api-docs
#

set -e

# Vercel-specific commands and configurations
if ! [[ "$OSTYPE" =~ "darwin"* ]]; then
  echo "Detected non-Darwin host. Running Vercel-specific commands and configurations"

  # Required to resolve `locale.Error: unsupported locale setting`
  export LC_ALL=C.UTF-8

  if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # shellcheck source=/dev/null
    source "$HOME/.local/bin/env"  
  fi

  uv python install 3.11
  uv venv
  source .venv/bin/activate
  uv pip install tox
fi

echo "Running sphinx-mdx and copying files to \`docs/api/python-api\`"
tox -e sphinx-mdx
cp -rf sphinx/_build/mdx/sections/api/apidocs/* docs/api/python-api/

echo "Running sphinx and copying \`object.inv\` to \`static/\`"
tox -e sphinx
cp sphinx/_build/json/objects.inv static/.
