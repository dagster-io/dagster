#!/usr/bin/env bash
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
  export UV_PYTHON_DOWNLOADS=automatic
  uv python install 3.11
  uv venv --python 3.11 --clear
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
  echo "Running sphinx-mdx and copying files to \`docs/api\`"
  tox -e sphinx-mdx-vercel
  cp -rf sphinx/_build/mdx/sections/api/dagster docs/api
  cp -rf sphinx/_build/mdx/sections/integrations/libraries docs/integrations
  cp -rf sphinx/_build/mdx/sections/api/clis docs/api
  cp -rf sphinx/_build/mdx/sections/api/graphql docs/api

  echo "Copying \`objects.inv\` to \`static/\`"
  cp sphinx/_build/mdx/objects.inv static/.
else
  uv_install
  uv_activate_venv

  # Do not parallelize local sphinx-mdx build -- see tox.ini
  echo "Running sphinx-mdx and copying files to \`docs/api\`"
  tox -e sphinx-mdx-local
  cp -rf sphinx/_build/mdx/sections/api/dagster docs/api
  cp -rf sphinx/_build/mdx/sections/integrations/libraries docs/integrations
  cp -rf sphinx/_build/mdx/sections/api/clis docs/api
  cp -rf sphinx/_build/mdx/sections/api/graphql docs/api

  echo "Copying \`objects.inv\` to \`static/\`"
  cp sphinx/_build/mdx/objects.inv static/.
fi
