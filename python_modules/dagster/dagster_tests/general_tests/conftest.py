import os
import subprocess

import pytest
from dagster_test.dagster_core_docker_buildkite import (
    build_and_tag_test_image,
    test_project_docker_image,
)

IS_BUILDKITE = os.getenv('BUILDKITE') is not None


@pytest.fixture(scope='session', autouse=True)
def unset_dagster_home():
    old_env = os.getenv('DAGSTER_HOME')
    if old_env is not None:
        del os.environ['DAGSTER_HOME']
    yield
    if old_env is not None:
        os.environ['DAGSTER_HOME'] = old_env


@pytest.fixture(scope='session')
def dagster_docker_image():
    docker_image = test_project_docker_image()

    if not IS_BUILDKITE:
        # Being conservative here when first introducing this. This could fail
        # if the Docker daemon is not running, so for now we just skip the tests using this
        # fixture if the build fails, and warn with the output from the build command
        try:
            build_and_tag_test_image(docker_image)
        except subprocess.CalledProcessError as exc_info:
            pytest.skip(
                "Skipped container tests due to a failure when trying to build the image. "
                "Most likely, the docker deamon is not running.\n"
                "Output:\n{}".format(exc_info.output.decode())
            )

    return docker_image
