from dagster_dlift.client import UnscopedDbtCloudClient
from dlift_kitchen_sink.instance import get_environment_id, get_unscoped_client


def test_cloud_instance() -> None:
    """Test that we can create a DbtCloudInstance and verify connections successfully."""
    instance = get_unscoped_client()
    assert isinstance(instance, UnscopedDbtCloudClient)

    instance.verify_connections()


def test_get_test_env() -> None:
    """Test that we can get the test environment ID."""
    assert get_environment_id()
