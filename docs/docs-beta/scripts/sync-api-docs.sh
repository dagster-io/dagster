#!/bin/sh
# Description: Builds and synchronizes MDX API docs from Sphinx
# Usage: yarn sync-api-docs

pushd ../sphinx

make install_uv
make install
make mdx
make mdx_copy

popd
