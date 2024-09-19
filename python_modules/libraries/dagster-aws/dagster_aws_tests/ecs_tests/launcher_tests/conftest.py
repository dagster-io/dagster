import json
from collections import namedtuple
from contextlib import contextmanager
from typing import Any, Callable, ContextManager, Iterator, Mapping, Sequence

import boto3
import moto
import pytest
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.external import ExternalJob
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.test_utils import in_process_test_workspace, instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._utils.warnings import disable_dagster_warnings

from dagster_aws_tests.ecs_tests.launcher_tests import repo

Secret = namedtuple("Secret", ["name", "arn"])


@pytest.fixture(autouse=True)
def ignore_dagster_warnings() -> Iterator[None]:
    with disable_dagster_warnings():
        yield


@pytest.fixture
def cloudwatch_client(region: str):
    with moto.mock_logs():
        yield boto3.client("logs", region_name=region)


@pytest.fixture
def log_group(cloudwatch_client) -> str:
    name = "/dagster-test/test-cloudwatch-logging"
    cloudwatch_client.create_log_group(logGroupName=name)
    return name


@pytest.fixture
def image() -> str:
    return "dagster:first"


@pytest.fixture
def other_image() -> str:
    return "dagster:second"


@pytest.fixture
def environment() -> Sequence[Mapping[str, str]]:
    return [{"name": "FOO", "value": "bar"}]


@pytest.fixture
def task_definition(ecs, image, environment):
    return ecs.register_task_definition(
        family="dagster",
        containerDefinitions=[
            {
                "name": "dagster",
                "image": image,
                "environment": environment,
                "entryPoint": ["ls"],
                "dependsOn": [
                    {
                        "containerName": "other",
                        "condition": "SUCCESS",
                    },
                ],
                "healthCheck": {"command": ["HELLO"]},
            },
            {
                "name": "other",
                "image": image,
                "entryPoint": ["ls"],
            },
        ],
        networkMode="awsvpc",
        memory="512",
        cpu="256",
    )["taskDefinition"]


@pytest.fixture
def assign_public_ip():
    return True


@pytest.fixture
def task(ecs, subnet, security_group, task_definition, assign_public_ip):
    return ecs.run_task(
        taskDefinition=task_definition["family"],
        networkConfiguration={
            "awsvpcConfiguration": {
                "assignPublicIp": "ENABLED" if assign_public_ip else "DISABLED",
                "subnets": [subnet.id],
                "securityGroups": [security_group.id],
            },
        },
    )["tasks"][0]


@pytest.fixture
def stub_aws(ecs, ec2, secrets_manager, cloudwatch_client, monkeypatch):
    def mock_client(*args, **kwargs):
        if "ecs" in args:
            return ecs
        if "secretsmanager" in args:
            return secrets_manager
        if "logs" in args:
            return cloudwatch_client
        else:
            raise Exception("Unexpected args")

    monkeypatch.setattr(boto3, "client", mock_client)
    monkeypatch.setattr(boto3, "resource", lambda *args, **kwargs: ec2)


@pytest.fixture
def stub_ecs_metadata(task, monkeypatch, requests_mock):
    container_uri = "http://metadata_host"
    monkeypatch.setenv("ECS_CONTAINER_METADATA_URI_V4", container_uri)
    container = task["containers"][0]["name"]
    requests_mock.get(container_uri, json={"Name": container})

    task_uri = container_uri + "/task"
    requests_mock.get(
        task_uri,
        json={
            "Cluster": task["clusterArn"],
            "TaskARN": task["taskArn"],
        },
    )


@pytest.fixture
def instance_cm(stub_aws, stub_ecs_metadata) -> Callable[..., ContextManager[DagsterInstance]]:
    @contextmanager
    def cm(config=None):
        overrides = {
            "run_launcher": {
                "module": "dagster_aws.ecs",
                "class": "EcsRunLauncher",
                "config": {**(config or {})},
            }
        }
        with instance_for_test(overrides) as dagster_instance:
            yield dagster_instance

    return cm


@pytest.fixture
def instance(
    instance_cm: Callable[..., ContextManager[DagsterInstance]],
) -> Iterator[DagsterInstance]:
    with instance_cm(
        {
            "run_ecs_tags": [
                {"key": "HAS_VALUE", "value": "SEE"},
                {"key": "DOES_NOT_HAVE_VALUE"},
            ]
        }
    ) as dagster_instance:
        yield dagster_instance


@pytest.fixture
def instance_with_log_group(
    instance_cm: Callable[..., ContextManager[DagsterInstance]], log_group: str
) -> Iterator[DagsterInstance]:
    with instance_cm(config={"task_definition": {"log_group": log_group}}) as dagster_instance:
        yield dagster_instance


