# pylint: disable=redefined-outer-name

import pytest
from dagster_aws.ecs.container_context import EcsContainerContext

from dagster.core.errors import DagsterInvalidConfigError


@pytest.fixture
def empty_container_context():
    return EcsContainerContext()


@pytest.fixture
def secrets_container_context(container_context_config):
    return EcsContainerContext.create_from_config(container_context_config)


@pytest.fixture
def other_secrets_container_context(other_container_context_config):
    return EcsContainerContext.create_from_config(other_container_context_config)


@pytest.fixture
def environment_container_context(environment_container_context_config):
    return EcsContainerContext.create_from_config(environment_container_context_config)


@pytest.fixture
def other_environment_container_context(other_environment_container_context_config):
    return EcsContainerContext.create_from_config(other_environment_container_context_config)


def test_empty_container_context(empty_container_context):
    assert empty_container_context.secrets == []
    assert empty_container_context.secrets_tags == []
    assert empty_container_context.environment == []


def test_invalid_config():
    with pytest.raises(
        DagsterInvalidConfigError, match="Errors while parsing ECS container context"
    ):
        EcsContainerContext.create_from_config(
            {"ecs": {"secrets": {"foo": "bar"}}}
        )  # invalid formatting

    with pytest.raises(
        DagsterInvalidConfigError, match="Errors while parsing ECS container context"
    ):
        EcsContainerContext.create_from_config(
            {"ecs": {"environment": {"foo": "bar"}}}
        )  # invalid formatting


def test_merge(
    empty_container_context,
    secrets_container_context,
    other_secrets_container_context,
    configured_secret,
    other_configured_secret,
    environment_container_context,
    other_environment_container_context,
):
    assert secrets_container_context.secrets == [
        {"name": "HELLO", "valueFrom": configured_secret.arn + "/hello"},
    ]
    assert secrets_container_context.secrets_tags == ["dagster"]

    assert other_secrets_container_context.secrets == [
        {"name": "GOODBYE", "valueFrom": other_configured_secret.arn + "/goodbye"},
    ]

    assert other_secrets_container_context.secrets_tags == ["other_secret_tag"]

    assert environment_container_context.environment == [{"name": "FOO", "value": "BAR"}]

    assert other_environment_container_context.environment == [
        {"name": "Hello", "value": "Goodbye"},
        {"name": "FOO", "value": "BAZ"},
    ]

    merged = other_secrets_container_context.merge(secrets_container_context)

    assert merged.secrets == [
        {"name": "HELLO", "valueFrom": configured_secret.arn + "/hello"},
        {"name": "GOODBYE", "valueFrom": other_configured_secret.arn + "/goodbye"},
    ]

    assert merged.secrets_tags == ["dagster", "other_secret_tag"]

    assert (
        empty_container_context.merge(secrets_container_context).secrets
        == secrets_container_context.secrets
    )
    assert (
        empty_container_context.merge(secrets_container_context).secrets_tags
        == secrets_container_context.secrets_tags
    )

    merged = merged.merge(environment_container_context)

    assert (
        merged.environment
        == environment_container_context.environment + secrets_container_context.environment
    )

    merged = merged.merge(other_environment_container_context)

    assert len(merged.environment) == 4
    assert merged.environment == [
        {"name": "Hello", "value": "Goodbye"},
        {"name": "FOO", "value": "BAZ"},
        {"name": "FOO", "value": "BAR"},
        {"name": "foo", "value": "bar"},
    ]
