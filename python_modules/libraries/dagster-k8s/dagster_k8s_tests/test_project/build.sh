#! /bin/bash
ROOT=$(git rev-parse --show-toplevel)

set -ux

function cleanup {
    rm -rf $ROOT/python_modules/libraries/dagster-k8s/dagster_k8s_tests/test_project/dagster
    rm -rf $ROOT/python_modules/libraries/dagster-k8s/dagster_k8s_tests/test_project/dagster-graphql
    rm -rf $ROOT/python_modules/libraries/dagster-k8s/dagster_k8s_tests/test_project/dagit
    rm -rf $ROOT/python_modules/libraries/dagster-k8s/dagster_k8s_tests/test_project/dagster-postgres
    rm -rf $ROOT/python_modules/libraries/dagster-k8s/dagster_k8s_tests/test_project/dagster-aws
    rm -rf $ROOT/python_modules/libraries/dagster-k8s/dagster_k8s_tests/test_project/dagster-cron
    rm -rf $ROOT/python_modules/libraries/dagster-k8s/dagster_k8s_tests/test_project/dagster-gcp
    rm -rf $ROOT/python_modules/libraries/dagster-k8s/dagster_k8s_tests/test_project/dagster-k8s
    rm -rf $ROOT/python_modules/libraries/dagster-k8s/dagster_k8s_tests/test_project/examples
    set +ux
    popd
}
# ensure cleanup happens on error or normal exit
trap cleanup INT TERM EXIT ERR

# rebuild dagit before building container
pushd $ROOT && make rebuild_dagit && popd

pushd $ROOT/python_modules/libraries/dagster-k8s/dagster_k8s_tests/test_project
cp -R ../../../../dagster . && \
cp -R ../../../../dagster-graphql . && \
cp -R ../../../../dagit . && \
cp -R ../../../dagster-postgres . && \
cp -R ../../../dagster-aws . && \
cp -R ../../../dagster-cron . && \
cp -R ../../../dagster-gcp . && \
cp -R ../../../../../examples . && \
rsync -av --progress ../../../dagster-k8s . --exclude dagster_k8s_tests
\
find . -name '*.egg-info' | xargs rm -rf && \
find . -name '*.tox' | xargs rm -rf && \
find . -name 'dist' | xargs rm -rf && \
\
docker build -t dagster-k8s-demo .