@pytest.fixture
def instance_with_resources(
    instance_cm: Callable[..., ContextManager[DagsterInstance]],
) -> Iterator[DagsterInstance]:
    with instance_cm(
        config={
            "run_resources": {
                "cpu": "1024",
                "memory": "2048",
                "ephemeral_storage": 50,
            }
        }
    ) as dagster_instance:
        yield dagster_instance


@pytest.fixture
def instance_dont_use_current_task(
    instance_cm: Callable[..., ContextManager[DagsterInstance]], subnet, monkeypatch
) -> Iterator[DagsterInstance]:
    with instance_cm(
        config={
            "use_current_ecs_task_config": False,
            "run_task_kwargs": {
                "cluster": "my_cluster",
                "networkConfiguration": {
                    "awsvpcConfiguration": {
                        "subnets": [subnet.id],
                        "assignPublicIp": "ENABLED",
                    },
                },
            },
        }
    ) as dagster_instance:
        # Not running in an ECS task
        monkeypatch.setenv("ECS_CONTAINER_METADATA_URI_V4", None)
        yield dagster_instance


@pytest.fixture
def instance_fargate_spot(
    instance_cm: Callable[..., ContextManager[DagsterInstance]],
) -> Iterator[DagsterInstance]:
    with instance_cm(
        config={
            "run_task_kwargs": {
                "capacityProviderStrategy": [
                    {
                        "capacityProvider": "FARGATE_SPOT",
                    }
                ],
            },
        }
    ) as dagster_instance:
        yield dagster_instance


@pytest.fixture
def workspace(instance: DagsterInstance, image: str) -> Iterator[WorkspaceRequestContext]:
    with in_process_test_workspace(
        instance,
        loadable_target_origin=LoadableTargetOrigin(
            python_file=repo.__file__,
            attribute=repo.repository.name,
        ),
        container_image=image,
    ) as workspace:
        yield workspace


@pytest.fixture
def other_workspace(
    instance: DagsterInstance, other_image: str
) -> Iterator[WorkspaceRequestContext]:
    with in_process_test_workspace(
        instance,
        loadable_target_origin=LoadableTargetOrigin(
            python_file=repo.__file__,
            attribute=repo.repository.name,
        ),
        container_image=other_image,
    ) as workspace:
        yield workspace


@pytest.fixture
def job() -> JobDefinition:
    return repo.job


@pytest.fixture
def external_job(workspace: WorkspaceRequestContext) -> ExternalJob:
    location = workspace.get_code_location(workspace.code_location_names[0])
    return location.get_repository(repo.repository.name).get_full_external_job(repo.job.name)


@pytest.fixture
def other_external_job(other_workspace: WorkspaceRequestContext) -> ExternalJob:
    location = other_workspace.get_code_location(other_workspace.code_location_names[0])
    return location.get_repository(repo.repository.name).get_full_external_job(repo.job.name)


@pytest.fixture
def run(instance: DagsterInstance, job: JobDefinition, external_job: ExternalJob) -> DagsterRun:
    return instance.create_run_for_job(
        job,
        external_job_origin=external_job.get_external_origin(),
        job_code_origin=external_job.get_python_origin(),
    )


@pytest.fixture
def other_run(
    instance: DagsterInstance, job: JobDefinition, other_external_job: ExternalJob
) -> DagsterRun:
    return instance.create_run_for_job(
        job,
        external_job_origin=other_external_job.get_external_origin(),
        job_code_origin=other_external_job.get_python_origin(),
    )


@pytest.fixture
def launch_run(
    workspace: WorkspaceRequestContext, job: JobDefinition, external_job: ExternalJob
) -> Callable[[DagsterInstance], None]:
    def _launch_run(instance: DagsterInstance) -> None:
        run = instance.create_run_for_job(
            job,
            external_job_origin=external_job.get_external_origin(),
            job_code_origin=external_job.get_python_origin(),
        )
        instance.launch_run(run.run_id, workspace)

    return _launch_run


@pytest.fixture
def custom_instance_cm(stub_aws, stub_ecs_metadata):
    @contextmanager
    def cm(config=None):
        overrides = {
            "run_launcher": {
                "module": "dagster_aws.ecs.test_utils",
                "class": "CustomECSRunLauncher",
                "config": {**(config or {})},
            }
        }
        with instance_for_test(overrides) as dagster_instance:
            yield dagster_instance

    return cm


