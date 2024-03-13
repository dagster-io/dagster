import copy
import json
import time
from concurrent.futures import ThreadPoolExecutor

import dagster_aws
import pytest
from botocore.exceptions import ClientError
from dagster._check import CheckError
from dagster._core.code_pointer import FileCodePointer
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.launcher import LaunchRunContext
from dagster._core.launcher.base import WorkerStatus
from dagster._core.origin import JobPythonOrigin, RepositoryPythonOrigin
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.tags import RUN_WORKER_ID_TAG
from dagster_aws.ecs import EcsEventualConsistencyTimeout
from dagster_aws.ecs.launcher import (
    DEFAULT_LINUX_RESOURCES,
    DEFAULT_WINDOWS_RESOURCES,
    RUNNING_STATUSES,
    STOPPED_STATUSES,
)
from dagster_aws.ecs.tasks import DagsterEcsTaskDefinitionConfig
from dagster_aws.ecs.utils import get_task_definition_family


@pytest.mark.parametrize("task_long_arn_format", ["enabled", "disabled"])
def test_default_launcher(
    ecs,
    instance,
    workspace,
    run,
    subnet,
    image,
    environment,
    task_long_arn_format,
):
    ecs.put_account_setting(name="taskLongArnFormat", value=task_long_arn_format)
    assert not run.tags

    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    initial_tasks = ecs.list_tasks()["taskArns"]

    instance.launch_run(run.run_id, workspace)

    # A new task definition is created
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_definitions) == len(initial_task_definitions) + 1
    task_definition_arn = next(iter(set(task_definitions).difference(initial_task_definitions)))
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)
    task_definition = task_definition["taskDefinition"]

    assert instance.run_launcher.check_run_worker_health(run).status == WorkerStatus.RUNNING

    # It has a new family, name, and image
    assert task_definition["family"] == get_task_definition_family("run", run.external_job_origin)
    assert len(task_definition["containerDefinitions"]) == 1
    container_definition = task_definition["containerDefinitions"][0]
    assert container_definition["name"] == "run"
    assert container_definition["image"] == image
    assert not container_definition.get("entryPoint")
    assert not container_definition.get("dependsOn")
    # But other stuff is inherited from the parent task definition
    assert all(item in container_definition["environment"] for item in environment)
    assert {"name": "DAGSTER_RUN_JOB_NAME", "value": "job"} in container_definition["environment"]

    # A new task is launched
    tasks = ecs.list_tasks()["taskArns"]

    assert len(tasks) == len(initial_tasks) + 1
    task_arn = next(iter(set(tasks).difference(initial_tasks)))
    task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]
    assert subnet.id in str(task)
    assert task["taskDefinitionArn"] == task_definition["taskDefinitionArn"]
    assert task["launchType"] == "FARGATE"

    # The run is tagged with info about the ECS task
    assert instance.get_run_by_id(run.run_id).tags["ecs/task_arn"] == task_arn
    cluster_arn = ecs._cluster_arn("default")  # noqa: SLF001
    assert instance.get_run_by_id(run.run_id).tags["ecs/cluster"] == cluster_arn

    # If we're using the new long ARN format,
    # the ECS task is tagged with info about the Dagster run
    if task_long_arn_format == "enabled":
        assert (
            ecs.list_tags_for_resource(resourceArn=task_arn)["tags"][0]["key"] == "dagster/run_id"
        )
        assert ecs.list_tags_for_resource(resourceArn=task_arn)["tags"][0]["value"] == run.run_id

    # We set job-specific overides
    overrides = task["overrides"]["containerOverrides"]
    assert len(overrides) == 1
    override = overrides[0]
    assert override["name"] == "run"
    assert "execute_run" in override["command"]
    assert run.run_id in str(override["command"])

    # And we log
    events = instance.event_log_storage.get_logs_for_run(run.run_id)
    latest_event = events[-1]
    assert latest_event.message == "[EcsRunLauncher] Launching run in ECS task"
    metadata = latest_event.dagster_event.engine_event_data.metadata
    assert metadata["ECS Task ARN"] == MetadataValue.text(task_arn)
    assert metadata["ECS Cluster"] == MetadataValue.text(cluster_arn)
    assert metadata["Run ID"] == MetadataValue.text(run.run_id)

    # check status and stop task
    assert instance.run_launcher.check_run_worker_health(run).status == WorkerStatus.RUNNING
    ecs.stop_task(task=task_arn)


def test_launcher_fargate_spot(
    ecs,
    instance_fargate_spot,
    workspace,
    external_job,
    job,
    subnet,
    image,
    environment,
):
    instance = instance_fargate_spot
    run = instance.create_run_for_job(
        job,
        external_job_origin=external_job.get_external_origin(),
        job_code_origin=external_job.get_python_origin(),
    )
    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    initial_tasks = ecs.list_tasks()["taskArns"]

    instance.launch_run(run.run_id, workspace)

    # A new task definition is still created
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_definitions) == len(initial_task_definitions) + 1
    task_definition_arn = next(iter(set(task_definitions).difference(initial_task_definitions)))
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)
    task_definition = task_definition["taskDefinition"]

    # A new task is launched
    tasks = ecs.list_tasks()["taskArns"]

    assert len(tasks) == len(initial_tasks) + 1
    task_arn = next(iter(set(tasks).difference(initial_tasks)))
    task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]

    assert task["capacityProviderName"] == "FARGATE_SPOT"

    # Override capacity provider strategy with tags
    run = instance.create_run_for_job(
        job,
        external_job_origin=external_job.get_external_origin(),
        job_code_origin=external_job.get_python_origin(),
    )
    instance.add_run_tags(
        run.run_id,
        {
            "ecs/run_task_kwargs": json.dumps(
                {
                    "capacityProviderStrategy": [
                        {
                            "capacityProvider": "CUSTOM",
                        },
                    ],
                }
            )
        },
    )
    instance.launch_run(run.run_id, workspace)

    # A new task definition is still created
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_definitions) == len(initial_task_definitions) + 1
    task_definition_arn = next(iter(set(task_definitions).difference(initial_task_definitions)))
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)
    task_definition = task_definition["taskDefinition"]

    # A new task is launched
    second_tasks = ecs.list_tasks()["taskArns"]

    assert len(second_tasks) == len(tasks) + 1
    task_arn = next(iter(set(second_tasks).difference(tasks)))
    task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]

    assert task["capacityProviderName"] == "CUSTOM"


