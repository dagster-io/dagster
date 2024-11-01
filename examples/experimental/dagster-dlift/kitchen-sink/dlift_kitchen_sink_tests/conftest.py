import pytest
from dagster_dlift.client import DbtCloudClient
from dlift_kitchen_sink.instance import get_environment_id, get_instance, get_project_id


@pytest.fixture
def instance() -> DbtCloudClient:
    return get_instance()


@pytest.fixture
def environment_id() -> int:
    return get_environment_id()


@pytest.fixture
def project_id() -> int:
    return get_project_id()
