from contextlib import contextmanager

from dagster._core.test_utils import instance_for_test
from dagster._utils.merger import merge_dicts


@contextmanager
def gen_agent_instance(
    url=None,
    token=None,
    timeout=None,
    deployment=None,
    python_logs=None,
    user_code_launcher_config=None,
    dagster_cloud_api_config=None,
    additional_config=None,
):
    with instance_for_test(
        merge_dicts(
            {
                "instance_class": {
                    "module": "dagster_cloud",
                    "class": "DagsterCloudAgentInstance",
                },
                "user_code_launcher": {
                    "module": "dagster_cloud.workspace.user_code_launcher",
                    "class": "ProcessUserCodeLauncher",
                    "config": user_code_launcher_config or {},
                },
                "dagster_cloud_api": merge_dicts(
                    {"url": url} if url else {},
                    {"agent_token": token} if token else {},
                    ({"timeout": timeout} if timeout else {}),
                    {"deployment": deployment} if deployment else {},
                    dagster_cloud_api_config or {},
                ),
            },
            {"python_logs": python_logs} if python_logs else {},
            (additional_config or {}),
        )
    ) as instance:
        yield instance