def test_launcher_dont_use_current_task(
    ecs,
    instance_dont_use_current_task,
    workspace,
    external_job,
    job,
    subnet,
    image,
    environment,
):
    instance = instance_dont_use_current_task
    run = instance.create_run_for_job(
        job,
        external_job_origin=external_job.get_external_origin(),
        job_code_origin=external_job.get_python_origin(),
    )

    cluster = instance.run_launcher.run_task_kwargs["cluster"]
    assert cluster == "my_cluster"

    assert not run.tags

    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    initial_tasks = ecs.list_tasks(cluster=cluster)["taskArns"]

    instance.launch_run(run.run_id, workspace)

    # A new task definition is still created
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_definitions) == len(initial_task_definitions) + 1
    task_definition_arn = next(iter(set(task_definitions).difference(initial_task_definitions)))
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)
    task_definition = task_definition["taskDefinition"]

    assert instance.run_launcher.check_run_worker_health(run).status == WorkerStatus.RUNNING

    # It has a new family, name, and image
    assert task_definition["family"] == get_task_definition_family("run", run.external_job_origin)
    assert len(task_definition["containerDefinitions"]) == 1
    container_definition = task_definition["containerDefinitions"][0]
    assert container_definition["name"] == "run"
    assert container_definition["image"] == image
    assert not container_definition.get("entryPoint")
    assert not container_definition.get("dependsOn")

    # It does not take in the environment configured on the calling task definition
    assert not any(item in container_definition["environment"] for item in environment)
    assert {"name": "DAGSTER_RUN_JOB_NAME", "value": "job"} in container_definition["environment"]

    # A new task is launched
    tasks = ecs.list_tasks(cluster=cluster)["taskArns"]

    assert len(tasks) == len(initial_tasks) + 1
    task_arn = next(iter(set(tasks).difference(initial_tasks)))
    task = ecs.describe_tasks(cluster=cluster, tasks=[task_arn])["tasks"][0]
    assert subnet.id in str(task)
    assert task["taskDefinitionArn"] == task_definition["taskDefinitionArn"]

    # The run is tagged with info about the ECS task
    assert instance.get_run_by_id(run.run_id).tags["ecs/task_arn"] == task_arn
    cluster_arn = ecs._cluster_arn(cluster)  # noqa: SLF001
    assert instance.get_run_by_id(run.run_id).tags["ecs/cluster"] == cluster_arn

    assert ecs.list_tags_for_resource(resourceArn=task_arn)["tags"][0]["key"] == "dagster/run_id"
    assert ecs.list_tags_for_resource(resourceArn=task_arn)["tags"][0]["value"] == run.run_id

    # We set job-specific overides
    overrides = task["overrides"]["containerOverrides"]
    assert len(overrides) == 1
    override = overrides[0]
    assert override["name"] == "run"
    assert "execute_run" in override["command"]
    assert run.run_id in str(override["command"])

    # And we log
    events = instance.event_log_storage.get_logs_for_run(run.run_id)
    latest_event = events[-1]
    assert latest_event.message == "[EcsRunLauncher] Launching run in ECS task"
    metadata = latest_event.dagster_event.engine_event_data.metadata
    assert metadata["ECS Task ARN"] == MetadataValue.text(task_arn)
    assert metadata["ECS Cluster"] == MetadataValue.text(cluster_arn)
    assert metadata["Run ID"] == MetadataValue.text(run.run_id)

    # check status and stop task
    assert instance.run_launcher.check_run_worker_health(run).status == WorkerStatus.RUNNING
    ecs.stop_task(cluster=cluster, task=task_arn)


def test_task_definition_registration(
    ecs, instance, workspace, run, other_workspace, other_run, secrets_manager, monkeypatch
):
    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    _initial_tasks = ecs.list_tasks()["taskArns"]

    instance.launch_run(run.run_id, workspace)

    # A new task definition is created
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_definitions) == len(initial_task_definitions) + 1

    # Launching another run reuses an existing task definition
    instance.launch_run(run.run_id, workspace)
    assert task_definitions == ecs.list_task_definitions()["taskDefinitionArns"]

    # Register a new task definition if the image changes
    instance.launch_run(other_run.run_id, other_workspace)
    assert len(ecs.list_task_definitions()["taskDefinitionArns"]) == len(task_definitions) + 1

    # Relaunching another run with the new image reuses an existing task definition
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    instance.launch_run(other_run.run_id, other_workspace)
    assert task_definitions == ecs.list_task_definitions()["taskDefinitionArns"]

    # Register a new task definition if secrets change
    secrets_manager.create_secret(
        Name="hello",
        SecretString="hello",
        Tags=[{"Key": "dagster", "Value": "true"}],
    )

    instance.launch_run(other_run.run_id, other_workspace)
    assert len(ecs.list_task_definitions()["taskDefinitionArns"]) == len(task_definitions) + 1

    # Relaunching another run with the same secrets reuses an existing task definition
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    instance.launch_run(other_run.run_id, other_workspace)
    assert task_definitions == ecs.list_task_definitions()["taskDefinitionArns"]

    # Register a new task definition if _reuse_task_definition returns False
    # for any other reason
    monkeypatch.setattr(instance.run_launcher, "_reuse_task_definition", lambda *_: False)

    instance.launch_run(other_run.run_id, other_workspace)
    assert len(ecs.list_task_definitions()["taskDefinitionArns"]) == len(task_definitions) + 1


