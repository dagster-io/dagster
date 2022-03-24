# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=unused-variable
import json
from collections import namedtuple
from unittest.mock import MagicMock, patch

import pytest

Secret = namedtuple("Secret", ["name", "arn"])


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
def configured_secret(secrets_manager):
    # A secret explicitly included in the launcher config
    name = "configured_secret"
    arn = secrets_manager.create_secret(
        Name=name,
        SecretString=json.dumps({"hello": "world"}),
    )["ARN"]

    yield Secret(name, arn)


def test_secrets(
    ecs,
    secrets_manager,
    instance_cm,
    launch_run,
    tagged_secret,
    other_secret,
    configured_secret,
):
    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]

    config = {
        "secrets": [
            {
                "name": "HELLO",
                "valueFrom": configured_secret.arn + "/hello",
            }
        ],
    }

    with instance_cm(config) as instance:
        launch_run(instance)

    # A new task definition is created
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_definitions) == len(initial_task_definitions) + 1
    task_definition_arn = list(set(task_definitions).difference(initial_task_definitions))[0]
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)
    task_definition = task_definition["taskDefinition"]

    # It includes tagged secrets
    secrets = task_definition["containerDefinitions"][0]["secrets"]
    assert {"name": tagged_secret.name, "valueFrom": tagged_secret.arn} in secrets

    # And configured secrets
    assert {
        "name": "HELLO",
        "valueFrom": configured_secret.arn + "/hello",
    } in secrets

    # But no other secrets
    assert len(secrets) == 2


def test_secrets_backcompat(
    ecs,
    secrets_manager,
    instance_cm,
    launch_run,
    tagged_secret,
    other_secret,
    configured_secret,
):
    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]

    with pytest.warns(DeprecationWarning, match="Setting secrets as a list of ARNs is deprecated"):
        with instance_cm({"secrets": [configured_secret.arn]}) as instance:
            launch_run(instance)

    # A new task definition is created
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_definitions) == len(initial_task_definitions) + 1
    task_definition_arn = list(set(task_definitions).difference(initial_task_definitions))[0]
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)
    task_definition = task_definition["taskDefinition"]

    # It includes tagged secrets
    secrets = task_definition["containerDefinitions"][0]["secrets"]
    assert {"name": tagged_secret.name, "valueFrom": tagged_secret.arn} in secrets

    # And configured secrets
    assert {"name": configured_secret.name, "valueFrom": configured_secret.arn} in secrets

    # But no other secrets
    assert len(secrets) == 2


def test_empty_secrets(
    ecs,
    secrets_manager,
    instance_cm,
    launch_run,
):
    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]

    with instance_cm({"secrets_tag": None}) as instance:
        m = MagicMock()
        with patch.object(instance.run_launcher, "secrets_manager", new=m):
            launch_run(instance)

        m.get_paginator.assert_not_called()
        m.describe_secret.assert_not_called()

    # A new task definition is created
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_definitions) == len(initial_task_definitions) + 1
    task_definition_arn = list(set(task_definitions).difference(initial_task_definitions))[0]
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)
    task_definition = task_definition["taskDefinition"]

    # No secrets
    assert not task_definition["containerDefinitions"][0].get("secrets")
