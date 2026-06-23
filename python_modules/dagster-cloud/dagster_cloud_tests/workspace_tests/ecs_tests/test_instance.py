import tempfile
import time
from contextlib import contextmanager
from unittest import mock

import boto3
import moto
import pytest
from dagster import DagsterRunStatus
from dagster._config import process_config, resolve_to_config_type
from dagster._core.launcher.base import WorkerStatus
from dagster._core.storage.tags import RUN_WORKER_ID_TAG
from dagster._core.test_utils import create_run_for_test, environ, instance_for_test
from dagster._serdes import ConfigurableClassData
from dagster._utils.merger import merge_dicts
from dagster_aws.ecs import EcsRunLauncher
from dagster_cloud.execution.monitoring import CloudRunWorkerStatus
from dagster_cloud.workspace.ecs import EcsUserCodeLauncher
from dagster_cloud.workspace.ecs.client import (
    DEFAULT_ECS_GRACE_PERIOD,
    DEFAULT_ECS_TIMEOUT,
    Service,
)
from dagster_cloud.workspace.user_code_launcher import UserCodeLauncherEntry
from dagster_cloud.workspace.user_code_launcher.utils import (
    deterministic_label_for_location,
    get_grpc_server_env,
)
from dagster_cloud_cli.core.workspace import CodeLocationDeployData


@pytest.fixture
def secrets_manager():
    with moto.mock_aws():
        yield boto3.client("secretsmanager")


