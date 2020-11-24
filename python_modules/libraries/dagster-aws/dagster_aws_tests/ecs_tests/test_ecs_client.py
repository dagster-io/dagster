# pylint: disable=redefined-outer-name
import os

import boto3
import pytest
from dagster.core.test_utils import instance_for_test
from dagster_aws.ecs import client
from moto import mock_ecs, mock_sts


@pytest.fixture
def mock_ecs_client():
    with mock_ecs():
        yield boto3.client("ecs", region_name="us-east-2")


@pytest.fixture
def mock_ecs_cluster(mock_ecs_client):
    name = "test-cluster"
    mock_ecs_client.create_cluster(clusterName=name)
    return name


@pytest.fixture
def test_client(mock_ecs_client, mock_ecs_cluster):  # pylint: disable=unused-argument
    return client.ECSClient(
        key_id="Testing",
        access_key="Testing",
        starter_client=mock_ecs_client,
        starter_log_client=boto3.client("logs", region_name="us-east-2"),
    )


def test_set_cluster(test_client, mock_ecs_cluster):
    assert mock_ecs_cluster in test_client.cluster


def test_command(test_client, mock_ecs_client):
    test_client.set_and_register_task(
        ["echoes"], [""], family=" ",
    )
    taskdef = mock_ecs_client.describe_task_definition(
        taskDefinition=test_client.task_definition_arn
    )["taskDefinition"]
    assert taskdef["containerDefinitions"][0]["command"][0] == "echoes"


def test_entry(test_client, mock_ecs_client):
    test_client.set_and_register_task(
        [" "], ["entries"], family=" ",
    )
    taskdef = mock_ecs_client.describe_task_definition(
        taskDefinition=test_client.task_definition_arn
    )["taskDefinition"]
    assert taskdef["containerDefinitions"][0]["entryPoint"][0] == "entries"


def test_family(test_client, mock_ecs_client):
    test_client.set_and_register_task(
        ["echoes"], [""], family="basefam",
    )
    taskdef = mock_ecs_client.describe_task_definition(
        taskDefinition=test_client.task_definition_arn
    )["taskDefinition"]
    assert taskdef["family"] == "basefam"
    logger = taskdef["containerDefinitions"][0]["logConfiguration"]["options"]
    assert "basefam" in logger["awslogs-group"]


def test_region(test_client, mock_ecs_client):
    test_client.set_and_register_task(
        ["echoes"], [""], family="basefam",
    )
    taskdef = mock_ecs_client.describe_task_definition(
        taskDefinition=test_client.task_definition_arn
    )["taskDefinition"]
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


@mock_sts
def test_ecs_run_launcher_inits(mock_ecs_cluster):  # pylint: disable=unused-argument
    with instance_for_test(
        overrides={
            "run_launcher": {"module": "dagster_aws.ecs.launcher", "class": "ECSRunLauncher"}
        }
    ):
        pass
