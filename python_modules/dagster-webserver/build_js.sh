#! /bin/bash
GIT_ROOT=$(git rev-parse --show-toplevel)

# Support both standalone OSS repo and monorepo
if [ -d "${GIT_ROOT}/dagster-oss" ]; then
    ROOT="${GIT_ROOT}/dagster-oss"
else
    ROOT="${GIT_ROOT}"
fi

pushd "$ROOT/js_modules/dagster-ui"
set -eux

yarn install
yarn build
