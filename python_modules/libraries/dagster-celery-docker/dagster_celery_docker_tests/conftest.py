import os
from pathlib import Path

import boto3
import pytest
from dagster._core.test_utils import environ
from dagster_test.fixtures import docker_compose_cm, network_name_from_yml

IS_BUILDKITE = os.getenv("BUILDKITE") is not None
compose_file = Path(__file__).parent / "docker-compose.yml"


@pytest.fixture(scope="session")
def postgres_network():
    yield network_name_from_yml(compose_file)


@pytest.fixture(scope="session")
def hostnames():
    with docker_compose_cm(compose_file) as hostnames:
        yield hostnames


@pytest.fixture(scope="session")
def postgres_hostname(hostnames):
    yield hostnames["postgres"]


def aws_env(hostnames, from_pytest: bool):
    hostname = hostnames["s3"]
    endpoint_url_from_pytest = f"http://{hostname}:4566"
    endpoint_url_from_dagster_container = (
        endpoint_url_from_pytest if IS_BUILDKITE else "http://s3:4566"
    )
    access_key_id = "fake"
    secret_access_key = "fake"

    return {
        "AWS_ENDPOINT_URL": endpoint_url_from_pytest
        if from_pytest
        else endpoint_url_from_dagster_container,
        "AWS_ACCESS_KEY_ID": access_key_id,
        "AWS_SECRET_ACCESS_KEY": secret_access_key,
    }


@pytest.fixture(scope="session")
def aws_env_from_dagster_container(hostnames):
    yield aws_env(hostnames, from_pytest=False)


@pytest.fixture(scope="session")
def aws_env_from_pytest(hostnames):
    yield aws_env(hostnames, from_pytest=True)


@pytest.fixture(scope="session")
def bucket(aws_env_from_pytest):
    name = "dagster-scratch-80542c2"
    with environ(aws_env_from_pytest):
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="dagster-scratch-80542c2")
    yield name
