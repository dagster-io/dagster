# Backcompatability Integration Tests

This test suite ensures that the branch Dagster code can successfully communicate cross-process with older Dagster code.

## Running tests locally

Three environment variables need to be set: `DAGSTER_EARLIEST_RELEASE`, `DAGIT_DOCKERFILE` and `USER_CODE_DOCKERFILE`.

    - Set `DAGSTER_EARLIEST_RELEASE` to match the earliest release to test:
    ```bash
    export DAGSTER_EARLIEST_RELEASE="0.12.4"
    ```

    - If running with dagit from release and user code deployment from source:
    ```bash
    export DAGIT_DOCKERFILE="./Dockerfile_dagit_release"
    export USER_CODE_DOCKERFILE="./Dockerfile_user_code_source"
    ```

    - If running with dagit from source and user code deployment from release:
    ```bash
    export DAGIT_DOCKERFILE="./Dockerfile_dagit_source"
    export USER_CODE_DOCKERFILE="./Dockerfile_user_code_release"
    ```