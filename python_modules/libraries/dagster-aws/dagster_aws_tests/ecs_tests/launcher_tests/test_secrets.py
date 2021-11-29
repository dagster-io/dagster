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


@pytest.fixture
def configured_secret(secrets_manager):
    # A secret explicitly included in the launcher config
    name = "configured_secret"
    arn = secrets_manager.create_secret(
        Name=name,
        SecretString="hello",
    )["ARN"]

    yield Secret(name, arn)


@pytest.fixture
def instance(instance_cm, configured_secret):
    config = {"secrets": [configured_secret.arn]}
    with instance_cm(config) as dagster_instance:
        yield dagster_instance


def test_secrets(
    ecs, secrets_manager, instance, workspace, run, tagged_secret, other_secret, configured_secret
):
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
    assert {"name": tagged_secret.name, "valueFrom": tagged_secret.arn} in secrets

    # And configured secrets
    assert {"name": configured_secret.name, "valueFrom": configured_secret.arn} in secrets

    # But no other secrets
    assert len(secrets) == 2
