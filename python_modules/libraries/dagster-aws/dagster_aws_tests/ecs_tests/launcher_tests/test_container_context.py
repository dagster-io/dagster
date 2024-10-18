import pytest
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.test_utils import environ

from dagster_aws.ecs.container_context import EcsContainerContext


@pytest.fixture
def empty_container_context():
    return EcsContainerContext()


@pytest.fixture
def secrets_container_context(container_context_config):
    return EcsContainerContext.create_from_config(container_context_config)


@pytest.fixture
def other_secrets_container_context(other_container_context_config):
    return EcsContainerContext.create_from_config(other_container_context_config)


def test_empty_container_context(empty_container_context):
    assert empty_container_context.secrets == []
    assert empty_container_context.secrets_tags == []
    assert empty_container_context.env_vars == []


def test_invalid_config():
    with pytest.raises(
        DagsterInvalidConfigError, match="Errors while parsing ECS container context"
    ):
        EcsContainerContext.create_from_config(
            {"ecs": {"secrets": {"foo": "bar"}}}
        )  # invalid formatting


def test_merge(
    empty_container_context,
    secrets_container_context,
    other_secrets_container_context,
    configured_secret,
    other_configured_secret,
):
    assert secrets_container_context.secrets == [
        {"name": "HELLO", "valueFrom": configured_secret.arn + "/hello"},
    ]
    assert secrets_container_context.secrets_tags == ["dagster"]
    assert secrets_container_context.get_environment_dict() == {
        "FOO_ENV_VAR": "BAR_VALUE",
        "SHARED_KEY": "SHARED_VAL",
    }

    assert secrets_container_context.container_name == "foo"

    assert other_secrets_container_context.secrets == [
        {"name": "GOODBYE", "valueFrom": other_configured_secret.arn + "/goodbye"},
    ]

    assert other_secrets_container_context.secrets_tags == ["other_secret_tag"]

    assert other_secrets_container_context.container_name == "bar"

    with pytest.raises(
        Exception, match="Tried to load environment variable OTHER_FOO_ENV_VAR, but it was not set"
    ):
        other_secrets_container_context.get_environment_dict()

    with environ({"OTHER_FOO_ENV_VAR": "OTHER_BAR_VALUE"}):
        assert other_secrets_container_context.get_environment_dict() == {
            "OTHER_FOO_ENV_VAR": "OTHER_BAR_VALUE",
            "SHARED_OTHER_KEY": "SHARED_OTHER_VAL",
        }

    merged = secrets_container_context.merge(other_secrets_container_context)

    assert merged.secrets == [
        {"name": "GOODBYE", "valueFrom": other_configured_secret.arn + "/goodbye"},
        {"name": "HELLO", "valueFrom": configured_secret.arn + "/hello"},
    ]

    assert merged.secrets_tags == ["other_secret_tag", "dagster"]

    assert merged.container_name == "bar"

    assert merged.run_resources == {"cpu": "256", "memory": "8192", "ephemeral_storage": 100}
    assert merged.server_resources == {
        "cpu": "2048",
        "memory": "4096",
        "ephemeral_storage": 25,
        "replica_count": 2,
    }

    assert merged.server_ecs_tags == [
        {"key": "BAZ", "value": "QUUX"},
        {
            "key": "FOO",  # no value
        },
    ]
    assert merged.run_ecs_tags == [{"key": "GHI"}, {"key": "ABC", "value": "DEF"}]

    assert merged.task_role_arn == "other-task-role"
    assert merged.execution_role_arn == "other-fake-execution-role"

    assert merged.mount_points == [
        {
            "sourceVolume": "myOtherEfsVolume",
            "containerPath": "/mount/other/efs",
            "readOnly": True,
        },
        {
            "sourceVolume": "myEfsVolume",
            "containerPath": "/mount/efs",
            "readOnly": True,
        },
    ]

    assert merged.repository_credentials == "fake-secret-arn"

    assert merged.volumes == [
        {
            "name": "myOtherEfsVolume",
            "efsVolumeConfiguration": {
                "fileSystemId": "fs-5678",
                "rootDirectory": "/path/to/my/other/data",
            },
        },
        {
            "name": "myEfsVolume",
            "efsVolumeConfiguration": {
                "fileSystemId": "fs-1234",
                "rootDirectory": "/path/to/my/data",
            },
        },
    ]

    assert merged.server_sidecar_containers == [
        {
            "name": "OtherServerAgent",
            "image": "public.ecr.aws/other/agent:latest",
        },
        {
            "name": "DatadogAgent",
            "image": "public.ecr.aws/datadog/agent:latest",
            "environment": [
                {"name": "ECS_FARGATE", "value": "true"},
            ],
        },
    ]
    assert merged.server_health_check == other_secrets_container_context.server_health_check
    assert merged.run_sidecar_containers == [
        {
            "name": "OtherRunAgent",
            "image": "otherrun:latest",
        },
        {
            "name": "busyrun",
            "image": "busybox:latest",
        },
    ]

    with pytest.raises(
        Exception, match="Tried to load environment variable OTHER_FOO_ENV_VAR, but it was not set"
    ):
        merged.get_environment_dict()

    with environ({"OTHER_FOO_ENV_VAR": "OTHER_BAR_VALUE"}):
        assert merged.get_environment_dict() == {
            "FOO_ENV_VAR": "BAR_VALUE",
            "OTHER_FOO_ENV_VAR": "OTHER_BAR_VALUE",
            "SHARED_KEY": "SHARED_VAL",
            "SHARED_OTHER_KEY": "SHARED_OTHER_VAL",
        }

    assert (
        empty_container_context.merge(secrets_container_context).secrets
        == secrets_container_context.secrets
    )
    assert (
        empty_container_context.merge(secrets_container_context).secrets_tags
        == secrets_container_context.secrets_tags
    )
