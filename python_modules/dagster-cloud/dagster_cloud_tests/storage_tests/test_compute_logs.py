from dagster._core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster._core.test_utils import instance_for_test
from dagster_cloud.storage.compute_logs import CloudComputeLogManager


def test_cloud_compute_log_manager_configured():
    with instance_for_test(
        {
            "instance_class": {
                "module": "dagster_cloud",
                "class": "DagsterCloudAgentInstance",
            },
            "user_code_launcher": {
                "module": "dagster_cloud.workspace.user_code_launcher",
                "class": "ProcessUserCodeLauncher",
            },
            "dagster_cloud_api": {
                "url": "https://agent-api-test.dagster.cloud",
                "agent_token": "token",
            },
        }
    ) as instance:
        assert isinstance(instance.compute_log_manager, CloudComputeLogManager)


def test_cloud_compute_log_manager_configured_disabled():
    with instance_for_test(
        {
            "instance_class": {
                "module": "dagster_cloud",
                "class": "DagsterCloudAgentInstance",
            },
            "user_code_launcher": {
                "module": "dagster_cloud.workspace.user_code_launcher",
                "class": "ProcessUserCodeLauncher",
            },
            "dagster_cloud_api": {
                "url": "https://agent-api-test.dagster.cloud",
                "agent_token": "token",
            },
            "compute_logs": {
                "module": "dagster._core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            },
        }
    ) as instance:
        assert isinstance(instance.compute_log_manager, NoOpComputeLogManager)


def test_cloud_compute_log_manager_streaming():
    with instance_for_test(
        {
            "instance_class": {
                "module": "dagster_cloud",
                "class": "DagsterCloudAgentInstance",
            },
            "user_code_launcher": {
                "module": "dagster_cloud.workspace.user_code_launcher",
                "class": "ProcessUserCodeLauncher",
            },
            "dagster_cloud_api": {
                "url": "https://agent-api-test.dagster.cloud",
                "agent_token": "token",
            },
            "compute_logs": {
                "module": "dagster_cloud",
                "class": "CloudComputeLogManager",
                "config": {
                    "upload_interval": 10,
                },
            },
        }
    ) as instance:
        assert isinstance(instance.compute_log_manager, CloudComputeLogManager)
        assert instance.compute_log_manager.upload_interval == 10
