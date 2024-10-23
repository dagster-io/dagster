#!/bin/bash
WEBSERVER_VERSION=$1
WEBSERVER_LIBRARY_VERSION=$2
USER_CODE_VERSION=$3
USER_CODE_LIBRARY_VERSION=$4
USER_CODE_DEFINITIONS_FILE=$5

if [ "$WEBSERVER_VERSION" = "current_branch" ]; then
    export WEBSERVER_DOCKERFILE="./Dockerfile_webserver_source"
else
    export WEBSERVER_DOCKERFILE="./Dockerfile_webserver_release"
fi

if [ "$USER_CODE_VERSION" = "current_branch" ]; then
    export USER_CODE_DOCKERFILE="./Dockerfile_user_code_source"
else
    export USER_CODE_DOCKERFILE="./Dockerfile_user_code_release"
fi

ROOT=$(git rev-parse --show-toplevel)
BASE_DIR="${ROOT}/integration_tests/test_suites/backcompat-test-suite/webserver_service"

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
        $ROOT/python_modules/dagster-pipes \
        $ROOT/python_modules/dagit \
        $ROOT/python_modules/dagster-webserver \
        $ROOT/python_modules/dagster-graphql \
        python_modules/

copy_py $ROOT/python_modules/libraries/dagster-postgres \
        $ROOT/python_modules/libraries/dagster-docker \
        python_modules/libraries/

echo -e "--- \033[32m:docker: Building Docker images\033[0m"
docker-compose build \
    --build-arg WEBSERVER_VERSION="${WEBSERVER_VERSION}" \
    --build-arg WEBSERVER_LIBRARY_VERSION="${WEBSERVER_LIBRARY_VERSION}" \
    --build-arg USER_CODE_VERSION="${USER_CODE_VERSION}" \
    --build-arg USER_CODE_LIBRARY_VERSION="${USER_CODE_LIBRARY_VERSION}" \
    --build-arg USER_CODE_DEFINITIONS_FILE="${USER_CODE_DEFINITIONS_FILE}"
