#!/bin/bash
#
# **NOTE: this script is intended to by used from Vercel only!**
#
# Description: Builds and synchronizes MDX API docs from Sphinx
# Usage: yarn sync-api-docs
#

set -e

cd ..

if ! command -v uv &> /dev/null; then
    echo "uv is missing from PATH--installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.cargo/env
fi

uv venv
source .venv/bin/activate

# Required as is locale is not set by default in Vercel runner
export LC_ALL=C.UTF-8

if ! command -v tox &> /dev/null; then
    echo "tox is missing from PATH--installing..."
    uv pip install tox
fi

make mdx
make mdx_copy
