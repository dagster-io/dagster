# ruff: noqa: SLF001
import asyncio
import json
import re
import time
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from itertools import chain, cycle
from unittest import mock

import boto3
import botocore.exceptions
import pytest
from botocore.stub import ANY, Stubber
from dagster_aws.utils import ensure_dagster_aws_tests_import
from dagster_cloud.workspace.ecs.client import Client, EcsServiceError, Service

ensure_dagster_aws_tests_import()
from dagster_aws_tests.ecs_tests.stubbed_ecs import StubbedEcs


@pytest.fixture
def client(cluster_name="test"):
    client = Client(
        cluster_name=cluster_name,
        service_discovery_namespace_id="fake-namespace",
        log_group="fake-log-group",
        grace_period=0,
    )

    def _mock_assign_public_ip(*args, **kwags):
        return "ENABLED"

    client._infer_assign_public_ip = _mock_assign_public_ip  # ty: ignore[invalid-assignment]

    yield client


@pytest.fixture
def stubbed_ecs():
    return StubbedEcs(boto3.client("ecs"))


@pytest.fixture
def stubbed_client(stubbed_ecs, cluster_name="test"):
    client = Client(
        cluster_name=cluster_name,
        service_discovery_namespace_id="fake-namespace",
        log_group="fake-log-group",
        ecs_client=stubbed_ecs,
    )

    def _mock_assign_public_ip(*args, **kwags):
        return "ENABLED"

    client._infer_assign_public_ip = _mock_assign_public_ip  # ty: ignore[invalid-assignment]

    yield client


@pytest.fixture
def stubber(client):
    with Stubber(client.ecs) as stubber:
        yield stubber


@pytest.mark.parametrize("cluster_name", ["test", "arn:aws:ecs:region:012345678910:cluster/test"])
def test_cluster_name(client, cluster_name):
    assert client.cluster_name == "test"


def test_taggable(client, stubber):
    stubber.add_response(
        method="list_account_settings",
        service_response={
            "settings": [
                {"name": "serviceLongArnFormat", "value": "enabled"},
            ]
        },
    )
    assert client.taggable

    stubber.add_response(
        method="list_account_settings",
        service_response={
            "settings": [
                {"name": "serviceLongArnFormat", "value": "disabled"},
            ]
        },
    )
    assert not client.taggable


def test_create_service_tags(client, stubber):
    arn = "arn:aws:ecs:us-east-1:1234567890:service/cluster-name/service-name"
    tags = {"foo": "bar"}

    params_without_tags = [
        "clientToken",
        "cluster",
        "desiredCount",
        "launchType",
        "networkConfiguration",
        "serviceName",
        "serviceRegistries",
        "taskDefinition",
        "enableExecuteCommand",
        "propagateTags",
    ]

    # When the new ARN format is disabled
    stubber.add_response(
        method="list_account_settings",
        service_response={
            "settings": [
                {"name": "serviceLongArnFormat", "value": "disabled"},
            ]
        },
    )
    # Expect that tags don't get added
    expected_params_without_tags = dict.fromkeys(params_without_tags, ANY)
    stubber.add_response(
        method="create_service",
        service_response={"service": {"serviceArn": arn}},
        expected_params=expected_params_without_tags,
    )

    client._create_service(
        service_name="fake",
        service_registry_arn="fake",
        task_definition_arn="fake",
        tags=tags,
    )

    # When the new ARN format is enabled
    stubber.add_response(
        method="list_account_settings",
        service_response={
            "settings": [
                {"name": "serviceLongArnFormat", "value": "enabled"},
            ]
        },
    )
    # Expect that tags get added
    expected_params_with_tags = dict(
        expected_params_without_tags, tags=[{"key": "foo", "value": "bar"}]
    )
    stubber.add_response(
        method="create_service",
        service_response={"service": {"serviceArn": arn}},
        expected_params=expected_params_with_tags,
    )

    client._create_service(
        service_name="fake",
        service_registry_arn="fake",
        task_definition_arn="fake",
        tags=tags,
    )


def test_ecs_service_error():
    with pytest.raises(EcsServiceError) as ex:
        raise EcsServiceError(
            cluster="My cluster",
            task_arn="foo",
            stopped_reason="bar",
            logs=["My", "bad"],
            show_debug_prompt=False,
        )

    ex.match("ECS service failed because task foo failed: bar\n\nTask logs:\nMy\nbad")

    with pytest.raises(EcsServiceError) as ex:
        raise EcsServiceError(
            cluster="My cluster",
            task_arn="foo",
            stopped_reason="bar",
            logs=["My", "bad"],
            show_debug_prompt=True,
        )

    ex.match(
        "ECS service failed because task foo failed: bar\n\nTask logs:\nMy\nbad\n\nFor more"
        " information about the failure, check the ECS console for logs for task foo in cluster My"
        " cluster."
    )


