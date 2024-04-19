import pytest
from dagster._core.errors import DagsterImportClassFromCodePointerError
from dagster._core.test_utils import instance_for_test
from dagster_cloud.instance import DagsterCloudAgentInstance  # type: ignore


def test_backcompat_no_dagster_plus():
    with instance_for_test(
        overrides={
            "instance_class": {
                "module": "dagster_cloud.instance",
                "class": "DagsterCloudAgentInstance",
            }
        }
    ) as instance:
        assert instance.get_ref().custom_instance_class_data.module_name == "dagster_cloud.instance"
        assert isinstance(instance, DagsterCloudAgentInstance)

    with pytest.raises(
        DagsterImportClassFromCodePointerError, match="Couldn't import module dagster_plus.instance"
    ):
        with instance_for_test(
            overrides={
                "instance_class": {
                    "module": "dagster_plus.instance",
                    "class": "DagsterCloudAgentInstance",
                }
            }
        ) as instance:
            pass
