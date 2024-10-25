import pytest
from dagster_dlift.cloud_instance import DbtCloudInstance
from dlift_kitchen_sink.instance import get_environment_id, get_instance


@pytest.fixture
def instance() -> DbtCloudInstance:
    return get_instance()


@pytest.fixture
def environment_id() -> int:
    return get_environment_id()
