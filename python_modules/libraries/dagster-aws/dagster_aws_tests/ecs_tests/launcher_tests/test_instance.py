import pytest
from dagster._core.test_utils import environ


def test_default_instance(instance_cm):
    with instance_cm() as instance:
        assert instance.run_launcher.use_current_ecs_task_config
        assert instance.run_launcher.run_task_kwargs == {}


def test_run_task_kwargs(instance_cm):
    run_task_kwargs = {
        "launchType": "EC2",
    }

    with instance_cm(
        config={
            "run_task_kwargs": run_task_kwargs,
        }
    ) as instance:
        assert instance.run_launcher.run_task_kwargs == run_task_kwargs


def test_invalid_kwargs_field(instance_cm):
    with pytest.raises(Exception, match="Found an unexpected key foo in run_task_kwargs"):
        with instance_cm(config={"run_task_kwargs": {"foo": "bar"}}) as instance:
            print(instance.run_launcher)  # noqa: T201

    with pytest.raises(Exception):
        with instance_cm(
            config={"taskDefinition": "my-task-def"},
            match="Use the `taskDefinition` config field to pass in a task definition to run",
        ) as instance:
            print(instance.run_launcher)  # noqa: T201

    with pytest.raises(Exception):
        with instance_cm(
            config={"overrides": {"containerOverrides": {}}},
            match=(
                "Task overrides are set by the run launcher and cannot be set in run_task_kwargs."
            ),
        ) as instance:
            print(instance.run_launcher)  # noqa: T201


def test_task_definition_config(instance_cm, task_definition):
    with instance_cm(
        config={"task_definition": "dagster", "container_name": "dagster"}
    ) as instance:
        assert instance.run_launcher.task_definition == task_definition["taskDefinitionArn"]

    with pytest.raises(
        Exception,
        match="You have attempted to fetch the environment variable FOO which is not set.",
    ):
        with instance_cm(
            config={"task_definition": {"env": "FOO"}, "container_name": "dagster"}
        ) as instance:
            print(instance.run_launcher)  # noqa: T201

    with environ({"FOO": "dagster"}):
        with instance_cm(
            config={"task_definition": {"env": "FOO"}, "container_name": "dagster"}
        ) as instance:
            assert instance.run_launcher.task_definition == task_definition["taskDefinitionArn"]