def test_secrets(stubbed_client, stubbed_ecs):
    assert len(stubbed_ecs.list_task_definitions()["taskDefinitionArns"]) == 0

    secret_dict = {
        "secret_name1": "arn:aws:secretsmanager:us-west-2:111122223333:secret:aes128-1a2b3c",
        "secret_name2": "arn:aws:secretsmanager:us-west-2:111122223333:secret:aes192-4D5e6F",
    }

    stubbed_client.create_service(
        name="fake_service",
        image="fake_image",
        command=["fake_command"],
        execution_role_arn="fake-role",
        register_service_discovery=False,
        secrets=secret_dict,
    )

    task_arns = stubbed_ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_arns) == 1
    task_def = stubbed_ecs.describe_task_definition(taskDefinition=task_arns[0])

    assert task_def["taskDefinition"]["containerDefinitions"][0]["secrets"] == [
        {"name": secret_name, "valueFrom": secret_arn}
        for secret_name, secret_arn in secret_dict.items()
    ]


def test_wait_for_new_service_failure(client, stubber):
    service = Service(arn="arn:aws:ecs:region:012345678910:cluster/boom", client=client)

    failures = [
        {
            "arn": service.arn,
            "detail": "detail",
            "reason": "reason",
        },
    ]
    stubber.add_response(
        method="describe_services",
        service_response={
            "services": [],
            "failures": failures,
        },
    )

    with pytest.raises(
        Exception,
        match=re.escape(f"ECS DescribeServices API returned failures: {json.dumps(failures)}"),
    ):
        asyncio.run(client.wait_for_new_service(service, container_name=service.name))

    failures = [
        {
            "arn": service.arn,
            "detail": "detail1",
            "reason": "reason1",
        },
        {
            "arn": service.arn,
            "detail": "detail2",
            "reason": "reason2",
        },
    ]

    stubber.add_response(
        method="describe_services",
        service_response={
            "services": [],
            "failures": failures,
        },
    )
    with pytest.raises(
        Exception,
        match=re.escape(f"ECS DescribeServices API returned failures: {json.dumps(failures)}"),
    ) as ex:
        asyncio.run(client.wait_for_new_service(service, container_name=service.name))
    assert ex.match("detail1")
    assert ex.match("detail2")

    stubber.add_response(
        method="describe_services",
        service_response={
            "services": [],
            "failures": [],
        },
    )

    with pytest.raises(
        Exception,
        match=re.escape(
            f"ECS DescribeServices API returned an empty response for service {service.arn}."
        ),
    ):
        asyncio.run(client.wait_for_new_service(service, container_name=service.name))

    # Success after failure works due to grace period

    client.grace_period = 15

    async def _check_service_has_running_tasks(
        service_name, container_name, logger=None
    ) -> list[str]:
        return ["my_task"]

    client.check_service_has_running_tasks = _check_service_has_running_tasks

    stubber.add_response(
        method="describe_services",
        service_response={
            "services": [],
            "failures": failures,
        },
    )

    stubber.add_response(
        method="describe_services",
        service_response={
            "services": [
                {
                    "clusterArn": "arn:aws:ecs:us-east-1:012345678910:cluster/default",
                    "createdAt": time.time(),
                    "deploymentConfiguration": {
                        "maximumPercent": 200,
                        "minimumHealthyPercent": 100,
                    },
                    "deployments": [
                        {
                            "createdAt": time.time(),
                            "desiredCount": 1,
                            "id": "ecs-svc/9223370564341623665",
                            "pendingCount": 0,
                            "runningCount": 0,
                            "status": "PRIMARY",
                            "taskDefinition": (
                                "arn:aws:ecs:us-east-1:012345678910:task-definition/hello_world:6"
                            ),
                            "updatedAt": time.time(),
                        },
                    ],
                    "desiredCount": 1,
                    "events": [
                        {
                            "createdAt": time.time(),
                            "id": "38c285e5-d335-4b68-8b15-e46dedc8e88d",
                            # In this example, there is a service event that shows unavailable cluster resources.
                            "message": (
                                "(service ecs-simple-service) was unable to place a task because no"
                                " container instance met all of its requirements. The closest"
                                " matching (container-instance"
                                " 3f4de1c5-ffdd-4954-af7e-75b4be0c8841) is already using a port"
                                " required by your task. For more information, see the"
                                " Troubleshooting section of the Amazon ECS Developer Guide."
                            ),
                        },
                    ],
                    "loadBalancers": [],
                    "pendingCount": 0,
                    "runningCount": 0,
                    "serviceArn": "arn:aws:ecs:us-east-1:012345678910:service/ecs-simple-service",
                    "serviceName": "ecs-simple-service",
                    "status": "ACTIVE",
                    "taskDefinition": (
                        "arn:aws:ecs:us-east-1:012345678910:task-definition/hello_world:6"
                    ),
                },
            ],
            "failures": [],
        },
    )

    assert (
        asyncio.run(client.wait_for_new_service(service, container_name=service.name)) == "my_task"
    )


