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
        memory="512",
        cpu="256",
    )
    dagster2 = ecs.register_task_definition(
        family="dagster",
        containerDefinitions=[{"image": "hello_world:latest"}],
        memory="512",
        cpu="256",
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

    ecs.register_task_definition(
        family="bridge", containerDefinitions=[], networkMode="bridge", memory="512", cpu="256"
    )

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


def test_list_account_settings(ecs):
    assert not ecs.list_account_settings()["settings"]
    assert not ecs.list_account_settings(effectiveSettings=False)["settings"]

    settings = ecs.list_account_settings(effectiveSettings=True)["settings"]
    assert settings

    task_arn_format_setting = [
        setting for setting in settings if setting["name"] == "taskLongArnFormat"
    ][0]
    assert task_arn_format_setting["value"] == "enabled"


def test_list_tags_for_resource(ecs):
    invalid_arn = ecs._task_arn("invalid")
    with pytest.raises(ClientError):
        # The task doesn't exist
        ecs.list_tags_for_resource(resourceArn=invalid_arn)

    tags = [{"key": "foo", "value": "bar"}, {"key": "fizz", "value": "buzz"}]
    ecs.register_task_definition(
        family="dagster", containerDefinitions=[], networkMode="bridge", memory="512", cpu="256"
    )
    arn = ecs.run_task(taskDefinition="dagster")["tasks"][0]["taskArn"]

    assert not ecs.list_tags_for_resource(resourceArn=arn)["tags"]

    ecs.tag_resource(resourceArn=arn, tags=tags)

    assert ecs.list_tags_for_resource(resourceArn=arn)["tags"] == tags

    # With the new ARN format disabled
    ecs.put_account_setting(name="taskLongArnFormat", value="disabled")

    with pytest.raises(ClientError):
        ecs.list_tags_for_resource(resourceArn=arn)


def test_list_task_definitions(ecs):
    assert not ecs.list_task_definitions()["taskDefinitionArns"]

    def arn(task_definition):
        return task_definition["taskDefinition"]["taskDefinitionArn"]

    dagster1 = arn(
        ecs.register_task_definition(
            family="dagster", containerDefinitions=[], memory="512", cpu="256"
        )
    )
    dagster2 = arn(
        ecs.register_task_definition(
            family="dagster", containerDefinitions=[], memory="512", cpu="256"
        )
    )
    other1 = arn(
        ecs.register_task_definition(
            family="other", containerDefinitions=[], memory="512", cpu="256"
        )
    )

    assert len(ecs.list_task_definitions()["taskDefinitionArns"]) == 3
    assert dagster1 in ecs.list_task_definitions()["taskDefinitionArns"]
    assert dagster2 in ecs.list_task_definitions()["taskDefinitionArns"]
    assert other1 in ecs.list_task_definitions()["taskDefinitionArns"]


def test_list_tasks(ecs):
    assert not ecs.list_tasks()["taskArns"]

    ecs.register_task_definition(
        family="dagster", containerDefinitions=[], networkMode="bridge", memory="512", cpu="256"
    )
    ecs.register_task_definition(
        family="other", containerDefinitions=[], networkMode="bridge", memory="512", cpu="256"
    )

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


def test_put_account_setting(ecs):
    setting = ecs.put_account_setting(name="taskLongArnFormat", value="disabled")["setting"]
    assert setting["name"] == "taskLongArnFormat"
    assert setting["value"] == "disabled"

    # It overrides the default settings
    settings = ecs.list_account_settings(effectiveSettings=True)["settings"]
    assert settings

    task_arn_format_setting = [
        setting for setting in settings if setting["name"] == "taskLongArnFormat"
    ][0]
    assert task_arn_format_setting["value"] == "disabled"


def test_register_task_definition(ecs):
    # Without memory
    with pytest.raises(ClientError):
        ecs.register_task_definition(family="dagster", containerDefinitions=[])

    # Without cpu
    with pytest.raises(ClientError):
        ecs.register_task_definition(family="dagster", containerDefinitions=[], memory="512")

    # With an invalid memory/cpu combination
    # https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html
    with pytest.raises(ClientError):
        ecs.register_task_definition(
            family="dagster", containerDefinitions=[], memory="512", cpu="1"
        )

    response = ecs.register_task_definition(
        family="dagster", containerDefinitions=[], memory="512", cpu="256"
    )
    assert response["taskDefinition"]["family"] == "dagster"
    assert response["taskDefinition"]["revision"] == 1
    assert response["taskDefinition"]["taskDefinitionArn"].endswith("dagster:1")

    response = ecs.register_task_definition(
        family="other", containerDefinitions=[], memory="512", cpu="256"
    )
    assert response["taskDefinition"]["family"] == "other"
    assert response["taskDefinition"]["revision"] == 1
    assert response["taskDefinition"]["taskDefinitionArn"].endswith("other:1")

    response = ecs.register_task_definition(
        family="dagster", containerDefinitions=[], memory="512", cpu="256"
    )
    assert response["taskDefinition"]["family"] == "dagster"
    assert response["taskDefinition"]["revision"] == 2
    assert response["taskDefinition"]["taskDefinitionArn"].endswith("dagster:2")

    response = ecs.register_task_definition(
        family="dagster",
        containerDefinitions=[{"image": "hello_world:latest"}],
        memory="512",
        cpu="256",
    )
    assert response["taskDefinition"]["containerDefinitions"][0]["image"] == "hello_world:latest"

    response = ecs.register_task_definition(
        family="dagster", containerDefinitions=[], networkMode="bridge", memory="512", cpu="256"
    )
    assert response["taskDefinition"]["networkMode"] == "bridge"


def test_run_task(ecs, ec2, subnet):
    with pytest.raises(ParamValidationError):
        # The task doesn't exist
        ecs.run_task()

    with pytest.raises(ClientError):
        # The task definition doesn't exist
        ecs.run_task(taskDefinition="dagster")

    ecs.register_task_definition(
        family="awsvpc", containerDefinitions=[], networkMode="awsvpc", memory="512", cpu="256"
    )
    ecs.register_task_definition(
        family="bridge", containerDefinitions=[], networkMode="bridge", memory="512", cpu="256"
    )

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

    # It includes memory and cpu
    assert response["tasks"][0]["cpu"] == "256"
    assert response["tasks"][0]["memory"] == "512"

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

    # With a real subnet
    response = ecs.run_task(
        taskDefinition="awsvpc",
        networkConfiguration={"awsvpcConfiguration": {"subnets": [subnet.id]}},
    )

    assert len(response["tasks"]) == 1
    assert "awsvpc" in response["tasks"][0]["taskDefinitionArn"]
    attachment = response["tasks"][0]["attachments"][0]
    assert attachment["type"] == "ElasticNetworkInterface"
    details = dict(detail.values() for detail in attachment["details"])
    assert details["subnetId"] == subnet.id
    eni = ec2.NetworkInterface(details["networkInterfaceId"])
    assert not eni.association_attribute

    # When assigning a public IP
    response = ecs.run_task(
        taskDefinition="awsvpc",
        networkConfiguration={
            "awsvpcConfiguration": {"subnets": [subnet.id], "assignPublicIp": "ENABLED"}
        },
    )
    details = dict(detail.values() for detail in response["tasks"][0]["attachments"][0]["details"])
    assert details["subnetId"] == subnet.id
    eni = ec2.NetworkInterface(details["networkInterfaceId"])
    assert eni.association_attribute.get("PublicIp")

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
        memory="512",
        cpu="256",
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

    # With invalid memory and cpu overrides
    with pytest.raises(ClientError):
        ecs.run_task(
            taskDefinition="container",
            overrides={"cpu": "7"},
        )

    # With valid memory and cpu overrides
    response = ecs.run_task(taskDefinition="container", overrides={"cpu": "512", "memory": "1024"})
    assert response["tasks"][0]["overrides"]["cpu"] == "512"
    assert response["tasks"][0]["overrides"]["memory"] == "1024"


def test_stop_task(ecs):
    with pytest.raises(ClientError):
        # The task doesn't exist
        ecs.stop_task(task=ecs._task_arn("invalid"))

    ecs.register_task_definition(
        family="bridge", containerDefinitions=[], networkMode="bridge", memory="512", cpu="256"
    )
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

    ecs.register_task_definition(
        family="dagster", containerDefinitions=[], networkMode="bridge", memory="512", cpu="256"
    )
    arn = ecs.run_task(taskDefinition="dagster")["tasks"][0]["taskArn"]

    ecs.tag_resource(resourceArn=arn, tags=tags)

    # With the new ARN format disabled
    ecs.put_account_setting(name="taskLongArnFormat", value="disabled")

    with pytest.raises(ClientError):
        ecs.tag_resource(resourceArn=arn, tags=tags)
