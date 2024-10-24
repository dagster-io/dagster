from dagster_dlift.cloud_instance import DbtCloudInstance
from dlift_kitchen_sink.instance import get_instance


def test_cloud_instance() -> None:
    """Test that we can create a DbtCloudInstance and verify connections successfully."""
    instance = get_instance()
    assert isinstance(instance, DbtCloudInstance)

    instance.verify_connections()