def test_check_service_has_running_task__success():
    with mock.patch("dagster_cloud.workspace.ecs.client.time") as mock_time:
        with mock.patch("dagster_cloud.workspace.ecs.client.asyncio.sleep") as mock_asyncio_sleep:
            mock_time.time.side_effect = chain([1, 20], cycle([30]))

            async def no_sleep():
                await asyncio.sleep(0)

            mock_asyncio_sleep.side_effect = no_sleep

            client = Client(
                cluster_name="test",
                service_discovery_namespace_id="fake-namespace",
                log_group="fake-log-group",
                grace_period=0,
            )

            # timeouts used by the method
            client.timeout = 60

            with Stubber(client.ecs) as stubber:
                stubber.add_response(
                    method="describe_services",
                    service_response={"services": [{"desiredCount": 2, "runningCount": 2}]},
                )
                stubber.add_response(
                    method="list_tasks", service_response={"taskArns": ["my_task", "your_task"]}
                )
                stubber.add_response(
                    method="describe_tasks",
                    service_response={
                        "tasks": [
                            {
                                "taskDefinitionArn": "arn:aws:ecs:us-east-1:012345678910:task-definition/my_service:x.y.z"
                            }
                        ]
                    },
                )
                client._check_for_stopped_tasks = mock.MagicMock(return_value=[])  # ty: ignore[invalid-assignment]
                client._check_all_essential_containers_are_running = mock.MagicMock(  # ty: ignore[invalid-assignment]
                    return_value=True
                )
                response = asyncio.run(
                    client.check_service_has_running_tasks("my_service", "my_container")
                )
                assert response == ["my_task", "your_task"]


@mock.patch("dagster_cloud.workspace.ecs.client.time")
def test_check_service_has_running_task__missing_running_tasks_timeout(mock_time):
    mock_time.time.side_effect = chain([1, 20], cycle([100]))
    mock_time.sleep.side_effect = lambda _: None

    client = Client(
        cluster_name="test",
        service_discovery_namespace_id="fake-namespace",
        log_group="fake-log-group",
        grace_period=0,
    )

    # timeouts used by the method
    client.timeout = 60

    with Stubber(client.ecs) as stubber:
        stubber.add_response(
            method="describe_services",
            service_response={"services": [{"desiredCount": 2, "runningCount": 1}]},
        )
        # Getting events from the service
        stubber.add_response(
            method="describe_services",
            service_response={"services": [{"events": [{"message": "kaput"}]}]},
        )

        with mock.patch.object(client, "_check_for_stopped_tasks", return_value=[]):
            with mock.patch.object(
                client, "_check_all_essential_containers_are_running", return_value=True
            ):
                with pytest.raises(
                    Exception,
                    match=r"Timed out waiting for a running task for service: my_service. Service events:\nkaput",
                ):
                    asyncio.run(
                        client.check_service_has_running_tasks("my_service", "my_container")
                    )


@mock.patch("dagster_cloud.workspace.ecs.client.time")
def test_check_service_has_running_task__stopped_tasks_after_grace_period(mock_time):
    mock_time.time.side_effect = chain([1, 32], cycle([1000]))
    mock_time.sleep.side_effect = lambda _: None

    client = Client(
        cluster_name="test",
        service_discovery_namespace_id="fake-namespace",
        log_group="fake-log-group",
        grace_period=0,
    )

    # timeouts used by the method
    client.timeout = 60

    with Stubber(client.ecs) as stubber:
        stubber.add_response(
            method="describe_services",
            service_response={"services": [{"desiredCount": 1, "runningCount": 0}]},
        )

        # todo: add a test for get_task_logs and mock it for this test
        stubber.add_response(
            method="describe_tasks",
            service_response={
                "tasks": [
                    {
                        "taskDefinitionArn": "arn:aws:ecs:us-east-1:012345678910:task-definition/my_service:x.y.z"
                    }
                ]
            },
        )
        stubber.add_response(
            method="describe_task_definition",
            service_response={
                "taskDefinition": {
                    "containerDefinitions": [
                        {
                            "name": "my_container",
                            "logConfiguration": {
                                "logDriver": "awslogs",
                                "options": {"awslogs-stream-prefix": "my_log_prefix"},
                            },
                        },
                    ]
                }
            },
        )
        with Stubber(client.logs) as logs_stubber:
            logs_stubber.add_response(
                method="get_log_events",
                service_response={"events": [{"message": "couch"}, {"message": "potato"}]},
            )

            with mock.patch.object(
                client,
                "_check_for_stopped_tasks",
                return_value=[
                    {
                        "name": "failed_task",
                        "createdAt": datetime.fromtimestamp(6),
                        "taskArn": "some_arn",
                        "stoppedReason": "kaput",
                    }
                ],
            ):
                with pytest.raises(
                    Exception,
                    match=r"ECS service failed because task some_arn failed: kaput\n\nTask logs:\ncouch\npotato",
                ):
                    asyncio.run(
                        client.check_service_has_running_tasks("my_service", "my_container")
                    )


