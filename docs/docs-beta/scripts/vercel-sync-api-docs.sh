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

# File "/vercel/path0/docs/sphinx/.venv/bin/sphinx-build", line 8, in <module>
#   sys.exit(main())
#            ^^^^^^
# File "/vercel/path0/docs/sphinx/.venv/lib/python3.12/site-packages/sphinx/cmd/build.py", line 369, in main
#   locale.setlocale(locale.LC_ALL, '')
# File "/python312/lib/python3.12/locale.py", line 615, in setlocale
#   return _setlocale(category, locale)
#          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# locale.Error: unsupported locale setting
export LC_ALL=C.UTF-8

uv pip install tox
make mdx
make mdx_copy
