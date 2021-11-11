# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=unused-variable
from collections import namedtuple

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


def test_secrets(ecs, secrets_manager, instance, workspace, run, tagged_secret, other_secret):
    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]

    instance.launch_run(run.run_id, workspace)

    # A new task definition is created
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_definitions) == len(initial_task_definitions) + 1
    task_definition_arn = list(set(task_definitions).difference(initial_task_definitions))[0]
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)
    task_definition = task_definition["taskDefinition"]

    # It includes tagged secrets
    secrets = task_definition["containerDefinitions"][0]["secrets"]
    assert len(secrets) == 1
    assert {"name": tagged_secret.name, "valueFrom": tagged_secret.arn} in secrets
