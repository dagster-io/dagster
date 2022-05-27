# Backcompatability Integration Tests

This test suite ensures that the branch Dagster code can successfully communicate cross-process with older Dagster code.

## Running tests locally

In order to run, the `EARLIEST_TESTED_RELEASE` environment variable needs to be set.

- Set `EARLIEST_TESTED_RELEASE` to match the earliest release to test:
```bash
export EARLIEST_TESTED_RELEASE="0.12.8"
```


If you are on MacOS, ensure you have docker running

From `integration_tests/test_suites/backcompat-test-suite` run any of the following commands
* `pytest -m dagit-latest-release -xvv -ff tests/test_backcompat.py`
* `pytest -m dagit-earliest-release -xvv -ff tests/test_backcompat.py`
* `pytest -m user-code-latest-release -xvv -ff tests/test_backcompat.py`
* `pytest -m user-code-earliest-release -xvv -ff tests/test_backcompat.py`
* `tox dagit-latest-release`
* `tox dagit-earliest-release`
* `tox user-code-latest-release`
* `tox user-code-earliest-release`


where:
* dagit-latest-release: Dagit on most recent release and user code on current branch
* dagit-earliest-release: Dagit on earliest release to maintain backcompat for, and user code on current branch
* user-code-latest-release: Dagit on current branch and user code on latest minor release
* user-code-earliest-release: Dagit on current branch and user code on earliest release to maintain backcompat for


## Debugging tips

Most of the tests are run in subprocesses and inside docker containers, so if you're having trouble debugging
in this setup, you can emulate what the test is doing using two clones of dagster

1. create a new virtualenv running the same python version you usually use
2. clone dagster into a new folder. we'll call it `dagster_2` here
3. activate your new virtual env and cd into `dagster_2`
4. checkout the version of dagster you want to test against (ie. checkout release/0.14.17)
5. `make dev install` in `dagster_2`
6.

in user code run a grpc server (see docs) with python file as repo.py in integration tests
in dagster 2 update workspace to point at host and port of the grpc server you just started
in dagster_2 run dagit -w path to integration test workspace yaml

in user code start a python interpreter
import dagster_graphql dagster graphql client
setup client with host and port 
client.submit job