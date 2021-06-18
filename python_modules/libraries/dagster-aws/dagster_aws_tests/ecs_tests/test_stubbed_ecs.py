# pylint: disable=protected-access
import pytest
from botocore.exceptions import ClientError, ParamValidationError


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


def test_describe_tasks(ecs):
    assert not ecs.describe_tasks(tasks=["invalid"])["tasks"]
    assert not ecs.describe_tasks(cluster="dagster", tasks=["invalid"])["tasks"]

    ecs.register_task_definition(family="bridge", containerDefinitions=[], networkMode="bridge")

    default = ecs.run_task(taskDefinition="bridge")
    default_arn = default["tasks"][0]["taskArn"]
    default_id = default_arn.split("/")[-1]

    dagster = ecs.run_task(taskDefinition="bridge", cluster="dagster")
    dagster_arn = dagster["tasks"][0]["taskArn"]
    dagster_id = dagster_arn.split("/")[-1]

    # It uses the default cluster
    assert ecs.describe_tasks(tasks=[default_arn]) == default
    # It works with task ARNs
    assert not ecs.describe_tasks(tasks=[dagster_arn])["tasks"]
    assert ecs.describe_tasks(tasks=[dagster_arn], cluster="dagster") == dagster

    # And task IDs
    assert ecs.describe_tasks(tasks=[default_id]) == default
    assert not ecs.describe_tasks(tasks=[dagster_id])["tasks"]
    assert ecs.describe_tasks(tasks=[dagster_id], cluster="dagster") == dagster


def test_list_tags_for_resource(ecs):
    invalid_arn = ecs._task_arn("invalid")
    with pytest.raises(ClientError):
        # The task doesn't exist
        ecs.list_tags_for_resource(resourceArn=invalid_arn)

    tags = [{"key": "foo", "value": "bar"}, {"key": "fizz", "value": "buzz"}]
    ecs.register_task_definition(family="dagster", containerDefinitions=[], networkMode="bridge")
    arn = ecs.run_task(taskDefinition="dagster")["tasks"][0]["taskArn"]

    assert not ecs.list_tags_for_resource(resourceArn=arn)["tags"]

    ecs.tag_resource(resourceArn=arn, tags=tags)

    assert ecs.list_tags_for_resource(resourceArn=arn)["tags"] == tags


def test_list_task_definitions(ecs):
    assert not ecs.list_task_definitions()["taskDefinitionArns"]

    def arn(task_definition):
        return task_definition["taskDefinition"]["taskDefinitionArn"]

    dagster1 = arn(ecs.register_task_definition(family="dagster", containerDefinitions=[]))
    dagster2 = arn(ecs.register_task_definition(family="dagster", containerDefinitions=[]))
    other1 = arn(ecs.register_task_definition(family="other", containerDefinitions=[]))

    assert len(ecs.list_task_definitions()["taskDefinitionArns"]) == 3
    assert dagster1 in ecs.list_task_definitions()["taskDefinitionArns"]
    assert dagster2 in ecs.list_task_definitions()["taskDefinitionArns"]
    assert other1 in ecs.list_task_definitions()["taskDefinitionArns"]


def test_list_tasks(ecs):
    assert not ecs.list_tasks()["taskArns"]

    ecs.register_task_definition(family="dagster", containerDefinitions=[], networkMode="bridge")
    ecs.register_task_definition(family="other", containerDefinitions=[], networkMode="bridge")

    def arn(response):
        return response["tasks"][0]["taskArn"]

    default_cluster_dagster_family = arn(ecs.run_task(taskDefinition="dagster"))
    other_cluster_dagster_family = arn(ecs.run_task(taskDefinition="dagster", cluster="other"))
    default_cluster_other_family = arn(ecs.run_task(taskDefinition="other"))
    other_cluster_other_family = arn(ecs.run_task(taskDefinition="other", cluster="other"))

    # List using different combinations of cluster and family filters
    response = ecs.list_tasks()
    assert len(response["taskArns"]) == 2
    assert default_cluster_dagster_family in response["taskArns"]
    assert default_cluster_other_family in response["taskArns"]

    response = ecs.list_tasks(family="dagster")
    assert len(response["taskArns"]) == 1
    assert default_cluster_dagster_family in response["taskArns"]

    response = ecs.list_tasks(cluster="other")
    assert len(response["taskArns"]) == 2
    assert other_cluster_dagster_family in response["taskArns"]
    assert other_cluster_other_family in response["taskArns"]

    response = ecs.list_tasks(cluster="other", family="dagster")
    assert len(response["taskArns"]) == 1
    assert other_cluster_dagster_family in response["taskArns"]


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