@pytest.mark.skip(
    "This remains occasionally flaky on older versions of Python. See"
    " https://github.com/dagster-io/dagster/pull/11290 "
    "https://linear.app/elementl/issue/CLOUD-2093/re-enable-flaky-ecs-task-registration-race-condition-tests"
)
def test_task_definition_registration_race_condition(ecs, instance, workspace, run):
    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    initial_tasks = ecs.list_tasks()["taskArns"]

    with ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(10):
            executor.submit(instance.launch_run, run.run_id, workspace)

    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_definitions) == len(initial_task_definitions) + 1

    tasks = ecs.list_tasks()["taskArns"]
    assert len(tasks) == len(initial_tasks) + 10


def test_reuse_task_definition(instance, ecs):
    image = "image"
    secrets = []
    environment = [
        {
            "name": "MY_ENV_VAR",
            "value": "MY_VALUE",
        },
        {
            "name": "MY_OTHER_ENV_VAR",
            "value": "MY_OTHER_VALUE",
        },
    ]

    container_name = instance.run_launcher.container_name

    original_task_definition = {
        "family": "hello",
        "containerDefinitions": [
            {
                "image": image,
                "name": container_name,
                "secrets": secrets,
                "environment": environment,
                "command": ["echo", "HELLO"],
            },
            {
                "image": "other_image",
                "name": "the_sidecar",
            },
        ],
        "cpu": "256",
        "memory": "512",
    }

    task_definition_config = DagsterEcsTaskDefinitionConfig.from_task_definition_dict(
        original_task_definition, container_name
    )

    # New task definition not re-used since it is new
    assert not instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        task_definition_config, container_name
    )
    # Once it's registered, it is re-used

    ecs.register_task_definition(**original_task_definition)

    assert instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        task_definition_config, container_name
    )

    # Reordering environment is still reused
    task_definition = copy.deepcopy(original_task_definition)
    task_definition["containerDefinitions"][0]["environment"] = list(
        reversed(task_definition["containerDefinitions"][0]["environment"])
    )
    assert instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(task_definition, container_name),
        container_name,
    )

    # Changed image fails
    task_definition = copy.deepcopy(original_task_definition)
    task_definition["containerDefinitions"][0]["image"] = "new-image"

    assert not instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(task_definition, container_name),
        container_name,
    )

    # Changed container name fails
    task_definition = copy.deepcopy(original_task_definition)
    task_definition["containerDefinitions"][0]["name"] = "new-container"
    assert not instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(task_definition, "new-container"),
        container_name,
    )

    assert not instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(
            original_task_definition, container_name
        ),
        "new-container",
    )

    # Changed secrets fails
    task_definition = copy.deepcopy(original_task_definition)
    task_definition["containerDefinitions"][0]["secrets"].append(
        {"name": "new-secret", "valueFrom": "fake-arn"}
    )
    assert not instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(task_definition, container_name),
        container_name,
    )

    # Changed environment fails

    task_definition = copy.deepcopy(original_task_definition)
    task_definition["containerDefinitions"][0]["environment"].append(
        {"name": "MY_ENV_VAR", "value": "MY_ENV_VALUE"}
    )
    assert not instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(
            task_definition,
            container_name,
        ),
        container_name,
    )

    # Changed execution role fails
    task_definition = copy.deepcopy(original_task_definition)
    task_definition["executionRoleArn"] = "new-role"
    assert not instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(task_definition, container_name),
        container_name,
    )

    # Changed task role fails
    task_definition = copy.deepcopy(original_task_definition)
    task_definition["taskRoleArn"] = "new-role"
    assert not instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(task_definition, container_name),
        container_name,
    )

    # Changed runtime platform fails
    task_definition = copy.deepcopy(original_task_definition)
    task_definition["runtimePlatform"] = {"operatingSystemFamily": "WINDOWS_SERVER_2019_FULL"}
    assert not instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(task_definition, container_name),
        container_name,
    )

    # Changed command fails
    task_definition = copy.deepcopy(original_task_definition)
    task_definition["containerDefinitions"][0]["command"] = ["echo", "GOODBYE"]
    assert not instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(task_definition, container_name),
        container_name,
    )

    # Changed linuxParameters fails
    task_definition = copy.deepcopy(original_task_definition)
    task_definition["containerDefinitions"][0]["linuxParameters"] = {
        "capabilities": {"add": ["SYS_PTRACE"]},
        "initProcessEnabled": True,
    }
    assert not instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(task_definition, container_name),
        container_name,
    )

    # Any other diff passes
    task_definition = copy.deepcopy(original_task_definition)
    task_definition["somethingElse"] = "boom"
    assert instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(task_definition, container_name),
        container_name,
    )

    # Different sidecar image fails
    task_definition = copy.deepcopy(original_task_definition)
    task_definition["containerDefinitions"][1]["image"] = "new_sidecar_image"

    assert not instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(task_definition, container_name),
        container_name,
    )

    # Different sidecar name fails
    task_definition = copy.deepcopy(original_task_definition)
    task_definition["containerDefinitions"][1]["name"] = "new_sidecar_name"

    assert not instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(task_definition, container_name),
        container_name,
    )

    # Different sidecar environments fail
    task_definition = copy.deepcopy(original_task_definition)
    task_definition["containerDefinitions"][1]["environment"] = environment

    assert not instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(task_definition, container_name),
        container_name,
    )

    # Different sidecar secrets fail
    task_definition = copy.deepcopy(original_task_definition)
    task_definition["containerDefinitions"][1]["secrets"] = [
        {"name": "a_secret", "valueFrom": "an_arn"}
    ]

    assert not instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(task_definition, container_name),
        container_name,
    )

    # Other changes to sidecars do not fail
    task_definition = copy.deepcopy(original_task_definition)
    task_definition["containerDefinitions"][1]["cpu"] = "256"
    assert instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(task_definition, container_name),
        container_name,
    )

    # Fails if the existing task definition has a different container name
    task_definition = copy.deepcopy(original_task_definition)
    task_definition["containerDefinitions"][0]["name"] = "foobar"
    ecs.register_task_definition(**task_definition)

    assert not instance.run_launcher._reuse_task_definition(  # noqa: SLF001
        DagsterEcsTaskDefinitionConfig.from_task_definition_dict(
            original_task_definition, container_name
        ),
        container_name,
    )


