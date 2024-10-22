from dagster_dlift.cloud_instance import DbtCloudInstance
from dlift_kitchen_sink.constants import TEST_ENV_NAME
from dlift_kitchen_sink.instance import get_instance


def test_cloud_instance() -> None:
    """Test that we can create a DbtCloudInstance and verify connections successfully."""
    instance = get_instance()
    assert isinstance(instance, DbtCloudInstance)

    instance.verify_connections()


def test_get_test_env() -> None:
    """Test that we can get the test environment ID."""
    instance = get_instance()
    assert instance.get_environment_id_by_name(TEST_ENV_NAME)
