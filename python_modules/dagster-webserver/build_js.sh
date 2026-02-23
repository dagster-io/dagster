#!/bin/bash
export COREPACK_ENABLE_DOWNLOAD_PROMPT=0

GIT_ROOT=$(git rev-parse --show-toplevel)

if [ -d "${GIT_ROOT}/dagster-oss" ]; then
    ROOT="${GIT_ROOT}/dagster-oss"
else
    ROOT="${GIT_ROOT}"
fi

pushd "$ROOT/js_modules/dagster-ui"
set -eux

corepack enable
yarn install
yarn workspace @dagster-io/app-oss build