def test_default_task_definition_resources(ecs, instance_cm, run, workspace, job, external_job):
    task_role_arn = "fake-task-role"
    execution_role_arn = "fake-execution-role"
    with instance_cm(
        {
            "task_definition": {
                "task_role_arn": task_role_arn,
                "execution_role_arn": execution_role_arn,
            },
        }
    ) as instance:
        run = instance.create_run_for_job(
            job,
            external_job_origin=external_job.get_external_origin(),
            job_code_origin=external_job.get_python_origin(),
        )
        initial_tasks = ecs.list_tasks()["taskArns"]

        instance.launch_run(run.run_id, workspace)

        tasks = ecs.list_tasks()["taskArns"]
        task_arn = next(iter(set(tasks).difference(initial_tasks)))

        task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]

        task_definition_arn = task["taskDefinitionArn"]

        task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)[
            "taskDefinition"
        ]

        # Since this is not a windows task def, the default cpu/memory are 256/512
        assert task_definition["cpu"] == DEFAULT_LINUX_RESOURCES["cpu"]
        assert task_definition["memory"] == DEFAULT_LINUX_RESOURCES["memory"]

    # But a windows task def has different defaults that are valid for window
    with instance_cm(
        {
            "task_definition": {
                "task_role_arn": task_role_arn,
                "execution_role_arn": execution_role_arn,
                "runtime_platform": {"operatingSystemFamily": "WINDOWS_SERVER_2019_FULL"},
            },
        }
    ) as instance:
        run = instance.create_run_for_job(
            job,
            external_job_origin=external_job.get_external_origin(),
            job_code_origin=external_job.get_python_origin(),
        )
        initial_tasks = ecs.list_tasks()["taskArns"]

        instance.launch_run(run.run_id, workspace)

        tasks = ecs.list_tasks()["taskArns"]
        task_arn = next(iter(set(tasks).difference(initial_tasks)))

        task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]

        task_definition_arn = task["taskDefinitionArn"]

        task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)[
            "taskDefinition"
        ]

        # Default cpu/memory is higher on windows
        assert task_definition["cpu"] == DEFAULT_WINDOWS_RESOURCES["cpu"]
        assert task_definition["memory"] == DEFAULT_WINDOWS_RESOURCES["memory"]

    # Setting resources on the run launcher ignores the defaults
    with instance_cm(
        {
            "task_definition": {
                "task_role_arn": task_role_arn,
                "execution_role_arn": execution_role_arn,
            },
            "run_resources": {"cpu": "2048", "memory": "4096", "ephemeral_storage": 36},
        }
    ) as instance:
        run = instance.create_run_for_job(
            job,
            external_job_origin=external_job.get_external_origin(),
            job_code_origin=external_job.get_python_origin(),
        )
        initial_tasks = ecs.list_tasks()["taskArns"]

        instance.launch_run(run.run_id, workspace)

        tasks = ecs.list_tasks()["taskArns"]
        task_arn = next(iter(set(tasks).difference(initial_tasks)))

        task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]

        task_definition_arn = task["taskDefinitionArn"]

        task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)[
            "taskDefinition"
        ]

        assert task_definition["cpu"] == "2048"
        assert task_definition["memory"] == "4096"
        assert task_definition["ephemeralStorage"]["sizeInGiB"] == 36


