from unittest.mock import MagicMock, call, patch

import pytest
from dagster import build_op_context
from dagster_wandb import wandb_resource
from dagster_wandb.launch.ops import raise_on_invalid_config, run_launch_agent, run_launch_job

WANDB_PROJECT = "project"
WANDB_ENTITY = "entity"
LAUNCH_QUEUE = "my_queue"
ERROR_REGEX = r".*dagster_wandb.*"
wandb_resource_configured = wandb_resource.configured(
    {
        "api_key": "WANDB_API_KEY",
    }
)


@pytest.fixture
def launch_mock():
    with patch(
        "dagster_wandb.launch.ops.launch",
    ) as mock:
        yield mock


@pytest.fixture
def launch_add_mock():
    with patch(
        "dagster_wandb.launch.ops.launch_add",
    ) as mock:
        yield mock


def test_raise_on_invalid_config_raises_on_empty_entity():
    context = build_op_context(
        resources={
            "wandb_config": {"entity": "", "project": WANDB_PROJECT},
            "wandb_resource": MagicMock(),
        },
    )

    with pytest.raises(RuntimeError, match=ERROR_REGEX):
        raise_on_invalid_config(context)


def test_raise_on_invalid_config_raises_on_empty_project():
    context = build_op_context(
        resources={
            "wandb_config": {"entity": WANDB_ENTITY, "project": ""},
            "wandb_resource": MagicMock(),
        },
    )

    with pytest.raises(RuntimeError, match=ERROR_REGEX):
        raise_on_invalid_config(context)


def test_run_launch_agent_with_simple_config(launch_mock):
    wandb_resource_mock = MagicMock()
    context = build_op_context(
        resources={
            "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
            "wandb_resource": wandb_resource_mock,
        },
    )
    run_launch_agent(context)
    launch_mock.create_and_run_agent.assert_called_with(
        api=wandb_resource_mock.__getitem__.return_value,
        config={"entity": "entity", "project": "project"},
    )
    wandb_resource_mock.__getitem__.assert_has_calls(
        [
            call("api"),
        ],
    )


def test_run_launch_agent_with_complex_config(launch_mock):
    wandb_resource_mock = MagicMock()
    context = build_op_context(
        config={
            "queues": ["first_queue", "second_queue"],
            "max_jobs": 42,
        },
        resources={
            "wandb_config": {
                "entity": WANDB_ENTITY,
                "project": WANDB_PROJECT,
            },
            "wandb_resource": wandb_resource_mock,
        },
    )
    run_launch_agent(context)
    launch_mock.create_and_run_agent.assert_called_with(
        api=wandb_resource_mock.__getitem__.return_value,
        config={
            "entity": WANDB_ENTITY,
            "project": WANDB_PROJECT,
            "queues": ["first_queue", "second_queue"],
            "max_jobs": 42,
        },
    )
    wandb_resource_mock.__getitem__.assert_has_calls(
        [
            call("api"),
        ],
    )


def test_run_launch_job_on_queue_synchronously(launch_mock, launch_add_mock):
    wandb_resource_mock = MagicMock()
    context = build_op_context(
        config={
            "queue": LAUNCH_QUEUE,
        },
        resources={
            "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
            "wandb_resource": wandb_resource_mock,
        },
    )
    run_launch_job(context)
    assert launch_mock.run.call_count == 0
    launch_add_mock.assert_called_with(
        entity=WANDB_ENTITY, project=WANDB_PROJECT, queue=LAUNCH_QUEUE
    )
    assert launch_add_mock.return_value.wait_until_finished.call_count == 1


def test_run_launch_job_locally(launch_mock, launch_add_mock):
    wandb_resource_mock = MagicMock()
    context = build_op_context(
        resources={
            "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
            "wandb_resource": wandb_resource_mock,
        },
    )
    run_launch_job(context)
    launch_mock.run.assert_called_with(
        api=wandb_resource_mock.__getitem__.return_value,
        config={"entity": WANDB_ENTITY, "project": WANDB_PROJECT, "synchronous": True},
    )
    assert launch_add_mock.call_count == 0
    assert launch_add_mock.return_value.wait_until_finished.call_count == 0
