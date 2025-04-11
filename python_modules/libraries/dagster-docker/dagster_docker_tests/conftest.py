import os
from contextlib import contextmanager
from pathlib import Path

import boto3
import pytest
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


@pytest.fixture(scope="session")
def aws_env(hostnames):
    region = "us-east-1"
    hostname = hostnames["s3"]
    endpoint_url_from_pytest = f"http://{hostname}:4566"
    endpoint_url_from_dagster_container = (
        endpoint_url_from_pytest if IS_BUILDKITE else "http://s3:4566"
    )
    access_key_id = "fake"
    secret_access_key = "fake"

    boto3.client(
        "s3",
        region_name=region,
        endpoint_url=endpoint_url_from_pytest,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
    ).create_bucket(Bucket="dagster-scratch-80542c2")

    yield [
        f"AWS_ENDPOINT_URL={endpoint_url_from_dagster_container}",
        f"AWS_ACCESS_KEY_ID={access_key_id}",
        f"AWS_SECRET_ACCESS_KEY={secret_access_key}",
    ]


@pytest.fixture
def docker_postgres_instance(postgres_instance):
    @contextmanager
    def _instance(overrides=None):
        with postgres_instance(overrides=overrides) as instance:
            yield instance

    return _instance