def test_launching_with_task_definition_dict(ecs, instance_cm, run, workspace, job, external_job):
    container_name = "dagster"

    task_role_arn = "fake-task-role"
    execution_role_arn = "fake-execution-role"
    sidecar = {
        "name": "DatadogAgent",
        "image": "public.ecr.aws/datadog/agent:latest",
        "environment": [
            {"name": "ECS_FARGATE", "value": "true"},
        ],
    }
    log_group = "my-log-group"

    mount_points = [
        {
            "sourceVolume": "myEfsVolume",
            "containerPath": "/mount/efs",
            "readOnly": True,
        }
    ]
    volumes = [
        {
            "name": "myEfsVolume",
            "efsVolumeConfiguration": {
                "fileSystemId": "fs-1234",
                "rootDirectory": "/path/to/my/data",
            },
        }
    ]

    repository_credentials = "fake-secret-arn"

    linux_parameters = {
        "capabilities": {"add": ["SYS_PTRACE"]},
        "initProcessEnabled": True,
    }

    # You can provide a family or a task definition ARN
    with instance_cm(
        {
            "task_definition": {
                "log_group": log_group,
                "task_role_arn": task_role_arn,
                "execution_role_arn": execution_role_arn,
                "sidecar_containers": [sidecar],
                "requires_compatibilities": ["FARGATE"],
                "runtime_platform": {"operatingSystemFamily": "WINDOWS_SERVER_2019_FULL"},
                "mount_points": mount_points,
                "volumes": volumes,
                "repository_credentials": repository_credentials,
                "linux_parameters": linux_parameters,
            },
            "container_name": container_name,
        }
    ) as instance:
        run = instance.create_run_for_job(
            job,
            external_job_origin=external_job.get_external_origin(),
            job_code_origin=external_job.get_python_origin(),
        )

        initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
        initial_tasks = ecs.list_tasks()["taskArns"]

        instance.launch_run(run.run_id, workspace)

        new_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]

        # A new task definition is created
        assert new_task_definitions != initial_task_definitions

        # A new task is launched
        tasks = ecs.list_tasks()["taskArns"]
        assert len(tasks) == len(initial_tasks) + 1
        task_arn = next(iter(set(tasks).difference(initial_tasks)))
        task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]
        task_definition_arn = task["taskDefinitionArn"]

        task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)[
            "taskDefinition"
        ]

        assert task_definition["volumes"] == volumes
        assert task_definition["taskRoleArn"] == task_role_arn
        assert task_definition["executionRoleArn"] == execution_role_arn
        assert task_definition["runtimePlatform"] == {
            "operatingSystemFamily": "WINDOWS_SERVER_2019_FULL"
        }

        container_definition = task_definition["containerDefinitions"][0]
        assert container_definition["mountPoints"] == mount_points

        assert (
            container_definition["repositoryCredentials"]["credentialsParameter"]
            == repository_credentials
        )

        assert container_definition["linuxParameters"] == linux_parameters

        assert [container["name"] for container in task_definition["containerDefinitions"]] == [
            container_name,
            sidecar["name"],
        ]

        # We set job-specific overides
        overrides = task["overrides"]["containerOverrides"]
        assert len(overrides) == 1
        override = overrides[0]
        assert override["name"] == container_name
        assert "execute_run" in override["command"]
        assert run.run_id in str(override["command"])

        second_run = run = instance.create_run_for_job(
            job,
            external_job_origin=external_job.get_external_origin(),
            job_code_origin=external_job.get_python_origin(),
        )

        instance.launch_run(second_run.run_id, workspace)

        # A new task definition is not created
        assert ecs.list_task_definitions()["taskDefinitionArns"] == new_task_definitions


def test_launching_custom_task_definition(ecs, instance_cm, run, workspace, job, external_job):
    container_name = "override_container"

    task_definition = ecs.register_task_definition(
        family="override",
        containerDefinitions=[{"name": container_name, "image": "hello_world:latest"}],
        networkMode="bridge",
        memory="512",
        cpu="256",
    )["taskDefinition"]
    task_definition_arn = task_definition["taskDefinitionArn"]
    family = task_definition["family"]

    # The task definition doesn't exist
    with pytest.raises(Exception), instance_cm({"task_definition": "does not exist"}) as instance:
        print(instance.run_launcher)  # noqa: T201

    # The task definition doesn't include the default container name
    with pytest.raises(CheckError), instance_cm({"task_definition": family}) as instance:
        print(instance.run_launcher)  # noqa: T201

    # The task definition doesn't include the container name
    with pytest.raises(CheckError), instance_cm(
        {"task_definition": family, "container_name": "does not exist"}
    ) as instance:
        print(instance.run_launcher)  # noqa: T201

    # You can provide a family or a task definition ARN
    with instance_cm(
        {"task_definition": task_definition_arn, "container_name": container_name}
    ) as instance:
        run = instance.create_run_for_job(
            job,
            external_job_origin=external_job.get_external_origin(),
            job_code_origin=external_job.get_python_origin(),
        )

        initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
        initial_tasks = ecs.list_tasks()["taskArns"]

        instance.launch_run(run.run_id, workspace)

        # A new task definition is not created
        assert ecs.list_task_definitions()["taskDefinitionArns"] == initial_task_definitions

        # A new task is launched
        tasks = ecs.list_tasks()["taskArns"]
        assert len(tasks) == len(initial_tasks) + 1
        task_arn = next(iter(set(tasks).difference(initial_tasks)))
        task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]
        assert task["taskDefinitionArn"] == task_definition["taskDefinitionArn"]

        # We set job-specific overides
        overrides = task["overrides"]["containerOverrides"]
        assert len(overrides) == 1
        override = overrides[0]
        assert override["name"] == container_name
        assert "execute_run" in override["command"]
        assert run.run_id in str(override["command"])


