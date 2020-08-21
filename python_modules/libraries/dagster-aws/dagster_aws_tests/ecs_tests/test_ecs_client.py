import os

import boto3
import pytest
from dagster_aws.ecs import client
from moto import mock_ecs, mock_logs


@mock_ecs
@mock_logs
def test_set_cluster():
    log_client = boto3.client("logs", region_name="us-east-2")
    ecs_client = boto3.client("ecs", region_name="us-east-2")
    ecs_client.create_cluster(clusterName="test_clust")
    testclient = client.ECSClient(
        key_id="Testing",
        access_key="Testing",
        starter_client=ecs_client,
        starter_log_client=log_client,
    )
    assert "test_clust" in testclient.cluster


@mock_ecs
@mock_logs
def test_command():
    log_client = boto3.client("logs", region_name="us-east-2")
    ecs_client = boto3.client("ecs", region_name="us-east-2")
    ecs_client.create_cluster(clusterName="test_ecs_cluster")
    testclient = client.ECSClient(
        key_id="Testing",
        access_key="Testing",
        starter_client=ecs_client,
        starter_log_client=log_client,
    )
    testclient.set_and_register_task(
        ["echoes"], [""], family=" ",
    )
    taskdef = ecs_client.describe_task_definition(taskDefinition=testclient.task_definition_arn)[
        "taskDefinition"
    ]
    assert taskdef["containerDefinitions"][0]["command"][0] == "echoes"


@mock_ecs
@mock_logs
def test_entry():
    log_client = boto3.client("logs", region_name="us-east-2")
    ecs_client = boto3.client("ecs", region_name="us-east-2")
    ecs_client.create_cluster(clusterName="test_ecs_cluster")
    testclient = client.ECSClient(
        key_id="Testing",
        access_key="Testing",
        starter_client=ecs_client,
        starter_log_client=log_client,
    )
    testclient.set_and_register_task(
        [" "], ["entries"], family=" ",
    )
    taskdef = ecs_client.describe_task_definition(taskDefinition=testclient.task_definition_arn)[
        "taskDefinition"
    ]
    assert taskdef["containerDefinitions"][0]["entryPoint"][0] == "entries"


@mock_ecs
@mock_logs
def test_family():
    log_client = boto3.client("logs", region_name="us-east-2")
    ecs_client = boto3.client("ecs", region_name="us-east-2")
    ecs_client.create_cluster(clusterName="test_ecs_cluster")
    testclient = client.ECSClient(
        key_id="Testing",
        access_key="Testing",
        starter_client=ecs_client,
        starter_log_client=log_client,
    )
    testclient.set_and_register_task(
        ["echoes"], [""], family="basefam",
    )
    taskdef = ecs_client.describe_task_definition(taskDefinition=testclient.task_definition_arn)[
        "taskDefinition"
    ]
    assert taskdef["family"] == "basefam"
    logger = taskdef["containerDefinitions"][0]["logConfiguration"]["options"]
    assert "basefam" in logger["awslogs-group"]


@mock_ecs
@mock_logs
def test_region():
    log_client = boto3.client("logs", region_name="us-east-2")
    ecs_client = boto3.client("ecs", region_name="us-east-2")
    ecs_client.create_cluster(clusterName="test_ecs_cluster")
    testclient = client.ECSClient(
        key_id="Testing",
        access_key="Testing",
        starter_client=ecs_client,
        starter_log_client=log_client,
    )
    testclient.set_and_register_task(
        ["echoes"], [""], family="basefam",
    )
    taskdef = ecs_client.describe_task_definition(taskDefinition=testclient.task_definition_arn)[
        "taskDefinition"
    ]
    assert taskdef["family"] == "basefam"
    logger = taskdef["containerDefinitions"][0]["logConfiguration"]["options"]
    assert "us-east-2" in logger["awslogs-region"]


@pytest.mark.skipif(
    "AWS_ECS_TEST_DO_IT_LIVE" not in os.environ,
    reason="This test is slow and requires a live ECS cluster; run only upon explicit request",
)
def test_full_run():
    testclient = client.ECSClient()
    testclient.set_and_register_task(
        ["echo start"], ["/bin/bash", "-c"], family="multimessage",
    )
    networkConfiguration = {
        "awsvpcConfiguration": {
            "subnets": ["subnet-0f3b1467",],
            "securityGroups": ["sg-08627da7435350fa6",],
            "assignPublicIp": "ENABLED",
        }
    }
    testclient.run_task(networkConfiguration=networkConfiguration)

    testclient.set_and_register_task(
        ["echo middle"], ["/bin/bash", "-c"], family="multimessage",
    )
    testclient.run_task(networkConfiguration=networkConfiguration)
    testclient.set_and_register_task(
        ["echo $TEST"], ["/bin/bash", "-c"], family="multimessage",
    )
    testclient.run_task(networkConfiguration=networkConfiguration)
    testclient.spin_all()
    assert testclient.logs_messages == {2: ["end"], 1: ["middle"], 0: ["start"]}


@pytest.mark.skipif(
    "AWS_ECS_TEST_DO_IT_LIVE" not in os.environ,
    reason="This test is slow and requires a live ECS cluster; run only upon explicit request",
)
def test_one_run():
    testclient = client.ECSClient()
    testclient.set_and_register_task(
        ["echo start"], ["/bin/bash", "-c"], family="multimessage",
    )
    networkConfiguration = {
        "awsvpcConfiguration": {
            "subnets": ["subnet-0f3b1467",],
            "securityGroups": ["sg-08627da7435350fa6",],
            "assignPublicIp": "ENABLED",
        }
    }
    testclient.run_task(networkConfiguration=networkConfiguration)
    testclient.spin_all()
    assert testclient.logs_messages == {0: ["start"]}