@mock.patch("dagster_cloud.workspace.ecs.client.time")
def test_check_service_has_running_task__no_running_task_after_timeout(mock_time):
    mock_time.time.side_effect = chain([1, 30, 111], cycle([1000]))
    mock_time.sleep.side_effect = lambda _: None

    client = Client(
        cluster_name="test",
        service_discovery_namespace_id="fake-namespace",
        log_group="fake-log-group",
        grace_period=0,
    )

    # timeouts used by the method
    client.timeout = 60

    with Stubber(client.ecs) as stubber:
        # Waiting for tasks to be running
        stubber.add_response(
            method="describe_services",
            service_response={"services": [{"desiredCount": 1, "runningCount": 0}]},
        )
        # Getting events from the service
        stubber.add_response(
            method="describe_services",
            service_response={"services": [{"events": [{"message": "kaput"}]}]},
        )

        with mock.patch.object(client, "_check_for_stopped_tasks", return_value=[]):
            with pytest.raises(
                Exception,
                match=r"Timed out waiting for a running task for service: my_service. Service events:\nkaput",
            ):
                asyncio.run(client.check_service_has_running_tasks("my_service", "my_container"))


@mock.patch("dagster_cloud.workspace.ecs.client.time")
def test_check_service_has_running_task__task_stopped_with_transient_failure_immediately(mock_time):
    with mock.patch("dagster_cloud.workspace.ecs.client.time") as mock_time:
        with mock.patch("dagster_cloud.workspace.ecs.client.asyncio.sleep") as mock_asyncio_sleep:
            mock_time.time.side_effect = chain([1, 20], cycle([50]))

            async def no_sleep(_):
                return

            mock_asyncio_sleep.side_effect = no_sleep

            client = Client(
                cluster_name="test",
                service_discovery_namespace_id="fake-namespace",
                log_group="fake-log-group",
                grace_period=0,
            )

            # timeouts used by the method
            client.timeout = 60

            # simulate grace period for stopped tasks passing
            client.grace_period = 15

            with Stubber(client.ecs) as stubber:
                stubber.add_response(
                    method="describe_services",
                    service_response={"services": [{"desiredCount": 1, "runningCount": 0}]},
                )
                stubber.add_response(
                    method="list_tasks", service_response={"taskArns": ["my_task"]}
                )
                stubber.add_response(
                    method="describe_tasks",
                    service_response={
                        "tasks": [
                            {
                                "createdAt": datetime.fromtimestamp(6),
                                "taskArn": "some_arn",
                                "stoppedReason": "Timeout waiting for network interface provisioning to complete",
                                "lastStatus": "STOPPED",
                            }
                        ]
                    },
                )
                stubber.add_response(
                    method="describe_services",
                    service_response={"services": [{"desiredCount": 1, "runningCount": 1}]},
                )
                stubber.add_response(
                    method="list_tasks", service_response={"taskArns": ["your_task"]}
                )
                stubber.add_response(
                    method="describe_tasks",
                    service_response={
                        "tasks": [
                            {
                                "createdAt": datetime.fromtimestamp(6),
                                "taskArn": "new_arn",
                                "lastStatus": "RUNNING",
                            }
                        ]
                    },
                )
                client._check_all_essential_containers_are_running = mock.MagicMock(  # ty: ignore[invalid-assignment]
                    return_value=True
                )

                response = asyncio.run(
                    client.check_service_has_running_tasks("my_service", "my_container")
                )
                assert response == ["your_task"]