def test_eventual_consistency(ecs, instance, workspace, run, monkeypatch):
    initial_tasks = ecs.list_tasks()["taskArns"]

    retries = 0
    original_describe_tasks = instance.run_launcher.ecs.describe_tasks
    original_backoff_retries = dagster_aws.ecs.tasks.BACKOFF_RETRIES

    def describe_tasks(*_args, **_kwargs):
        nonlocal retries
        nonlocal original_describe_tasks

        if retries > 1:
            return original_describe_tasks(*_args, **_kwargs)
        retries += 1
        return {"tasks": []}

    with pytest.raises(EcsEventualConsistencyTimeout):
        monkeypatch.setattr(instance.run_launcher.ecs, "describe_tasks", describe_tasks)
        monkeypatch.setattr(dagster_aws.ecs.tasks, "BACKOFF_RETRIES", 0)
        instance.launch_run(run.run_id, workspace)

    # Reset the mock
    retries = 0
    monkeypatch.setattr(dagster_aws.ecs.tasks, "BACKOFF_RETRIES", original_backoff_retries)
    instance.launch_run(run.run_id, workspace)

    tasks = ecs.list_tasks()["taskArns"]
    assert len(tasks) == len(initial_tasks) + 1

    # backoff fails for reasons unrelated to eventual consistency

    def exploding_describe_tasks(*_args, **_kwargs):
        raise Exception("boom")

    with pytest.raises(Exception, match="boom"):
        monkeypatch.setattr(instance.run_launcher.ecs, "describe_tasks", exploding_describe_tasks)
        instance.launch_run(run.run_id, workspace)


@pytest.mark.parametrize("assign_public_ip", [True, False])
def test_public_ip_assignment(ecs, ec2, instance, workspace, run, assign_public_ip):
    initial_tasks = ecs.list_tasks()["taskArns"]

    instance.launch_run(run.run_id, workspace)

    tasks = ecs.list_tasks()["taskArns"]
    task_arn = next(iter(set(tasks).difference(initial_tasks)))
    task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]
    attachment = task.get("attachments")[0]
    details = dict([(detail.get("name"), detail.get("value")) for detail in attachment["details"]])
    eni = ec2.NetworkInterface(details["networkInterfaceId"])
    attributes = eni.association_attribute or {}

    assert bool(attributes.get("PublicIp")) == assign_public_ip


def test_launcher_run_resources(
    ecs,
    instance_with_resources,
    workspace,
    external_job,
    job,
):
    instance = instance_with_resources
    run = instance.create_run_for_job(
        job,
        external_job_origin=external_job.get_external_origin(),
        job_code_origin=external_job.get_python_origin(),
    )

    existing_tasks = ecs.list_tasks()["taskArns"]

    instance.launch_run(run.run_id, workspace)

    tasks = ecs.list_tasks()["taskArns"]
    task_arn = next(iter(set(tasks).difference(existing_tasks)))
    task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]

    assert task.get("overrides").get("memory") == "2048"
    assert task.get("overrides").get("cpu") == "1024"


def test_launch_cannot_use_system_tags(instance_cm, workspace, job, external_job):
    with instance_cm(
        {
            "run_ecs_tags": [{"key": "dagster/run_id", "value": "NOPE"}],
        }
    ) as instance:
        run = instance.create_run_for_job(
            job,
            external_job_origin=external_job.get_external_origin(),
            job_code_origin=external_job.get_python_origin(),
        )
        with pytest.raises(Exception, match="Cannot override system ECS tag: dagster/run_id"):
            instance.launch_run(run.run_id, workspace)


def test_launch_run_with_container_context(
    ecs,
    instance,
    launch_run_with_container_context,
    container_context_config,
):
    existing_tasks = ecs.list_tasks()["taskArns"]

    launch_run_with_container_context(instance)

    tasks = ecs.list_tasks()["taskArns"]
    task_arn = next(iter(set(tasks).difference(existing_tasks)))
    task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]

    assert any(tag == {"key": "HAS_VALUE", "value": "SEE"} for tag in task["tags"])
    assert any(tag == {"key": "DOES_NOT_HAVE_VALUE"} for tag in task["tags"])
    assert any(
        tag == {"key": "ABC", "value": "DEF"} for tag in task["tags"]
    )  # from container context

    assert (
        task.get("overrides").get("memory")
        == container_context_config["ecs"]["run_resources"]["memory"]
    )
    assert (
        task.get("overrides").get("cpu") == container_context_config["ecs"]["run_resources"]["cpu"]
    )
    assert (
        task.get("overrides").get("ephemeralStorage").get("sizeInGiB")
        == container_context_config["ecs"]["run_resources"]["ephemeral_storage"]
    )

    task_definition_arn = task["taskDefinitionArn"]

    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)[
        "taskDefinition"
    ]

    container_definition = task_definition["containerDefinitions"][0]

    assert task_definition["taskRoleArn"] == container_context_config["ecs"]["task_role_arn"]
    assert (
        task_definition["executionRoleArn"] == container_context_config["ecs"]["execution_role_arn"]
    )
    assert task_definition["runtimePlatform"] == container_context_config["ecs"]["runtime_platform"]
    assert task_definition["cpu"] == container_context_config["ecs"]["run_resources"]["cpu"]
    assert task_definition["memory"] == container_context_config["ecs"]["run_resources"]["memory"]
    assert (
        task_definition["ephemeralStorage"]["sizeInGiB"]
        == container_context_config["ecs"]["run_resources"]["ephemeral_storage"]
    )
    assert task_definition["volumes"] == container_context_config["ecs"]["volumes"]

    assert container_definition["mountPoints"] == container_context_config["ecs"]["mount_points"]

    assert (
        container_definition["repositoryCredentials"]["credentialsParameter"]
        == container_context_config["ecs"]["repository_credentials"]
    )

    sidecar_container = task_definition["containerDefinitions"][1]
    assert sidecar_container["name"] == "busyrun"
    assert sidecar_container["image"] == "busybox:latest"


