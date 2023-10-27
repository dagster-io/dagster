#! /bin/bash
ROOT=$(git rev-parse --show-toplevel)
pushd "$ROOT/js_modules/dagster-ui"
set -eux

yarn install
yarn build