@mock.patch("dagster_cloud.workspace.ecs.client.time")
def test_check_service_has_running_task__running_task_moves_to_transient_startup_failure(mock_time):
    with mock.patch("dagster_cloud.workspace.ecs.client.time") as mock_time:
        with mock.patch("dagster_cloud.workspace.ecs.client.asyncio.sleep") as mock_asyncio_sleep:
            mock_time.time.side_effect = chain([1, 20], cycle([30]))

            async def no_sleep(_):
                return

            mock_asyncio_sleep.side_effect = no_sleep

            client = Client(
                cluster_name="test",
                service_discovery_namespace_id="fake-namespace",
                log_group="fake-log-group",
                grace_period=0,
            )

            # timeouts used by the method
            client.timeout = 60

            with Stubber(client.ecs) as stubber:
                stubber.add_response(
                    method="describe_services",
                    service_response={"services": [{"desiredCount": 1, "runningCount": 1}]},
                )
                stubber.add_response(
                    method="list_tasks", service_response={"taskArns": ["my_task"]}
                )
                stubber.add_response(
                    method="describe_tasks",
                    service_response={
                        "tasks": [
                            {
                                "createdAt": datetime.fromtimestamp(6),
                                "taskArn": "some_arn",
                                "stoppedReason": "Timeout waiting for network interface provisioning to complete",
                                "lastStatus": "STOPPED",
                            }
                        ]
                    },
                )
                stubber.add_response(
                    method="describe_services",
                    service_response={"services": [{"desiredCount": 1, "runningCount": 1}]},
                )
                stubber.add_response(
                    method="list_tasks", service_response={"taskArns": ["your_task"]}
                )
                stubber.add_response(
                    method="describe_tasks",
                    service_response={
                        "tasks": [
                            {
                                "createdAt": datetime.fromtimestamp(6),
                                "taskArn": "new_arn",
                                "lastStatus": "RUNNING",
                            }
                        ]
                    },
                )
                client._check_for_stopped_tasks = mock.MagicMock(return_value=[])  # ty: ignore[invalid-assignment]
                client._check_all_essential_containers_are_running = mock.MagicMock(  # ty: ignore[invalid-assignment]
                    return_value=True
                )

                response = asyncio.run(
                    client.check_service_has_running_tasks("my_service", "my_container")
                )
                assert response == ["your_task"]


@pytest.mark.parametrize(
    "sub_test_name, containers, expected",
    [
        (
            "single_essential_container_running",
            [
                {
                    "name": "my_container",
                    "essential": True,
                    "lastStatus": "RUNNING",
                },
            ],
            True,
        ),
        (
            "single_essential_container_running_with_stopped_sidecar",
            [
                {
                    "name": "my_container",
                    "essential": True,
                    "lastStatus": "RUNNING",
                },
                {
                    "name": "my_sidecar",
                    "essential": False,
                    "lastStatus": "STOPPED",
                },
            ],
            True,
        ),
        (
            "single_essential_container_stopped",
            [
                {
                    "name": "my_container",
                    "essential": True,
                    "lastStatus": "STOPPED",
                },
            ],
            False,
        ),
        (
            "multiple_essential_containers_running",
            [
                {
                    "name": "my_container",
                    "essential": True,
                    "lastStatus": "RUNNING",
                },
                {
                    "name": "my_other_container",
                    "essential": True,
                    "lastStatus": "RUNNING",
                },
            ],
            True,
        ),
        (
            "multiple_essential_containers_with_one_stopped",
            [
                {
                    "name": "my_container",
                    "essential": True,
                    "lastStatus": "RUNNING",
                },
                {
                    "name": "my_other_container",
                    "essential": True,
                    "lastStatus": "STOPPED",
                },
            ],
            False,
        ),
    ],
)
def test_check_all_essential_containers_are_running(sub_test_name, containers, expected):
    # arrange
    mockTaskArn = "arn:aws:ecs:us-east-1:012345678910:task-definition/hello_world:x.y.z"
    task_definition = {
        "containerDefinitions": [
            {"name": c["name"], "essential": c["essential"]} for c in containers
        ]
    }

    task = {
        "taskDefinitionArn": mockTaskArn,
        "containers": [{"name": c["name"], "lastStatus": c["lastStatus"]} for c in containers],
    }

    client = Client(
        cluster_name="test",
        service_discovery_namespace_id="fake-namespace",
        log_group="fake-log-group",
        grace_period=0,
    )
    with mock.patch.object(
        client.ecs,
        "describe_task_definition",
        return_value={
            "taskDefinition": task_definition,
        },
    ) as mock_describe_task_definition:
        # act
        ret_val = client._check_all_essential_containers_are_running(task)

        # assert
        assert mock_describe_task_definition.call_count == 1
        mock_describe_task_definition.assert_called_with(taskDefinition=mockTaskArn)

        assert ret_val == expected


