# Backcompatability Integration Tests

This test suite ensures that the branch Dagster code can successfully communicate cross-process with older Dagster code.

## Running tests locally

In order to run, the `EARLIEST_TESTED_RELEASE` environment variable needs to be set.

    - Set `EARLIEST_TESTED_RELEASE` to match the earliest release to test:
    ```bash
    export EARLIEST_TESTED_RELEASE="0.12.8"
    ```