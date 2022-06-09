import pytest


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
        with instance_cm(config={"run_task_kwargs": {"foo": "bar"}}):
            pass

    with pytest.raises(Exception):
        with instance_cm(
            config={"taskDefinition": "my-task-def"},
            match="Use the `taskDefinition` config field to pass in a task definition to run",
        ):
            pass

    with pytest.raises(Exception):
        with instance_cm(
            config={"overrides": {"containerOverrides": {}}},
            match="Task overrides are set by the run launcher and cannot be set in run_task_kwargs.",
        ):
            pass
