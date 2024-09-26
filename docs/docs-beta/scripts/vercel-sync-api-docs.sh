#!/bin/bash
#
# **NOTE: this script is intended to by used from Vercel only!**
#
# Description: Builds and synchronizes MDX API docs from Sphinx
# Usage: yarn sync-api-docs
#

set -e

cd ..

export LC_ALL=C.UTF-8

curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.cargo/env

uv python install 3.11
uv venv
source .venv/bin/activate

uv pip install tox
uvx tox -e sphinx-mdx
make mdx_copy
