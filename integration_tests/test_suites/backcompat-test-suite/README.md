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

### Option 1:
To view the logs of the docker containers that are spun up during testing, you'll need to comment out a line in the
test suite so that the containers are not removed. In `tests/test_backcompat.py` in `docker_service_up()` the final lines will be
```python
    try:
        yield
    finally:
        subprocess.check_output(["docker-compose", "-f", docker_compose_file, "stop"])
        subprocess.check_output(["docker-compose", "-f", docker_compose_file, "rm", "-f"])
```
change them to
```python
    try:
        yield
    finally:
        subprocess.check_output(["docker-compose", "-f", docker_compose_file, "stop"])
      #  subprocess.check_output(["docker-compose", "-f", docker_compose_file, "rm", "-f"])
```
When you run the backcompat test, you can view the docker containers using `docker container ls -a` and view the logs for the container in
question using `docker logs <CONTAINER ID>`

### Option 2:
Most of the tests are run in subprocesses and inside docker containers, so if you're having trouble debugging
in this setup, you can emulate what the test is doing using two clones of dagster

1. create a new virtualenv running the same python version you usually use
2. clone dagster into a new folder. we'll call it `dagster_2` here. We'll call your normal clone of dagster that's on your user branch `dagster`
3. activate your new virtual env and cd into `dagster_2`
4. checkout the version of dagster you want to test against (ie. checkout release/0.14.17)
5. `make dev install` in `dagster_2`
6. In `dagster` start up a grpc server pointing at `repo.py` in `dagit_service`: `dagster api grpc --python-file dagit_service/repo.py --host 0.0.0.0 --port 4266`
7. In `dagster_2` update `integration_tests/test_suites/backcompat-test-suite/dagit_service/workspace.yaml` to tell dagit that the grpc service host is localhost and the port is 4266
8. In `dagster_2` run dagit: `dagit -w integration_tests/test_suites/backcompat-test-suite/dagit_service/workspace.yaml`
9. In `dagster` open a python interpreter and run the following
```python
from dagster_graphql import DagsterGraphQLClient

client = DagsterGraphQLClient("localhost", port_number=3000)
client.submit_pipeline_execution(pipeline_name="the_job", mode="default", run_config={})
```

10. You can modify the args to `submit_pipeline_execution` based on the test that you are debugging

This setup should allow you to set breakpoints in `dagster` and `dagster_2`