@contextmanager
def ecs_instance(monkeypatch, user_code_launcher_overrides=None, overrides=None):
    monkeypatch.setenv("CLUSTER", "fake-cluster")
    monkeypatch.setenv("SUBNET1", "fake-subnet-1")
    monkeypatch.setenv("SUBNET2", "fake-subnet-2")

    with instance_for_test(
        {
            "instance_class": {
                "module": "dagster_cloud",
                "class": "DagsterCloudAgentInstance",
            },
            "user_code_launcher": {
                "module": "dagster_cloud.workspace.ecs",
                "class": "EcsUserCodeLauncher",
                "config": merge_dicts(
                    {
                        "cluster": {
                            "env": "CLUSTER",
                        },
                        "subnets": [
                            {"env": "SUBNET1"},
                            {"env": "SUBNET2"},
                        ],
                        "service_discovery_namespace_id": "fake-namespace",
                        "execution_role_arn": "fake-role",
                        "log_group": "fake-log-group",
                    },
                    user_code_launcher_overrides or {},
                ),
            },
            "dagster_cloud_api": {
                "url": "http://localhost:2874",
                "agent_token": "FAKE_TOKEN",
                "deployment": "sandbox",
            },
            "compute_logs": {
                "module": "dagster._core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            },
            **(overrides or {}),
        }
    ) as instance:
        yield instance


@moto.mock_aws()
def test_default_ecs_instance(monkeypatch):
    with ecs_instance(monkeypatch) as instance:
        assert isinstance(instance.user_code_launcher, EcsUserCodeLauncher)
        assert isinstance(instance.user_code_launcher.inst_data, ConfigurableClassData)
        assert "fake-subnet-1" in instance.user_code_launcher.subnets
        assert "fake-subnet-2" in instance.user_code_launcher.subnets
        assert len(instance.user_code_launcher.subnets) == 2
        assert not instance.user_code_launcher.task_role_arn
        assert not instance.user_code_launcher.security_group_ids
        assert instance.user_code_launcher.secrets == []
        assert instance.user_code_launcher.secrets_tag is None
        assert instance.user_code_launcher.env_vars == []
        assert instance.user_code_launcher.client.timeout == DEFAULT_ECS_TIMEOUT
        assert instance.user_code_launcher.client.grace_period == DEFAULT_ECS_GRACE_PERIOD

        assert not instance.user_code_launcher._get_enable_ecs_exec()  # noqa


@moto.mock_aws()
def test_timeouts_override(monkeypatch):
    with ecs_instance(monkeypatch, {"ecs_timeout": 100, "ecs_grace_period": 50}) as instance:
        assert instance.user_code_launcher.client.timeout == 100
        assert instance.user_code_launcher.client.grace_period == 50


@moto.mock_aws()
def test_ecs_exec_override(monkeypatch):
    with ecs_instance(monkeypatch, {"enable_ecs_exec": True}) as instance:
        assert instance.user_code_launcher._get_enable_ecs_exec()  # noqa


@moto.mock_aws()
def test_env_vars_override(monkeypatch):
    env_vars = ["FOO_ENV_VAR", "BAR_ENV_VAR=BAR_VALUE"]
    with ecs_instance(monkeypatch, {"env_vars": env_vars}) as instance:
        assert instance.user_code_launcher.env_vars == env_vars
        assert instance.run_launcher.env_vars == env_vars


@moto.mock_aws()
def test_secrets_override(monkeypatch):
    secrets = [
        {
            "name": "FOO",
            "valueFrom": "arn:aws:secretsmanager:us-west-2:111122223333:secret:aes128-1a2b3c",
        },
        {
            "name": "BAR",
            "valueFrom": "arn:aws:secretsmanager:us-west-2:111122223333:secret:aes192-4D5e6F",
        },
    ]
    with ecs_instance(monkeypatch, {"secrets": secrets, "secrets_tag": "my_tag"}) as instance:
        assert instance.user_code_launcher.secrets == secrets
        assert instance.user_code_launcher.secrets_tag == "my_tag"
        assert isinstance(instance.user_code_launcher.inst_data, ConfigurableClassData)

        assert instance.run_launcher.secrets == secrets
        assert instance.run_launcher.secrets_tags == ["my_tag"]

    with ecs_instance(monkeypatch, {"task_role_arn": "fake-role"}) as instance:
        assert instance.user_code_launcher.task_role_arn == "fake-role"

    with ecs_instance(monkeypatch, {"security_group_ids": ["fake-sg"]}) as instance:
        assert instance.user_code_launcher.security_group_ids == ["fake-sg"]


@moto.mock_aws()
def test_repository_credentials_override(monkeypatch):
    repository_credentials_arn = (
        "arn:aws:secretsmanager:us-west-2:111122223333:secret:fake-registry-creds-AbCdEf"
    )
    with ecs_instance(
        monkeypatch, {"repository_credentials": repository_credentials_arn}
    ) as instance:
        assert instance.user_code_launcher.repository_credentials == repository_credentials_arn
        assert instance.run_launcher.repository_credentials == repository_credentials_arn

        run_launcher_kwargs = instance.user_code_launcher._run_launcher_kwargs()  # noqa: SLF001
        assert (
            run_launcher_kwargs["task_definition"]["repository_credentials"]
            == repository_credentials_arn
        )


@moto.mock_aws()
def test_empty_secrets(monkeypatch):
    with ecs_instance(monkeypatch, {"secrets": [], "secrets_tag": None}) as instance:
        assert instance.user_code_launcher.secrets == []
        assert instance.user_code_launcher.secrets_tag is None
        assert instance.run_launcher.secrets == []
        assert instance.run_launcher.secrets_tags == []


@moto.mock_aws()
def test_timeout_debug_info(monkeypatch):
    with ecs_instance(monkeypatch) as instance:
        fake_client = mock.MagicMock()
        fake_client.get_task_logs = mock.MagicMock(return_value=["Hi", "these", "are", "logs"])

        instance.user_code_launcher.client = fake_client

        timeout_debug_info = instance.user_code_launcher._get_update_failure_debug_info(  # noqa: SLF001
            "my_task_arn"
        )

        assert (
            timeout_debug_info
            == "Task logs:\nHi\nthese\nare\nlogs\n\nFor more information about the failure, check"
            " the ECS console for logs for task my_task_arn in cluster fake-cluster."
        )


@moto.mock_aws()
def test_transient_startup_failure_health_check(monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        with ecs_instance(
            monkeypatch,
            overrides={
                "run_storage": {
                    "module": "dagster._core.storage.runs",
                    "class": "SqliteRunStorage",
                    "config": {"base_dir": temp_dir},
                },
            },
        ) as instance:
            fake_ecs = mock.MagicMock()

            task_arn = "arn:aws:ecs:us-west-2:657821118200:task/serverless-agent-5bae4d6a-b58f-392d-b7ab-92c53d938193-Cluster/d12fcac0355f4bb3ae768653d61cc31e"

            # taken from a real transient startup failure with some irrelevant keys stripped out
            fake_ecs.describe_tasks = mock.MagicMock(
                return_value={
                    "tasks": [
                        {
                            "containers": [
                                {
                                    "containerArn": "arn:aws:ecs:us-west-2:657821118200:container/serverless-agent-5bae4d6a-b58f-392d-b7ab-92c53d938193-Cluster/d12fcac0355f4bb3ae768653d61cc31e/8d008fad-e39f-4fd6-a4f5-324a7c2f0eff",
                                    "taskArn": "arn:aws:ecs:us-west-2:657821118200:task/serverless-agent-5bae4d6a-b58f-392d-b7ab-92c53d938193-Cluster/d12fcac0355f4bb3ae768653d61cc31e",
                                    "name": "DatadogAgent",
                                    "image": "public.ecr.aws/datadog/agent:latest",
                                    "lastStatus": "STOPPED",
                                    "healthStatus": "UNKNOWN",
                                    "cpu": "0",
                                },
                                {
                                    "containerArn": "arn:aws:ecs:us-west-2:657821118200:container/serverless-agent-5bae4d6a-b58f-392d-b7ab-92c53d938193-Cluster/d12fcac0355f4bb3ae768653d61cc31e/c40d570e-0243-4bde-a760-e965ebf938a8",
                                    "taskArn": task_arn,
                                    "name": "dagster",
                                    "image": "657821118200.dkr.ecr.us-west-2.amazonaws.com/fake-image-29f7eac-5070495852-1",
                                    "lastStatus": "STOPPED",
                                    "healthStatus": "UNKNOWN",
                                    "cpu": "0",
                                },
                            ],
                            "cpu": "4096",
                            "desiredStatus": "STOPPED",
                            "enableExecuteCommand": False,
                            "group": "family:fake_task_definition_9972342a",
                            "healthStatus": "UNKNOWN",
                            "lastStatus": "STOPPED",
                            "launchType": "FARGATE",
                            "platformVersion": "1.4.0",
                            "platformFamily": "Linux",
                            "stopCode": "TaskFailedToStart",
                            "stoppedReason": (
                                "Timeout waiting for network interface provisioning to complete."
                            ),
                            "tags": [],
                            "taskArn": "arn:aws:ecs:us-west-2:657821118200:task/serverless-agent-5bae4d6a-b58f-392d-b7ab-92c53d938193-Cluster/d12fcac0355f4bb3ae768653d61cc31e",
                            "taskDefinitionArn": "arn:aws:ecs:us-west-2:657821118200:task-definition/fun-fake-group-dagster-cloud_9972342a:1966",
                            "version": 4,
                            "ephemeralStorage": {"sizeInGiB": 128},
                        }
                    ],
                    "failures": [],
                }
            )

            run_launcher = instance.run_launcher
            run_launcher.ecs = fake_ecs

            starting_run = create_run_for_test(
                instance,
                job_name="foo_job",
                tags={
                    RUN_WORKER_ID_TAG: "abcde",
                    "ecs/task_arn": task_arn,
                    "ecs/cluster": "serverless-agent-5bae4d6a-b58f-392d-b7ab-92c53d938193-Cluster",
                },
                status=DagsterRunStatus.STARTING,
            )

            health_check = CloudRunWorkerStatus.from_check_run_health_result(
                starting_run.run_id, run_launcher.check_run_worker_health(starting_run)
            )
            assert health_check.status_type == WorkerStatus.FAILED
            assert health_check.transient
            assert health_check.run_worker_id == "abcde"

            # started run is not considered transient
            started_run = create_run_for_test(
                instance,
                job_name="foo_job",
                tags={
                    RUN_WORKER_ID_TAG: "abcde",
                    "ecs/task_arn": task_arn,
                    "ecs/cluster": "serverless-agent-5bae4d6a-b58f-392d-b7ab-92c53d938193-Cluster",
                },
                status=DagsterRunStatus.STARTED,
            )

            health_check = CloudRunWorkerStatus.from_check_run_health_result(
                started_run.run_id, run_launcher.check_run_worker_health(started_run)
            )
            assert not health_check.transient


@moto.mock_aws()
def test_cannot_set_system_tags(monkeypatch):
    with ecs_instance(
        monkeypatch,
        {
            "server_ecs_tags": [
                {
                    "key": "dagster/deployment_name",
                    "value": "NOPE",
                },
                {
                    "key": "dagster/grpc_server",
                },
            ],
        },
    ) as instance:
        instance.user_code_launcher._wait_for_dagster_server_process = mock.MagicMock(  # noqa: SLF001
            return_value=None
        )  # fmt: skip

        metadata_with_container_context = CodeLocationDeployData(
            image="foo_image",
            python_file="repo.py",
        )

        with pytest.raises(Exception, match="Cannot override system ECS tags"):
            instance.user_code_launcher._start_new_server_spinup(  # noqa: SLF001
                deployment_name="sandbox",
                location_name="test_location",
                desired_entry=UserCodeLauncherEntry(metadata_with_container_context, time.time()),
            )


@moto.mock_aws()
def test_repository_credentials_from_launcher_spinup(monkeypatch):
    repository_credentials_arn = (
        "arn:aws:secretsmanager:us-west-2:111122223333:secret:fake-registry-creds-AbCdEf"
    )
    with ecs_instance(
        monkeypatch, {"repository_credentials": repository_credentials_arn}
    ) as instance:
        fake_client = mock.MagicMock()
        fake_client.create_service = mock.MagicMock(
            return_value=Service(
                client=fake_client,
                arn="arn:aws:ecs::us-west-2:123456:service/my-cluster-name/my-service-name",
            )
        )

        instance.user_code_launcher.client = fake_client

        instance.user_code_launcher._wait_for_dagster_server_process = mock.MagicMock(  # noqa: SLF001
            return_value=None
        )  # fmt: skip

        metadata = CodeLocationDeployData(
            image="foo_image",
            python_file="repo.py",
        )

        instance.user_code_launcher._start_new_server_spinup(  # noqa: SLF001
            deployment_name="sandbox",
            location_name="test_location",
            desired_entry=UserCodeLauncherEntry(metadata, time.time()),
        )

        instance.user_code_launcher.client.create_service.assert_called_once()
        _args, kwargs = instance.user_code_launcher.client.create_service.call_args
        assert kwargs["repository_credentials"] == repository_credentials_arn

    # container_context value overrides launcher-level value
    container_context_creds = (
        "arn:aws:secretsmanager:us-west-2:111122223333:secret:override-creds-XyZ"
    )
    with ecs_instance(
        monkeypatch, {"repository_credentials": repository_credentials_arn}
    ) as instance:
        fake_client = mock.MagicMock()
        fake_client.create_service = mock.MagicMock(
            return_value=Service(
                client=fake_client,
                arn="arn:aws:ecs::us-west-2:123456:service/my-cluster-name/my-service-name",
            )
        )

        instance.user_code_launcher.client = fake_client

        instance.user_code_launcher._wait_for_dagster_server_process = mock.MagicMock(  # noqa: SLF001
            return_value=None
        )  # fmt: skip

        metadata = CodeLocationDeployData(
            image="foo_image",
            python_file="repo.py",
            container_context={
                "ecs": {"repository_credentials": container_context_creds},
            },
        )

        instance.user_code_launcher._start_new_server_spinup(  # noqa: SLF001
            deployment_name="sandbox",
            location_name="test_location",
            desired_entry=UserCodeLauncherEntry(metadata, time.time()),
        )

        _args, kwargs = instance.user_code_launcher.client.create_service.call_args
        assert kwargs["repository_credentials"] == container_context_creds


@moto.mock_aws()
def test_config_from_container_context(monkeypatch, secrets_manager):
    foo_tagged_secret = secrets_manager.create_secret(
        Name="foo_tagged_secret",
        SecretString="foo_tagged_value",
        Tags=[{"Key": "my_tag", "Value": "foo"}],
    )

    bar_tagged_secret = secrets_manager.create_secret(
        Name="bar_tagged_secret",
        SecretString="bar_tagged_value",
        Tags=[{"Key": "additional_tag", "Value": "bar"}],
    )

    foo_secret_arn = "arn:aws:secretsmanager:us-west-2:111122223333:secret:aes128-1a2b3c"

    hello_secret_arn = "arn:aws:secretsmanager:us-east-1:123456789012:secret:HELLO-AbCdEf:token::"

    instance_secrets = [
        {"name": "FOO", "valueFrom": foo_secret_arn},
    ]
    instance_env_vars = ["FOO_ENV_VAR"]
    with ecs_instance(
        monkeypatch,
        {
            "secrets": instance_secrets,
            "secrets_tag": "my_tag",
            "env_vars": instance_env_vars,
            "runtime_platform": {"operatingSystemFamily": "LINUX"},
            "mount_points": [
                {
                    "sourceVolume": "myEfsVolume",
                    "containerPath": "/mount/efs",
                    "readOnly": True,
                }
            ],
            "volumes": [
                {
                    "name": "myEfsVolume",
                    "efsVolumeConfiguration": {
                        "fileSystemId": "fs-1234",
                        "rootDirectory": "/path/to/my/data",
                    },
                }
            ],
            "server_sidecar_containers": [
                {
                    "name": "DatadogAgent",
                    "image": "public.ecr.aws/datadog/agent:latest",
                    "environment": [
                        {"name": "ECS_FARGATE", "value": "true"},
                    ],
                }
            ],
            "run_sidecar_containers": [
                {
                    "name": "busyrun",
                    "image": "busybox:latest",
                }
            ],
            "server_ecs_tags": [
                {
                    "key": "FOO",  # no value
                }
            ],
            "run_ecs_tags": [{"key": "ABC", "value": "DEF"}],  # with value
            "server_health_check": {
                "command": ["HELLO"],
            },
        },
    ) as instance:
        fake_client = mock.MagicMock()
        fake_client.create_service = mock.MagicMock(
            return_value=Service(
                client=fake_client,
                arn="arn:aws:ecs::us-west-2:123456:service/my-cluster-name/my-service-name",
            )
        )

        instance.user_code_launcher.client = fake_client

        instance.user_code_launcher._wait_for_dagster_server_process = mock.MagicMock(  # noqa: SLF001
            return_value=None
        )  # fmt: skip

        metadata_with_container_context = CodeLocationDeployData(
            image="foo_image",
            python_file="repo.py",
            container_context={
                "ecs": {
                    "secrets": [
                        {
                            "name": "HELLO",
                            "valueFrom": hello_secret_arn,
                        }
                    ],
                    "secrets_tags": ["additional_tag"],
                    "env_vars": ["BAR_ENV_VAR=BAR_VALUE"],
                    "server_resources": {
                        "cpu": "1024",
                        "memory": "2048",
                    },
                    "task_role_arn": "fake-task-role-arn",
                    "execution_role_arn": "fake-execution-role-arn",
                    "runtime_platform": {"operatingSystemFamily": "WINDOWS_SERVER_2019_FULL"},
                    "mount_points": [
                        {
                            "sourceVolume": "myOtherEfsVolume",
                            "containerPath": "/mount/other/efs",
                            "readOnly": True,
                        }
                    ],
                    "volumes": [
                        {
                            "name": "myOtherEfsVolume",
                            "efsVolumeConfiguration": {
                                "fileSystemId": "fs-5678",
                                "rootDirectory": "/path/to/my/other/data",
                            },
                        },
                    ],
                    "server_sidecar_containers": [
                        {
                            "name": "OtherServerAgent",
                            "image": "public.ecr.aws/other/agent:latest",
                        }
                    ],
                    "run_sidecar_containers": [
                        {
                            "name": "OtherRunAgent",
                            "image": "otherrun:latest",
                        }
                    ],
                    "server_ecs_tags": [{"key": "BAZ", "value": "QUUX"}],
                    "run_ecs_tags": [
                        {
                            "key": "GHI",
                        }
                    ],
                    "repository_credentials": "fake-secret-arn",
                    "server_health_check": {
                        "command": ["CMD-SHELL", "curl -f http://localhost/ || exit 1"],
                        "interval": 30,
                        "timeout": 5,
                        "retries": 3,
                        "startPeriod": 0,
                    },
                }
            },
        )

        server_timestamp = time.time()

        with environ({"FOO_ENV_VAR": "FOO_VALUE"}):
            instance.user_code_launcher._start_new_server_spinup(  # noqa: SLF001
                deployment_name="sandbox",
                location_name="test_location",
                desired_entry=UserCodeLauncherEntry(
                    metadata_with_container_context, server_timestamp
                ),
            )

        instance.user_code_launcher.client.create_service.assert_called_once()
        _args, kwargs = instance.user_code_launcher.client.create_service.call_args

        expected_kwargs = {
            "image": "foo_image",
            "command": metadata_with_container_context.get_grpc_server_command(),
            "env": {
                "FOO_ENV_VAR": "FOO_VALUE",
                "BAR_ENV_VAR": "BAR_VALUE",
                **get_grpc_server_env(
                    metadata_with_container_context,
                    4000,
                    location_name="test_location",
                    instance_ref=instance.ref_for_deployment(
                        "sandbox",
                    ),
                ),
            },
            "tags": {
                "dagster/location_name": "testlocation",
                "dagster/deployment_name": "sandbox",
                "dagster/location_hash": deterministic_label_for_location(
                    "sandbox", "test_location"
                ),
                "dagster/grpc_server": "1",
                "dagster/agent_id": instance.instance_uuid,
                "FOO": None,
                "BAZ": "QUUX",
                "dagster/server_timestamp": str(server_timestamp),
            },
            "task_role_arn": "fake-task-role-arn",
            "execution_role_arn": "fake-execution-role-arn",
            "secrets": {
                "FOO": foo_secret_arn,
                "HELLO": hello_secret_arn,
                "bar_tagged_secret": bar_tagged_secret["ARN"],
                "foo_tagged_secret": foo_tagged_secret["ARN"],
            },
            "cpu": "1024",
            "memory": "2048",
            "runtime_platform": {"operatingSystemFamily": "WINDOWS_SERVER_2019_FULL"},
            "mount_points": [
                {
                    "sourceVolume": "myOtherEfsVolume",
                    "containerPath": "/mount/other/efs",
                    "readOnly": True,
                },
                {
                    "sourceVolume": "myEfsVolume",
                    "containerPath": "/mount/efs",
                    "readOnly": True,
                },
            ],
            "volumes": [
                {
                    "name": "myOtherEfsVolume",
                    "efsVolumeConfiguration": {
                        "fileSystemId": "fs-5678",
                        "rootDirectory": "/path/to/my/other/data",
                    },
                },
                {
                    "name": "myEfsVolume",
                    "efsVolumeConfiguration": {
                        "fileSystemId": "fs-1234",
                        "rootDirectory": "/path/to/my/data",
                    },
                },
            ],
            "sidecars": [
                {
                    "name": "OtherServerAgent",
                    "image": "public.ecr.aws/other/agent:latest",
                },
                {
                    "name": "DatadogAgent",
                    "image": "public.ecr.aws/datadog/agent:latest",
                    "environment": [
                        {"name": "ECS_FARGATE", "value": "true"},
                    ],
                },
            ],
            "repository_credentials": "fake-secret-arn",
            "health_check": {
                "command": ["CMD-SHELL", "curl -f http://localhost/ || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 0,
            },
        }

        differing_keys = [key for key, value in expected_kwargs.items() if kwargs[key] != value]

        assert not differing_keys, (
            f"Differing keys: {differing_keys} between {kwargs} and {expected_kwargs}"
        )

        run_launcher_kwargs = instance.user_code_launcher._run_launcher_kwargs()  # noqa

        process_result = process_config(
            resolve_to_config_type(EcsRunLauncher.config_type()),
            run_launcher_kwargs,
        )
        assert process_result.success, str(process_result.errors)

        assert run_launcher_kwargs == {
            "task_definition": {
                "log_group": "fake-log-group",
                "execution_role_arn": "fake-role",
                "requires_compatibilities": ["FARGATE"],
                "runtime_platform": {"operatingSystemFamily": "LINUX"},
                "mount_points": [
                    {
                        "sourceVolume": "myEfsVolume",
                        "containerPath": "/mount/efs",
                        "readOnly": True,
                    }
                ],
                "volumes": [
                    {
                        "name": "myEfsVolume",
                        "efsVolumeConfiguration": {
                            "fileSystemId": "fs-1234",
                            "rootDirectory": "/path/to/my/data",
                        },
                    }
                ],
                "sidecar_containers": [
                    {
                        "name": "busyrun",
                        "image": "busybox:latest",
                    }
                ],
            },
            "secrets": instance_secrets,
            "secrets_tag": "my_tag",
            "container_name": "dagster",
            "env_vars": ["FOO_ENV_VAR"],
            "use_current_ecs_task_config": False,
            "run_resources": {},
            "run_task_kwargs": {
                "cluster": "fake-cluster",
                "networkConfiguration": fake_client.network_configuration,
                "launchType": "FARGATE",
            },
            "run_ecs_tags": [
                {"key": "ABC", "value": "DEF"},
            ],
            "task_definition_prefix": "dagsterrun",
        }
