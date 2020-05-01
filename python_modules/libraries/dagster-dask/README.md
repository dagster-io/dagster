## dagster-dask

Check out the docs for `dagster-dask` [here](https://docs.dagster.io/docs/deploying/dask/). Also checkout other deployment options in the [deployment section](https://docs.dagster.io/docs/deploying/) of Dagster's docs.

### Python version support

Because Dask has dropped support for Python versions < 3.6, we do not test dagster-dask on
Python 2.7 or 3.5.

### Running tests

You will need a running Dask cluster:

    export PYTHON_VERSION=3.6
    ./dagster_dask_tests/dask-docker/build.sh $PYTHON_VERSION
    docker-compose -f dagster_dask_tests/dask-docker/docker-compose.yml up -d
