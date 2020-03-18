## dagster-airflow

Check out the docs for `dagster-airflow` [here](https://dagster.readthedocs.io/en/latest/sections/deploying/other/airflow.html). Also checkout other deployment options in the [deployment section](https://dagster.readthedocs.io/en/latest/sections/deploying/index.html) of Dagster's docs.

## Running tests locally

From repo root

```
# select your python version
.buildkite/images/docker/test_project/build.sh 3.6.8

export DAGSTER_DOCKER_IMAGE="dagster-docker-buildkite"

pytest python_modules/libraries/dagster-airflow/dagster_airflow_tests/
```
