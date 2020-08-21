"""Test fixtures for dagster-airflow.

These make very heavy use of fixture dependency and scope. If you're unfamiliar with pytest
fixtures, read: https://docs.pytest.org/en/latest/fixture.html.
"""
# pylint doesn't understand the way that pytest constructs fixture dependencies
# pylint: disable=redefined-outer-name, unused-argument
import os
import shutil
import tempfile

import docker
import pytest
from dagster_test.test_project import build_and_tag_test_image, test_project_docker_image

from dagster.utils import load_yaml_from_path, mkdir_p

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@pytest.fixture(scope="module")
def airflow_home():
    """Check that AIRFLOW_HOME is set, and return it"""
    airflow_home_dir = os.getenv("AIRFLOW_HOME")
    assert airflow_home_dir, "No AIRFLOW_HOME set -- is airflow installed?"
    airflow_home_dir = os.path.abspath(os.path.expanduser(airflow_home_dir))

    return airflow_home_dir


@pytest.fixture(scope="module")
def clean_airflow_home(airflow_home):
    """Ensure that the existing contents of AIRFLOW_HOME do not interfere with test."""

    airflow_dags_path = os.path.join(airflow_home, "dags")

    # Ensure Airflow DAGs folder exists
    if not os.path.exists(airflow_dags_path):
        os.makedirs(airflow_dags_path)

    tempdir_path = tempfile.mkdtemp()

    # Move existing DAGs aside for test
    dags_files = os.listdir(airflow_dags_path)
    for dag_file in dags_files:
        shutil.move(os.path.join(airflow_dags_path, dag_file), tempdir_path)

    yield

    # Clean up DAGs produced by test
    shutil.rmtree(airflow_dags_path)
    os.makedirs(airflow_dags_path)

    # Move original DAGs back
    file_paths = os.listdir(tempdir_path)
    for file_path in file_paths:
        shutil.move(
            os.path.join(tempdir_path, file_path), os.path.join(airflow_dags_path, file_path)
        )

    shutil.rmtree(tempdir_path)


@pytest.fixture(scope="session")
def dagster_docker_image():
    docker_image = test_project_docker_image()

    if not IS_BUILDKITE:
        try:
            client = docker.from_env()
            client.images.get(docker_image)
            print(  # pylint: disable=print-call
                "Found existing image tagged {image}, skipping image build. To rebuild, first run: "
                "docker rmi {image}".format(image=docker_image)
            )
        except docker.errors.ImageNotFound:
            build_and_tag_test_image(docker_image)

    return docker_image


@pytest.fixture(scope="module")
def dags_path(airflow_home):
    """Abspath to the magic Airflow DAGs folder."""
    path = os.path.join(airflow_home, "dags", "")
    mkdir_p(os.path.abspath(path))
    return path


@pytest.fixture(scope="module")
def plugins_path(airflow_home):
    """Abspath to the magic Airflow plugins folder."""
    path = os.path.join(airflow_home, "plugins", "")
    mkdir_p(os.path.abspath(path))
    return path


@pytest.fixture(scope="module")
def run_config(s3_bucket, test_repo_path):
    env_dict = load_yaml_from_path(os.path.join(test_repo_path, "env.yaml"))
    env_dict["storage"] = {"s3": {"s3_bucket": s3_bucket}}
    yield env_dict


@pytest.fixture(scope="session")
def s3_bucket():
    yield "dagster-scratch-80542c2"


@pytest.fixture(scope="session")
def gcs_bucket():
    yield "dagster-scratch-ccdfe1e"
