import pytest


@pytest.fixture(scope="session")
def s3_bucket():
    yield "dagster-scratch-80542c2"