@pytest.mark.parametrize(
    "sub_test_name, stopped_tasks_arn, stopped_tasks, expected",
    [
        ("no_stopped_tasks", {"taskArns": []}, {"tasks": []}, []),
        (
            "three_stopped_task_sorted",
            {"taskArns": ["first", "third", "second"]},
            {
                "tasks": [
                    {
                        "name": "first",
                        "createdAt": datetime.fromtimestamp(1_000_000),
                    },
                    {
                        "name": "third",
                        "createdAt": datetime.fromtimestamp(3_000_000),
                    },
                    {
                        "name": "second",
                        "createdAt": datetime.fromtimestamp(2_000_000),
                    },
                ]
            },
            ["third", "second", "first"],  # sorted by createdAt in reverse order
        ),
    ],
)
def test_check_for_stopped_tasks(sub_test_name, stopped_tasks_arn, stopped_tasks, expected, caplog):
    client = Client(
        cluster_name="test",
        service_discovery_namespace_id="fake-namespace",
        log_group="fake-log-group",
        grace_period=0,
    )
    with mock.patch.object(
        client.ecs, "list_tasks", return_value=stopped_tasks_arn
    ) as mock_list_tasks:
        ret_val = None
        if len(expected) > 1:
            with mock.patch.object(
                client.ecs, "describe_tasks", return_value=stopped_tasks
            ) as mock_describe_tasks:
                ret_val = client._check_for_stopped_tasks("my_service")
                assert mock_describe_tasks.call_count == 1
        else:
            ret_val = client._check_for_stopped_tasks("my_service")

        assert mock_list_tasks.call_count == 1
        assert [v["name"] for v in ret_val] == expected


def test_list_services(aws_mock, monkeypatch, caplog):
    monkeypatch.setattr(
        "dagster_cloud.workspace.ecs.client.Client.taggable",
        True,
    )
    monkeypatch.setattr(
        "dagster_cloud.workspace.ecs.client.Client._infer_assign_public_ip",
        lambda *args, **kwargs: "ENABLED",
    )
    caplog.set_level("WARNING")

    # Create VPC, subnet, and security group for moto 5 compatibility
    ec2 = boto3.client("ec2")
    vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
    vpc_id = vpc["Vpc"]["VpcId"]
    subnet = ec2.create_subnet(VpcId=vpc_id, CidrBlock="10.0.1.0/24")
    subnet_id = subnet["Subnet"]["SubnetId"]
    security_group = ec2.create_security_group(
        GroupName="test-sg", Description="Test security group", VpcId=vpc_id
    )
    security_group_id = security_group["GroupId"]

    ecs = boto3.client("ecs")

    ecs.create_cluster(clusterName="test")

    client = Client(
        cluster_name="test",
        service_discovery_namespace_id="fake-namespace",
        log_group="fake-log-group",
        grace_period=0,
        subnet_ids=[subnet_id],
        security_group_ids=[security_group_id],
    )

    client.create_service(
        name="tagged",
        image="test",
        command=["test"],
        execution_role_arn="test",
        tags={"foo": "bar"},
    )

    client.create_service(
        name="untagged",
        image="test",
        command=["test"],
        execution_role_arn="test",
    )

    assert len(client.list_services()) == 2

    # Backcompat: If we can't use the Resource Groups Tagging API
    # warn once and flip to legacy mode
    with mock.patch.object(
        client.tags_client,
        "get_paginator",
        side_effect=botocore.exceptions.ClientError(
            operation_name="GetResources",
            error_response={"Error": {"Code": "AccessDeniedException"}},
        ),
    ):
        assert len(client.list_services(tags={"foo": "bar"})) == 1
        assert client.list_services(tags={"foo": "bar"})[0].name == "tagged"
        assert len(caplog.records) == 1

    # Re-initialize the client and enable the Resource Groups Tagging API
    # There are no warnings
    caplog.clear()
    client = Client(
        cluster_name="test",
        service_discovery_namespace_id="fake-namespace",
        log_group="fake-log-group",
        grace_period=0,
        subnet_ids=[subnet_id],
        security_group_ids=[security_group_id],
    )
    assert len(client.list_services()) == 2

    assert len(client.list_services(tags={"foo": "bar"})) == 1
    assert client.list_services(tags={"foo": "bar"})[0].name == "tagged"
    assert len(caplog.records) == 0

    # Given that the Resource Group API returns resources that are not corresponding to services that
    # are present in the cluster, list_services should filter these out from its return value
    with mock.patch.object(client.tags_client, "get_paginator") as mock_get_paginator:
        mock_get_paginator.return_value.paginate.return_value = [
            {
                "ResourceTagMappingList": [
                    {
                        "ResourceARN": "arn:aws:ecs:us-east-1:123456789012:service/test/tagged",
                        "Tags": [{"Key": "foo", "Value": "bar"}],
                    },
                    {
                        "ResourceARN": "arn:aws:ecs:us-east-1:123456789012:service/test/missing",
                        "Tags": [{"Key": "foo", "Value": "bar"}],
                    },
                ]
            }
        ]
        result = client.list_services(tags={"foo": "bar"})
        assert len(result) == 1
        assert result[0].name == "tagged"


