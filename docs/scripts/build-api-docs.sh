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
fi

# Required to resolve `locale.Error: unsupported locale setting`
if [[ -z "$LC_ALL" && "$(uname)" == "Darwin" ]]; then
  export LC_ALL=en_US.UTF-8
fi

echo "Running sphinx-mdx and copying files to \`docs/api/python-api\`"
tox -e sphinx-mdx
cp -rf sphinx/_build/mdx/sections/api/apidocs/* docs/api/python-api/

echo "Running sphinx and copying \`object.inv\` to \`static/\`"
tox -e sphinx
cp sphinx/_build/json/objects.inv static/.
