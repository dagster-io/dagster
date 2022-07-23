# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=unused-variable
from unittest.mock import MagicMock, patch

import pytest

from dagster.core.test_utils import environ


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


def test_environment(
    ecs,
    instance_cm,
    launch_run,
):
    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]

    config = {"env_vars": ["FOO_ENV_VAR=BAR_VALUE"]}

    with instance_cm(config) as instance:
        launch_run(instance)

    # A new task definition is created
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_definitions) == len(initial_task_definitions) + 1
    task_definition_arn = list(set(task_definitions).difference(initial_task_definitions))[0]
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)
    task_definition = task_definition["taskDefinition"]

    # It includes the environment
    environment = task_definition["containerDefinitions"][0]["environment"]
    assert {"name": "FOO_ENV_VAR", "value": "BAR_VALUE"} in environment


def test_environment_missing_env_var_value(
    ecs,
    instance_cm,
    launch_run,
):
    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]

    config = {"env_vars": ["FOO_ENV_VAR"]}

    with instance_cm(config) as instance:
        with pytest.raises(
            Exception, match="Tried to load environment variable FOO_ENV_VAR, but it was not set"
        ):
            launch_run(instance)

        with environ({"FOO_ENV_VAR": "BAR_VALUE"}):
            launch_run(instance)

    # A new task definition is created
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_definitions) == len(initial_task_definitions) + 1
    task_definition_arn = list(set(task_definitions).difference(initial_task_definitions))[0]
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)
    task_definition = task_definition["taskDefinition"]

    # It includes the environment
    environment = task_definition["containerDefinitions"][0]["environment"]
    assert {"name": "FOO_ENV_VAR", "value": "BAR_VALUE"} in environment


def test_secrets_with_container_context(
    ecs,
    secrets_manager,
    instance_cm,
    launch_run_with_container_context,
    tagged_secret,
    other_secret,
    configured_secret,
):
    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]

    # Secrets config is pulled from container context on the run, rather than run launcher config
    config = {"secrets_tag": None, "secrets": []}

    with instance_cm(config) as instance:
        launch_run_with_container_context(instance)

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


def test_environment_with_container_context(
    ecs,
    instance_cm,
    launch_run_with_container_context,
):
    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]

    # Secrets config is pulled from container context on the run, rather than run launcher config
    config = {"env_vars": ["RUN_LAUNCHER_NAME=RUN_LAUNCHER_VALUE"]}

    with instance_cm(config) as instance:
        launch_run_with_container_context(instance)

    # A new task definition is created
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_definitions) == len(initial_task_definitions) + 1
    task_definition_arn = list(set(task_definitions).difference(initial_task_definitions))[0]
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)
    task_definition = task_definition["taskDefinition"]

    # It includes environment from run launcher
    environment = task_definition["containerDefinitions"][0]["environment"]

    assert {"name": "RUN_LAUNCHER_NAME", "value": "RUN_LAUNCHER_VALUE"} in environment

    # And container context
    assert {
        "name": "FOO_ENV_VAR",
        "value": "BAR_VALUE",
    } in environment


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
