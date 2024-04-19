import tempfile

import yaml
from dagster._core.instance import InstanceRef
from dagster._core.test_utils import instance_for_test
from dagster._serdes import (
    ConfigurableClassData,
)
from dagster_plus.instance import DagsterCloudAgentInstance  # type: ignore
from dagster_plus.storage.compute_logs import MockCloudComputeLogStorage  # type: ignore


def test_load_instance_from_dagster_plus():
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


def test_load_instance_from_dagster_plus_module():
    with instance_for_test(
        overrides={
            "instance_class": {
                "module": "dagster_plus.instance",
                "class": "DagsterCloudAgentInstance",
            }
        }
    ) as instance:
        assert instance.get_ref().custom_instance_class_data.module_name == "dagster_cloud.instance"
        assert isinstance(instance, DagsterCloudAgentInstance)


def test_load_instance_from_ref():
    with tempfile.TemporaryDirectory() as temp_dir:
        ref = InstanceRef.from_dir(temp_dir)
        ref = ref._replace(
            compute_logs_data=ConfigurableClassData(
                module_name="dagster_cloud.storage.compute_logs",
                class_name="MockCloudComputeLogStorage",
                config_yaml=yaml.dump({"base_dir": temp_dir}, default_flow_style=False),
            )
        )
        assert isinstance(ref.compute_log_manager, MockCloudComputeLogStorage)
        with DagsterCloudAgentInstance.from_ref(ref) as instance:
            assert isinstance(instance.compute_log_manager, MockCloudComputeLogStorage)
