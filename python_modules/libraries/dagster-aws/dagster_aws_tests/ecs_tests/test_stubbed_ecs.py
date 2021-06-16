import pytest
from botocore.exceptions import ClientError


def test_describe_task_definition(ecs):
    with pytest.raises(ClientError):
        # The task definition doesn't exist
        ecs.describe_task_definition(taskDefinition="dagster")

    dagster1 = ecs.register_task_definition(
        family="dagster",
        containerDefinitions=[{"image": "hello_world:latest"}],
        networkMode="bridge",
    )
    dagster2 = ecs.register_task_definition(
        family="dagster",
        containerDefinitions=[{"image": "hello_world:latest"}],
    )

    # It gets the latest revision
    assert ecs.describe_task_definition(taskDefinition="dagster") == dagster2
    # It gets the specific revision
    assert ecs.describe_task_definition(taskDefinition="dagster:1") == dagster1
    assert ecs.describe_task_definition(taskDefinition="dagster:2") == dagster2

    # It also works with ARNs
    dagster1_arn = dagster1["taskDefinition"]["taskDefinitionArn"]
    dagster2_arn = dagster2["taskDefinition"]["taskDefinitionArn"]
    assert ecs.describe_task_definition(taskDefinition=dagster1_arn) == dagster1
    assert ecs.describe_task_definition(taskDefinition=dagster2_arn) == dagster2

    with pytest.raises(ClientError):
        # The revision doesn't exist
        ecs.describe_task_definition(taskDefinition="dagster:3")


def test_register_task_definition(ecs):
    response = ecs.register_task_definition(family="dagster", containerDefinitions=[])
    assert response["taskDefinition"]["family"] == "dagster"
    assert response["taskDefinition"]["revision"] == 1
    assert response["taskDefinition"]["taskDefinitionArn"].endswith("dagster:1")

    response = ecs.register_task_definition(family="other", containerDefinitions=[])
    assert response["taskDefinition"]["family"] == "other"
    assert response["taskDefinition"]["revision"] == 1
    assert response["taskDefinition"]["taskDefinitionArn"].endswith("other:1")

    response = ecs.register_task_definition(family="dagster", containerDefinitions=[])
    assert response["taskDefinition"]["family"] == "dagster"
    assert response["taskDefinition"]["revision"] == 2
    assert response["taskDefinition"]["taskDefinitionArn"].endswith("dagster:2")

    response = ecs.register_task_definition(
        family="dagster", containerDefinitions=[{"image": "hello_world:latest"}]
    )
    assert response["taskDefinition"]["containerDefinitions"][0]["image"] == "hello_world:latest"

    response = ecs.register_task_definition(
        family="dagster", containerDefinitions=[], networkMode="bridge"
    )
    assert response["taskDefinition"]["networkMode"] == "bridge"
