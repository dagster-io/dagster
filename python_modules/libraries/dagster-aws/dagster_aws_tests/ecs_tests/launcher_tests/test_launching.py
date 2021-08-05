# pylint: disable=protected-access
import dagster_aws
import pytest
from dagster.check import CheckError
from dagster_aws.ecs import EcsEventualConsistencyTimeout


def test_default_launcher(
    ecs,
    instance,
    workspace,
    run,
    subnet,
    network_interface,
    image,
    environment,
):
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
    assert task_definition["family"] == "dagster-run"
    assert len(task_definition["containerDefinitions"]) == 1
    container_definition = task_definition["containerDefinitions"][0]
    assert container_definition["name"] == "run"
    assert container_definition["image"] == image
    assert not container_definition.get("entryPoint")
    # But other stuff is inhereted from the parent task definition
    assert container_definition["environment"] == environment

    # A new task is launched
    tasks = ecs.list_tasks()["taskArns"]
    assert len(tasks) == len(initial_tasks) + 1
    task_arn = list(set(tasks).difference(initial_tasks))[0]
    task = ecs.describe_tasks(tasks=[task_arn])["tasks"][0]
    assert subnet.id in str(task)
    assert network_interface.id in str(task)
    assert task["taskDefinitionArn"] == task_definition["taskDefinitionArn"]

    # The run is tagged with info about the ECS task
    assert instance.get_run_by_id(run.run_id).tags["ecs/task_arn"] == task_arn
    assert instance.get_run_by_id(run.run_id).tags["ecs/cluster"] == ecs._cluster_arn("default")

    # And the ECS task is tagged with info about the Dagster run
    assert ecs.list_tags_for_resource(resourceArn=task_arn)["tags"][0]["key"] == "dagster/run_id"
    assert ecs.list_tags_for_resource(resourceArn=task_arn)["tags"][0]["value"] == run.run_id

    # We set pipeline-specific overides
    overrides = task["overrides"]["containerOverrides"]
    assert len(overrides) == 1
    override = overrides[0]
    assert override["name"] == "run"
    assert "execute_run" in override["command"]
    assert run.run_id in str(override["command"])


def test_launching_custom_task_definition(
    ecs, instance_cm, run, workspace, pipeline, external_pipeline
):
    container_name = "override_container"

    task_definition = ecs.register_task_definition(
        family="override",
        containerDefinitions=[{"name": container_name, "image": "hello_world:latest"}],
        networkMode="bridge",
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
    original_backoff_retries = dagster_aws.ecs.launcher.BACKOFF_RETRIES

    def describe_tasks(*_args, **_kwargs):
        nonlocal retries
        nonlocal original_describe_tasks

        if retries > 1:
            return original_describe_tasks(*_args, **_kwargs)
        retries += 1
        return {"tasks": []}

    with pytest.raises(EcsEventualConsistencyTimeout):
        monkeypatch.setattr(instance.run_launcher.ecs, "describe_tasks", describe_tasks)
        monkeypatch.setattr(dagster_aws.ecs.launcher, "BACKOFF_RETRIES", 0)
        instance.launch_run(run.run_id, workspace)

    # Reset the mock
    retries = 0
    monkeypatch.setattr(dagster_aws.ecs.launcher, "BACKOFF_RETRIES", original_backoff_retries)
    instance.launch_run(run.run_id, workspace)

    tasks = ecs.list_tasks()["taskArns"]
    assert len(tasks) == len(initial_tasks) + 1

    # backoff fails for reasons unrelated to eventual consistency

    def exploding_describe_tasks(*_args, **_kwargs):
        raise Exception("boom")

    with pytest.raises(Exception, match="boom"):
        monkeypatch.setattr(instance.run_launcher.ecs, "describe_tasks", exploding_describe_tasks)
        instance.launch_run(run.run_id, workspace)
