#!/bin/sh
#
# **NOTE: this script is intended to by used from Vercel only!**
#
# Description: Builds and synchronizes MDX API docs from Sphinx
# Usage: yarn sync-api-docs
#

pushd ../sphinx

curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.cargo/env

make install
make mdx
make mdx_copy

popd