def test_memory_and_cpu(ecs, instance, workspace, run, task_definition):
    # By default
    initial_tasks = ecs.list_tasks()["taskArns"]

    instance.launch_run(run.run_id, workspace)

    tasks = ecs.list_tasks()["taskArns"]
    task_arn = next(iter(set(tasks).difference(initial_tasks)))
    task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]

    assert task.get("memory") == task_definition.get("memory")
    assert not task.get("overrides").get("memory")
    assert task.get("cpu") == task_definition.get("cpu")
    assert not task.get("overrides").get("cpu")

    # Override memory
    existing_tasks = ecs.list_tasks()["taskArns"]

    instance.add_run_tags(run.run_id, {"ecs/memory": "1024"})
    instance.launch_run(run.run_id, workspace)

    tasks = ecs.list_tasks()["taskArns"]
    task_arn = next(iter(set(tasks).difference(existing_tasks)))
    task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]

    assert task.get("memory") == task_definition.get("memory")
    # taskOverrides expects cpu/memory as strings
    assert task.get("overrides").get("memory") == "1024"
    # taskOverrides expects cpu/memory as integers
    assert task.get("overrides").get("containerOverrides")[0].get("memory") == 1024
    assert task.get("cpu") == task_definition.get("cpu")
    assert not task.get("overrides").get("cpu")
    assert not task.get("overrides").get("containerOverrides")[0].get("cpu")

    # Also override cpu
    existing_tasks = ecs.list_tasks()["taskArns"]

    instance.add_run_tags(run.run_id, {"ecs/cpu": "512"})
    instance.launch_run(run.run_id, workspace)

    tasks = ecs.list_tasks()["taskArns"]
    task_arn = next(iter(set(tasks).difference(existing_tasks)))
    task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]

    assert task.get("memory") == task_definition.get("memory")
    assert task.get("overrides").get("memory") == "1024"
    assert task.get("overrides").get("containerOverrides")[0].get("memory") == 1024
    assert task.get("cpu") == task_definition.get("cpu")
    assert task.get("overrides").get("cpu") == "512"
    assert task.get("overrides").get("containerOverrides")[0].get("cpu") == 512

    # Override with invalid constraints
    instance.add_run_tags(run.run_id, {"ecs/memory": "999"})
    with pytest.raises(ClientError):
        instance.launch_run(run.run_id, workspace)


def test_status(
    ecs,
    instance_with_log_group,
    job,
    external_job,
    cloudwatch_client,
    log_group,
):
    instance = instance_with_log_group

    run = instance.create_run_for_job(
        job,
        external_job_origin=external_job.get_external_origin(),
        job_code_origin=external_job.get_python_origin(),
        tags={RUN_WORKER_ID_TAG: "abcdef"},
    )

    instance.run_launcher.launch_run(LaunchRunContext(dagster_run=run, workspace=None))

    assert instance.run_launcher.logs == cloudwatch_client

    # Reach into StubbedEcs and grab the task
    # so we can modify its status. This is kind of complicated
    # right now so it might point toward a potential refactor of
    # our internal task data structure - maybe a dict of dicts
    # using cluster and arn as keys - instead of a dict of lists?
    task_arn = instance.get_run_by_id(run.run_id).tags["ecs/task_arn"]
    task = next(task for task in ecs.storage.tasks["default"] if task["taskArn"] == task_arn)

    task_id = task_arn.split("/")[-1]

    for status in RUNNING_STATUSES:
        task["lastStatus"] = status
        running_health_check = instance.run_launcher.check_run_worker_health(run)
        assert running_health_check.status == WorkerStatus.RUNNING

    for status in STOPPED_STATUSES:
        task["lastStatus"] = status

        task["containers"][0]["exitCode"] = 0
        assert instance.run_launcher.check_run_worker_health(run).status == WorkerStatus.SUCCESS

        task["containers"][0]["exitCode"] = 1
        # Without logs (or on a failure fetching logs) the health check sitll fails

        failure_health_check = instance.run_launcher.check_run_worker_health(run)
        assert failure_health_check.status == WorkerStatus.FAILED
        assert (
            failure_health_check.msg
            == f"Task {task_arn} failed.\nStop code: None.\nStop reason: None.\nContainer 'run'"
            " failed - exit code 1.\n"
        )

        assert not failure_health_check.transient
        assert failure_health_check.run_worker_id == "abcdef"

        # with logs, the failure includes the run worker logs

        family = instance.run_launcher._get_run_task_definition_family(run)  # noqa: SLF001
        log_stream = f"{family}/run/{task_id}"
        cloudwatch_client.create_log_stream(logGroupName=log_group, logStreamName=log_stream)

        cloudwatch_client.put_log_events(
            logGroupName=log_group,
            logStreamName=log_stream,
            logEvents=[
                {"timestamp": int(time.time() * 1000), "message": "Oops something bad happened"}
            ],
        )

        failure_health_check = instance.run_launcher.check_run_worker_health(run)
        assert failure_health_check.status == WorkerStatus.FAILED

        assert (
            failure_health_check.msg
            == f"Task {task_arn} failed.\nStop code: None.\nStop reason: None.\nContainer 'run'"
            " failed - exit code 1.\nRun worker logs:\nOops something bad happened"
        )

    task["lastStatus"] = "foo"
    unknown_health_check = instance.run_launcher.check_run_worker_health(run)
    assert unknown_health_check.status == WorkerStatus.UNKNOWN
    assert unknown_health_check.run_worker_id == "abcdef"

    task["lastStatus"] = "STOPPED"
    task["stoppedReason"] = "Timeout waiting for network interface provisioning to complete."

    started_health_check = instance.run_launcher.check_run_worker_health(run)
    assert started_health_check.status == WorkerStatus.FAILED
    assert not started_health_check.transient
    assert started_health_check.run_worker_id == "abcdef"

    task["stoppedReason"] = "Timeout waiting for EphemeralStorage provisioning to complete."

    started_health_check = instance.run_launcher.check_run_worker_health(run)
    assert started_health_check.status == WorkerStatus.FAILED
    assert not started_health_check.transient
    assert started_health_check.run_worker_id == "abcdef"

    task["stoppedReason"] = (
        "CannotPullContainerError: pull image manifest has been retried 5 time(s): Get"
        ' "https://myfakeimage:myfakemanifest":'
        " dial tcp 12.345.678.78:443: i/o timeout"
    )

    started_health_check = instance.run_launcher.check_run_worker_health(run)
    assert started_health_check.status == WorkerStatus.FAILED
    assert not started_health_check.transient
    assert started_health_check.run_worker_id == "abcdef"

    # STARTING runs with these errors are considered a transient failure that can be retried
    starting_run = instance.create_run_for_job(
        job,
        external_job_origin=external_job.get_external_origin(),
        job_code_origin=external_job.get_python_origin(),
        status=DagsterRunStatus.STARTING,
        tags={RUN_WORKER_ID_TAG: "efghi"},
    )
    instance.run_launcher.launch_run(LaunchRunContext(dagster_run=starting_run, workspace=None))
    task_arn = instance.get_run_by_id(starting_run.run_id).tags["ecs/task_arn"]
    task = next(task for task in ecs.storage.tasks["default"] if task["taskArn"] == task_arn)
    task["lastStatus"] = "STOPPED"
    task["stoppedReason"] = "Timeout waiting for network interface provisioning to complete."

    starting_health_check = instance.run_launcher.check_run_worker_health(starting_run)
    assert starting_health_check.status == WorkerStatus.FAILED
    assert starting_health_check.transient
    assert starting_health_check.run_worker_id == "efghi"