def test_delete_service_golden_path(aws_mock):
    """Test complete usual case where a service exist and is active, with a service discovery registration."""
    # Create VPC for service discovery namespace (moto 5 requires a real VPC)
    ec2 = boto3.client("ec2")
    vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
    vpc_id = vpc["Vpc"]["VpcId"]

    ecs = boto3.client("ecs")
    service_discovery = boto3.client("servicediscovery")
    service_discovery.create_private_dns_namespace(Name="fake-namespace", Vpc=vpc_id)
    namespace = "fake-namespace"
    namespaces = service_discovery.list_namespaces(
        Filters=[{"Name": "NAME", "Values": [namespace]}]
    )
    namespace_id = namespaces["Namespaces"][0]["Id"]
    service_discovery.get_namespace(Id=namespace_id)
    ecs.create_cluster(clusterName="test", serviceConnectDefaults={"namespace": namespace_id})

    client = Client(
        cluster_name="test",
        service_discovery_namespace_id=namespace_id,
        log_group="fake-log-group",
    )

    ecs.register_task_definition(
        family="test",
        executionRoleArn="test",
        taskRoleArn="test",
        containerDefinitions=[
            {
                "name": "test",
                "image": "test",
                "command": ["test"],
                "memory": 512,
            }
        ],
    )

    ecs.create_service(
        cluster="test",
        serviceName="my_service",
        taskDefinition="test",
    )

    service_discovery.create_service(Name="my_service", NamespaceId=namespace_id, Type="HTTP")

    # Moto does not implement or does not implement correctly these methods:
    # - service_discovery.list_instances
    # - service_discovery.deregister_instance
    # - service_discovery.get_operation
    # So we have to mock them manually, also we have to mock delete_service because it does not seem
    # to correctly change the list of services in the cluster.
    with mock.patch.object(
        client.service_discovery,
        "list_instances",
        return_value={"Instances": [{"Id": "fake_instance"}]},
    ):
        with mock.patch.object(
            client.service_discovery, "deregister_instance", return_value={"OperationId": "foobar"}
        ) as mock_deregister_instance:
            with mock.patch.object(
                client.service_discovery,
                "get_operation",
                return_value={"Operation": {"Status": "SUCCESS"}},
            ) as mock_get_operation:
                with mock.patch.object(client.ecs, "delete_service") as mock_delete_service:
                    StubService = namedtuple("StubService", "name hostname")
                    client.delete_service(
                        StubService(name="my_service", hostname=f"my_service.{namespace}"),
                    )
                    assert mock_delete_service.call_args.kwargs == {
                        "cluster": "test",
                        "service": "my_service",
                        "force": True,
                    }
                assert mock_get_operation.call_args.kwargs == {"OperationId": "foobar"}
            assert mock_deregister_instance.call_args.kwargs["InstanceId"] == "fake_instance"


def test_delete_service_service_missing(aws_mock, caplog):
    """Test that the delete_service method does not raise an exception if the service is not found."""
    caplog.set_level("WARNING")
    ecs = boto3.client("ecs")
    ecs.create_cluster(clusterName="test")
    client = Client(
        cluster_name="test",
        service_discovery_namespace_id="some-namespace-id",
        log_group="fake-log-group",
    )

    # moto's ServiceNotFoundException is not a subclass of botocore.exceptions.ClientError
    exception = botocore.exceptions.ClientError(
        {"Error": {"Code": "ServiceNotFoundException", "Message": "Service was not found"}},
        "update_service",
    )

    StubService = namedtuple("StubService", "name hostname")
    with mock.patch.object(client.ecs, "update_service", side_effect=exception):
        with mock.patch.object(client.ecs, "delete_service") as mock_delete_service:
            client.delete_service(
                StubService(name="my_service", hostname="my_service.some-namespace")
            )
            # delete will not have been called if the service is not found on the previous update command
            assert mock_delete_service.call_count == 0

    # command should not fail but should log a warning
    assert "my_service is not found or inactive" in caplog.text


