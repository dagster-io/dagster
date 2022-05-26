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