def test_run_task(ecs, subnet):
    with pytest.raises(ParamValidationError):
        # The task doesn't exist
        ecs.run_task()

    with pytest.raises(ClientError):
        # The task definition doesn't exist
        ecs.run_task(taskDefinition="dagster")

    ecs.register_task_definition(family="awsvpc", containerDefinitions=[], networkMode="awsvpc")
    ecs.register_task_definition(family="bridge", containerDefinitions=[], networkMode="bridge")

    response = ecs.run_task(taskDefinition="bridge")
    assert len(response["tasks"]) == 1
    assert "bridge" in response["tasks"][0]["taskDefinitionArn"]
    assert response["tasks"][0]["lastStatus"] == "RUNNING"

    # It uses the default cluster
    assert response["tasks"][0]["clusterArn"] == ecs._cluster_arn("default")
    response = ecs.run_task(taskDefinition="bridge", cluster="dagster")
    assert response["tasks"][0]["clusterArn"] == ecs._cluster_arn("dagster")
    response = ecs.run_task(taskDefinition="bridge", cluster=ecs._cluster_arn("dagster"))
    assert response["tasks"][0]["clusterArn"] == ecs._cluster_arn("dagster")

    response = ecs.run_task(taskDefinition="bridge", count=2)
    assert len(response["tasks"]) == 2
    assert all(["bridge" in task["taskDefinitionArn"] for task in response["tasks"]])

    with pytest.raises(ClientError):
        # It must have a networkConfiguration if networkMode is "awsvpc"
        ecs.run_task(taskDefinition="awsvpc")

    # The subnet doesn't exist
    with pytest.raises(ClientError):
        ecs.run_task(
            taskDefinition="awsvpc",
            networkConfiguration={"awsvpcConfiguration": {"subnets": ["subnet-12345"]}},
        )

    #  The subnet exists but there's no network interface
    with pytest.raises(ClientError):
        ecs.run_task(
            taskDefinition="awsvpc",
            networkConfiguration={"awsvpcConfiguration": {"subnets": [subnet.id]}},
        )

    network_interface = subnet.create_network_interface()
    response = ecs.run_task(
        taskDefinition="awsvpc",
        networkConfiguration={"awsvpcConfiguration": {"subnets": [subnet.id]}},
    )

    assert len(response["tasks"]) == 1
    assert "awsvpc" in response["tasks"][0]["taskDefinitionArn"]
    attachment = response["tasks"][0]["attachments"][0]
    assert attachment["type"] == "ElasticNetworkInterface"
    assert {"name": "subnetId", "value": subnet.id} in attachment["details"]
    assert {"name": "networkInterfaceId", "value": network_interface.id} in attachment["details"]

    # containers and overrides are included
    ecs.register_task_definition(
        family="container",
        containerDefinitions=[
            {
                "name": "hello_world",
                "image": "hello_world:latest",
                "environment": [{"name": "FOO", "value": "bar"}],
            }
        ],
        networkMode="bridge",
    )
    response = ecs.run_task(taskDefinition="container")
    assert response["tasks"][0]["containers"]
    # ECS does not expose the task definition's environment when
    # describing tasks
    assert "FOO" not in response

    response = ecs.run_task(
        taskDefinition="container",
        overrides={"containerOverrides": [{"name": "hello_world", "command": ["ls"]}]},
    )
    assert response["tasks"][0]["overrides"]["containerOverrides"][0]["command"] == ["ls"]


def test_stop_task(ecs):
    with pytest.raises(ClientError):
        # The task doesn't exist
        ecs.stop_task(task=ecs._task_arn("invalid"))

    ecs.register_task_definition(family="bridge", containerDefinitions=[], networkMode="bridge")
    task_arn = ecs.run_task(taskDefinition="bridge")["tasks"][0]["taskArn"]

    assert ecs.describe_tasks(tasks=[task_arn])["tasks"][0]["lastStatus"] == "RUNNING"

    response = ecs.stop_task(task=task_arn)
    assert response["task"]["taskArn"] == task_arn
    assert response["task"]["lastStatus"] == "STOPPED"

    assert ecs.describe_tasks(tasks=[task_arn])["tasks"][0]["lastStatus"] == "STOPPED"


def test_tag_resource(ecs):
    tags = [{"key": "foo", "value": "bar"}]

    invalid_arn = ecs._task_arn("invalid")
    with pytest.raises(ClientError):
        # The task doesn't exist
        ecs.tag_resource(resourceArn=invalid_arn, tags=tags)

    ecs.register_task_definition(family="dagster", containerDefinitions=[], networkMode="bridge")
    arn = ecs.run_task(taskDefinition="dagster")["tasks"][0]["taskArn"]

    ecs.tag_resource(resourceArn=arn, tags=tags)