def test_assign_public_ip_override():
    client = Client(
        cluster_name="test",
        service_discovery_namespace_id="fake-namespace",
        log_group="fake-log-group",
        grace_period=0,
        assign_public_ip=True,
    )
    assert client.network_configuration["awsvpcConfiguration"]["assignPublicIp"] == "ENABLED"

    client = Client(
        cluster_name="test",
        service_discovery_namespace_id="fake-namespace",
        log_group="fake-log-group",
        grace_period=0,
        assign_public_ip=False,
    )
    assert client.network_configuration["awsvpcConfiguration"]["assignPublicIp"] == "DISABLED"


def _make_sts_credentials(expires_in_minutes=60):
    """Create fake STS assume_role response credentials."""
    expiration = datetime.now(tz=timezone.utc) + timedelta(minutes=expires_in_minutes)
    return {
        "Credentials": {
            "AccessKeyId": "fake-access-key",
            "SecretAccessKey": "fake-secret-key",
            "SessionToken": "fake-session-token",
            "Expiration": expiration,
        },
        "AssumedRoleUser": {
            "AssumedRoleId": "fake-role-id",
            "Arn": "arn:aws:sts::123456789012:assumed-role/test-role/session",
        },
    }


def test_client_without_service_discovery_role_arn():
    """Client without service_discovery_role_arn uses default boto3 client."""
    client = Client(
        cluster_name="test",
        service_discovery_namespace_id="fake-namespace",
        log_group="fake-log-group",
        grace_period=0,
    )
    assert client._service_discovery_role_arn is None
    assert client._service_discovery is not None


def test_client_with_service_discovery_role_arn():
    """Client with service_discovery_role_arn assumes role via STS."""
    role_arn = "arn:aws:iam::123456789012:role/cross-account-sd"
    fake_creds = _make_sts_credentials()

    with (
        mock.patch("boto3.client") as mock_boto_client,
        mock.patch("boto3.Session") as mock_session_cls,
    ):
        mock_sts = mock.MagicMock()
        mock_sts.assume_role.return_value = fake_creds

        def _client_factory(service, **kwargs):
            if service == "sts":
                return mock_sts
            return mock.MagicMock()

        mock_boto_client.side_effect = _client_factory
        mock_session = mock.MagicMock()
        mock_session_cls.return_value = mock_session

        client = Client(
            cluster_name="test",
            service_discovery_namespace_id="fake-namespace",
            log_group="fake-log-group",
            grace_period=0,
            service_discovery_role_arn=role_arn,
        )

        mock_sts.assume_role.assert_called_once()
        call_kwargs = mock_sts.assume_role.call_args.kwargs
        assert call_kwargs["RoleArn"] == role_arn
        assert call_kwargs["DurationSeconds"] == 3600
        assert "dagster-ecs-sd-" in call_kwargs["RoleSessionName"]

        mock_session_cls.assert_called_once_with(
            aws_access_key_id="fake-access-key",
            aws_secret_access_key="fake-secret-key",
            aws_session_token="fake-session-token",
        )

        mock_session.client.assert_called_once()
        assert client._service_discovery_role_arn == role_arn


def test_service_discovery_session_refresh():
    """Service discovery session is refreshed when near expiration."""
    role_arn = "arn:aws:iam::123456789012:role/cross-account-sd"

    with mock.patch("boto3.client") as mock_boto_client, mock.patch("boto3.Session"):
        mock_sts = mock.MagicMock()
        mock_sts.assume_role.return_value = _make_sts_credentials()

        def _client_factory(service, **kwargs):
            if service == "sts":
                return mock_sts
            return mock.MagicMock()

        mock_boto_client.side_effect = _client_factory

        client = Client(
            cluster_name="test",
            service_discovery_namespace_id="fake-namespace",
            log_group="fake-log-group",
            grace_period=0,
            service_discovery_role_arn=role_arn,
        )

        assert mock_sts.assume_role.call_count == 1

        # Access the property — session is still valid, no refresh
        _ = client.service_discovery
        assert mock_sts.assume_role.call_count == 1

        # Simulate session about to expire (within 5-minute buffer)
        client._sd_session_expires = datetime.now(tz=timezone.utc) + timedelta(minutes=2)
        mock_sts.assume_role.return_value = _make_sts_credentials()

        # Access triggers refresh
        _ = client.service_discovery
        assert mock_sts.assume_role.call_count == 2


def test_service_discovery_no_refresh_without_role_arn():
    """Without role ARN, service_discovery property returns client directly without refresh."""
    client = Client(
        cluster_name="test",
        service_discovery_namespace_id="fake-namespace",
        log_group="fake-log-group",
        grace_period=0,
    )

    sd_client = client.service_discovery
    # Accessing multiple times returns the same client, no refresh logic involved
    assert client.service_discovery is sd_client
