# pylint: disable=protected-access
# pylint: disable=unused-variable
import dagster_aws
import pytest
from botocore.exceptions import ClientError
from dagster_aws.ecs import EcsEventualConsistencyTimeout

from dagster.check import CheckError
from dagster.core.events import MetadataEntry


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
    task_definition_arn = list(set(task_definitions).difference(initial_task_definitions))[0]
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)
    task_definition = task_definition["taskDefinition"]

    # It has a new family, name, and image
    # We get the family name from the location name. With the InProcessExecutor that we use in tests,
    # the location name is always <<in_process>>. And we sanitize it so it's compatible with the ECS API.
    assert task_definition["family"] == "in_process"
    assert len(task_definition["containerDefinitions"]) == 1
    container_definition = task_definition["containerDefinitions"][0]
    assert container_definition["name"] == "run"
    assert container_definition["image"] == image
    assert not container_definition.get("entryPoint")
    assert not container_definition.get("dependsOn")
    # But other stuff is inhereted from the parent task definition
    assert container_definition["environment"] == environment

    # A new task is launched
    tasks = ecs.list_tasks()["taskArns"]
    assert len(tasks) == len(initial_tasks) + 1
    task_arn = list(set(tasks).difference(initial_tasks))[0]
    task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]
    assert subnet.id in str(task)
    assert task["taskDefinitionArn"] == task_definition["taskDefinitionArn"]

    # The run is tagged with info about the ECS task
    assert instance.get_run_by_id(run.run_id).tags["ecs/task_arn"] == task_arn
    cluster_arn = ecs._cluster_arn("default")
    assert instance.get_run_by_id(run.run_id).tags["ecs/cluster"] == cluster_arn

    # If we're using the new long ARN format,
    # the ECS task is tagged with info about the Dagster run
    if task_long_arn_format == "enabled":
        assert (
            ecs.list_tags_for_resource(resourceArn=task_arn)["tags"][0]["key"] == "dagster/run_id"
        )
        assert ecs.list_tags_for_resource(resourceArn=task_arn)["tags"][0]["value"] == run.run_id

    # We set pipeline-specific overides
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
    event_metadata = latest_event.dagster_event.engine_event_data.metadata_entries
    assert MetadataEntry("ECS Task ARN", value=task_arn) in event_metadata
    assert MetadataEntry("ECS Cluster", value=cluster_arn) in event_metadata
    assert MetadataEntry("Run ID", value=run.run_id) in event_metadata


def test_task_definition_registration(
    ecs, instance, workspace, run, other_workspace, other_run, secrets_manager
):
    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    initial_tasks = ecs.list_tasks()["taskArns"]

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


def test_launching_custom_task_definition(
    ecs, instance_cm, run, workspace, pipeline, external_pipeline
):
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
    with pytest.raises(Exception), instance_cm({"task_definition": "does not exist"}):
        pass

    # The task definition doesn't include the default container name
    with pytest.raises(CheckError), instance_cm({"task_definition": family}):
        pass

    # The task definition doesn't include the container name
    with pytest.raises(CheckError), instance_cm(
        {"task_definition": family, "container_name": "does not exist"}
    ):
        pass

    # You can provide a family or a task definition ARN
    with instance_cm(
        {"task_definition": task_definition_arn, "container_name": container_name}
    ) as instance:

        run = instance.create_run_for_pipeline(
            pipeline,
            external_pipeline_origin=external_pipeline.get_external_origin(),
            pipeline_code_origin=external_pipeline.get_python_origin(),
        )

        initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
        initial_tasks = ecs.list_tasks()["taskArns"]

        instance.launch_run(run.run_id, workspace)

        # A new task definition is not created
        assert ecs.list_task_definitions()["taskDefinitionArns"] == initial_task_definitions

        # A new task is launched
        tasks = ecs.list_tasks()["taskArns"]
        assert len(tasks) == len(initial_tasks) + 1
        task_arn = list(set(tasks).difference(initial_tasks))[0]
        task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]
        assert task["taskDefinitionArn"] == task_definition["taskDefinitionArn"]

        # We set pipeline-specific overides
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
    task_arn = list(set(tasks).difference(initial_tasks))[0]
    task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]
    attachment = task.get("attachments")[0]
    details = dict([(detail.get("name"), detail.get("value")) for detail in attachment["details"]])
    eni = ec2.NetworkInterface(details["networkInterfaceId"])
    attributes = eni.association_attribute or {}

    assert bool(attributes.get("PublicIp")) == assign_public_ip


def test_memory_and_cpu(ecs, instance, workspace, run, task_definition):
    # By default
    initial_tasks = ecs.list_tasks()["taskArns"]

    instance.launch_run(run.run_id, workspace)

    tasks = ecs.list_tasks()["taskArns"]
    task_arn = list(set(tasks).difference(initial_tasks))[0]
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
    task_arn = list(set(tasks).difference(existing_tasks))[0]
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
    task_arn = list(set(tasks).difference(existing_tasks))[0]
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
