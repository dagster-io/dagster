#!/bin/bash
#
# Description: Builds and synchronizes MDX API docs from Sphinx Usage: yarn sync-api-docs
#

set -e

cd ..

# only set local when running in Vercel, not local execution
if ! [[ "$OSTYPE" =~ "darwin"* ]]; then
    export LC_ALL=C.UTF-8
fi

if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.local/bin/env"
fi

uv python install 3.11
uv venv
source .venv/bin/activate

uv pip install tox
uvx tox -e sphinx-mdx
make mdx_copy