@pytest.fixture
def custom_instance(
    custom_instance_cm: Callable[..., ContextManager[DagsterInstance]],
) -> Iterator[DagsterInstance]:
    with custom_instance_cm() as dagster_instance:
        yield dagster_instance


@pytest.fixture
def custom_workspace(
    custom_instance: DagsterInstance, image: str
) -> Iterator[WorkspaceRequestContext]:
    with in_process_test_workspace(
        custom_instance,
        loadable_target_origin=LoadableTargetOrigin(
            python_file=repo.__file__,
            attribute=repo.repository.name,
        ),
        container_image=image,
    ) as workspace:
        yield workspace


@pytest.fixture
def custom_run(
    custom_instance: DagsterInstance, job: JobDefinition, external_job: ExternalJob
) -> DagsterRun:
    return custom_instance.create_run_for_job(
        job,
        external_job_origin=external_job.get_external_origin(),
        job_code_origin=external_job.get_python_origin(),
    )


@pytest.fixture
def tagged_secret(secrets_manager):
    # A secret tagged with "dagster"
    name = "tagged_secret"
    arn = secrets_manager.create_secret(
        Name=name,
        SecretString="hello",
        Tags=[{"Key": "dagster", "Value": "true"}],
    )["ARN"]

    yield Secret(name, arn)


@pytest.fixture
def other_secret(secrets_manager):
    # A secret without a tag
    name = "other_secret"
    arn = secrets_manager.create_secret(
        Name=name,
        SecretString="hello",
    )["ARN"]

    yield Secret(name, arn)


@pytest.fixture
def configured_secret(secrets_manager) -> Iterator[Secret]:
    name = "configured_secret"
    arn = secrets_manager.create_secret(
        Name=name,
        SecretString=json.dumps({"hello": "world"}),
    )["ARN"]

    yield Secret(name, arn)


@pytest.fixture
def other_configured_secret(secrets_manager) -> Iterator[Secret]:
    name = "other_configured_secret"
    arn = secrets_manager.create_secret(
        Name=name,
        SecretString=json.dumps({"goodnight": "moon"}),
    )["ARN"]

    yield Secret(name, arn)


@pytest.fixture
def container_context_config(configured_secret: Secret) -> Mapping[str, Any]:
    return {
        "env_vars": ["SHARED_KEY=SHARED_VAL"],
        "ecs": {
            "secrets": [
                {
                    "name": "HELLO",
                    "valueFrom": configured_secret.arn + "/hello",
                }
            ],
            "secrets_tags": ["dagster"],
            "env_vars": ["FOO_ENV_VAR=BAR_VALUE"],
            "container_name": "foo",
            "run_resources": {
                "cpu": "4096",
                "memory": "8192",
                "ephemeral_storage": 100,
            },
            "server_resources": {
                "cpu": "1024",
                "memory": "2048",
                "ephemeral_storage": 25,
            },
            "task_role_arn": "fake-task-role",
            "execution_role_arn": "fake-execution-role",
            "runtime_platform": {
                "operatingSystemFamily": "WINDOWS_SERVER_2019_FULL",
            },
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
            "repository_credentials": "fake-secret-arn",
            "server_health_check": {
                "command": ["HELLO"],
            },
        },
    }


@pytest.fixture
def other_container_context_config(other_configured_secret):
    return {
        "env_vars": ["SHARED_OTHER_KEY=SHARED_OTHER_VAL"],
        "ecs": {
            "secrets": [
                {
                    "name": "GOODBYE",
                    "valueFrom": other_configured_secret.arn + "/goodbye",
                }
            ],
            "secrets_tags": ["other_secret_tag"],
            "env_vars": ["OTHER_FOO_ENV_VAR"],
            "container_name": "bar",
            "run_resources": {
                "cpu": "256",
            },
            "server_resources": {
                "cpu": "2048",
                "memory": "4096",
                "replica_count": 2,
            },
            "task_role_arn": "other-task-role",
            "execution_role_arn": "other-fake-execution-role",
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
                }
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
        },
    }


@pytest.fixture
def launch_run_with_container_context(
    job: JobDefinition,
    external_job: ExternalJob,
    workspace: WorkspaceRequestContext,
    container_context_config,
):
    def _launch_run(instance):
        python_origin = external_job.get_python_origin()
        python_origin = python_origin._replace(
            repository_origin=python_origin.repository_origin._replace(
                container_context=container_context_config,
            )
        )

        run = instance.create_run_for_job(
            job,
            external_job_origin=external_job.get_external_origin(),
            job_code_origin=python_origin,
        )
        instance.launch_run(run.run_id, workspace)

    return _launch_run
