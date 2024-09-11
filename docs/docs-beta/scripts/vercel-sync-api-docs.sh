#!/bin/bash
#
# **NOTE: this script is intended to by used from Vercel only!**
#
# Description: Builds and synchronizes MDX API docs from Sphinx
# Usage: yarn sync-api-docs
#

set -e

cd ..

curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.cargo/env

uv venv
source .venv/bin/activate

# Required as is locale is not set by default in Vercel runner
export LC_ALL=C.UTF-8

uv pip install tox
make mdx
make mdx_copy