def test_overrides_too_long(
    instance,
    workspace,
    job,
    external_job,
):
    large_container_context = {i: "boom" for i in range(10000)}

    mock_job_code_origin = JobPythonOrigin(
        job_name="test",
        repository_origin=RepositoryPythonOrigin(
            executable_path="/",
            code_pointer=FileCodePointer(
                python_file="foo.py",
                fn_name="foo",
            ),
            container_image="test:latest",
            container_context=large_container_context,
        ),
    )

    run = instance.create_run_for_job(
        job,
        external_job_origin=external_job.get_external_origin(),
        job_code_origin=mock_job_code_origin,
    )

    instance.launch_run(run.run_id, workspace)


def test_custom_launcher(
    ecs,
    custom_instance,
    custom_workspace,
    custom_run,
):
    assert not custom_run.tags

    initial_tasks = ecs.list_tasks()["taskArns"]

    custom_instance.launch_run(custom_run.run_id, custom_workspace)

    tasks = ecs.list_tasks()["taskArns"]
    task_arn = next(iter(set(tasks).difference(initial_tasks)))

    # And we log
    events = custom_instance.event_log_storage.get_logs_for_run(custom_run.run_id)
    latest_event = events[-1]
    assert latest_event.message == "Launching run in custom ECS task"
    metadata = latest_event.dagster_event.engine_event_data.metadata
    assert metadata["Run ID"] == MetadataValue.text(custom_run.run_id)

    # check status and stop task
    assert (
        custom_instance.run_launcher.check_run_worker_health(custom_run).status
        == WorkerStatus.RUNNING
    )
    ecs.stop_task(task=task_arn)


def test_external_launch_type(
    ecs,
    instance_cm,
    workspace,
    external_job,
    job,
):
    container_name = "external"

    task_definition = ecs.register_task_definition(
        family="external",
        containerDefinitions=[{"name": container_name, "image": "dagster:first"}],
        networkMode="bridge",
        memory="512",
        cpu="256",
    )["taskDefinition"]

    assert task_definition["networkMode"] == "bridge"

    task_definition_arn = task_definition["taskDefinitionArn"]

    # You can provide a family or a task definition ARN
    with instance_cm(
        {
            "task_definition": task_definition_arn,
            "container_name": container_name,
            "run_task_kwargs": {
                "launchType": "EXTERNAL",
            },
        }
    ) as instance:
        run = instance.create_run_for_job(
            job,
            external_job_origin=external_job.get_external_origin(),
            job_code_origin=external_job.get_python_origin(),
        )

        initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
        initial_tasks = ecs.list_tasks()["taskArns"]

        instance.launch_run(run.run_id, workspace)

        # A new task definition is not created
        assert ecs.list_task_definitions()["taskDefinitionArns"] == initial_task_definitions

        # A new task is launched
        tasks = ecs.list_tasks()["taskArns"]

        assert len(tasks) == len(initial_tasks) + 1
        task_arn = next(iter(set(tasks).difference(initial_tasks)))
        task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]

        assert task["taskDefinitionArn"] == task_definition["taskDefinitionArn"]
        assert task["launchType"] == "EXTERNAL"
