#!/bin/bash
DAGIT_BACKCOMPAT_VERSION=$1
USER_CODE_BACKCOMPAT_VERSION=$2


ROOT=$(git rev-parse --show-toplevel)
BASE_DIR="${ROOT}/integration_tests/test_suites/backcompat-test-suite/dagit_service"

function cleanup {
    rm -rf "${BASE_DIR}/python_modules"
    set +ux
    shopt -u expand_aliases
}

cleanup

# ensure cleanup happens on error or normal exit
trap cleanup INT TERM EXIT ERR

set -ux
shopt -s expand_aliases

pushd $BASE_DIR

mkdir -p python_modules
mkdir -p python_modules/libraries/

echo -e "--- \033[32m:truck: Copying files...\033[0m"
alias copy_py="rsync -av \
      --progress \
      --exclude *.egginfo \
      --exclude *.tox \
      --exclude dist \
      --exclude __pycache__ \
      --exclude *.pyc \
      --exclude .coverage"

copy_py $ROOT/python_modules/dagster \
        $ROOT/python_modules/dagit \
        $ROOT/python_modules/dagster-graphql \
        python_modules/

copy_py $ROOT/python_modules/libraries/dagster-postgres \
        $ROOT/python_modules/libraries/dagster-docker \
        python_modules/libraries/

echo -e "--- \033[32m:docker: Building Docker images\033[0m"
docker-compose build \
    --build-arg DAGIT_BACKCOMPAT_VERSION=${DAGIT_BACKCOMPAT_VERSION} \
    --build-arg USER_CODE_BACKCOMPAT_VERSION=${USER_CODE_BACKCOMPAT_VERSION}
