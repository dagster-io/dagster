import multiprocessing
import os
import re
import sys
import time
from typing import TYPE_CHECKING

import boto3
import botocore
import pytest
from dagster import asset, materialize
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSpec
from dagster._core.definitions.data_version import (
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MarkdownMetadataValue
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus

from dagster_aws.pipes import PipesCloudWatchMessageReader, PipesECSClient
from dagster_aws.pipes.clients.ecs import WaiterConfig
from dagster_aws_tests.pipes_tests.fake_ecs import LocalECSMockClient
from dagster_aws_tests.pipes_tests.utils import _MOTO_SERVER_URL

if TYPE_CHECKING:
    from mypy_boto3_ecs import ECSClient


@pytest.fixture
def ecs_client(moto_server, s3_client) -> "ECSClient":
    return boto3.client("ecs", region_name="us-east-1", endpoint_url=_MOTO_SERVER_URL)


@pytest.fixture
def ecs_cluster(ecs_client) -> str:
    cluster_name = "test-cluster"
    ecs_client.create_cluster(clusterName=cluster_name)
    return cluster_name


@pytest.fixture
def ecs_task_definition(ecs_client, external_script_default_components) -> str:
    task_definition = "test-task"
    ecs_client.register_task_definition(
        family=task_definition,
        containerDefinitions=[
            {
                "name": LocalECSMockClient.CONTAINER_NAME,
                "image": "test-image",
                "command": [sys.executable, external_script_default_components],
                "memory": 512,
            }
        ],
    )
    return task_definition


@pytest.fixture
def local_ecs_mock_client(
    ecs_client, cloudwatch_client, ecs_cluster, ecs_task_definition
) -> LocalECSMockClient:
    return LocalECSMockClient(ecs_client=ecs_client, cloudwatch_client=cloudwatch_client)


@pytest.fixture
def pipes_ecs_client(local_ecs_mock_client, s3_client, cloudwatch_client) -> PipesECSClient:
    return PipesECSClient(
        client=local_ecs_mock_client,
        message_reader=PipesCloudWatchMessageReader(
            client=cloudwatch_client,
        ),
    )


@asset(check_specs=[AssetCheckSpec(name="foo_check", asset=AssetKey(["ecs_asset"]))])
def ecs_asset(context: AssetExecutionContext, pipes_ecs_client: PipesECSClient):
    return pipes_ecs_client.run(
        context=context,
        extras={"bar": "baz"},
        run_task_params={
            "cluster": "test-cluster",
            "count": 1,
            "taskDefinition": "test-task",
            "launchType": "FARGATE",
            "networkConfiguration": {"awsvpcConfiguration": {"subnets": ["subnet-12345678"]}},
            "overrides": {
                "containerOverrides": [
                    {
                        "name": LocalECSMockClient.CONTAINER_NAME,
                        "environment": [
                            {
                                "name": "SLEEP_SECONDS",
                                "value": os.getenv(
                                    "SLEEP_SECONDS", "0.1"
                                ),  # this can be increased to test interruption
                            }
                        ],
                    }
                ]
            },
        },
        waiter_config=WaiterConfig(
            Delay=int(os.getenv("WAIT_DELAY", "6")),
            MaxAttempts=int(os.getenv("WAIT_MAX_ATTEMPTS", "1000000")),
        ),
    ).get_results()


def test_ecs_pipes(
    capsys,
    pipes_ecs_client: PipesECSClient,
):
    with instance_for_test() as instance:
        materialize(
            [ecs_asset], instance=instance, resources={"pipes_ecs_client": pipes_ecs_client}
        )
        mat = instance.get_latest_materialization_event(ecs_asset.key)
        assert mat and mat.asset_materialization
        assert isinstance(mat.asset_materialization.metadata["bar"], MarkdownMetadataValue)
        assert mat.asset_materialization.metadata["bar"].value == "baz"
        assert "AWS ECS Task URL" in mat.asset_materialization.metadata
        assert mat.asset_materialization.tags
        assert mat.asset_materialization.tags[DATA_VERSION_TAG] == "alpha"
        assert mat.asset_materialization.tags[DATA_VERSION_IS_USER_PROVIDED_TAG]

        captured = capsys.readouterr()
        assert re.search(r"dagster - INFO - [^\n]+ - hello world\n", captured.err, re.MULTILINE)

        asset_check_executions = instance.event_log_storage.get_asset_check_execution_history(
            check_key=AssetCheckKey(ecs_asset.key, name="foo_check"),
            limit=1,
        )
        assert len(asset_check_executions) == 1
        assert asset_check_executions[0].status == AssetCheckExecutionRecordStatus.SUCCEEDED


def test_ecs_pipes_interruption_forwarding(pipes_ecs_client: PipesECSClient):
    def materialize_asset(env, return_dict):
        os.environ.update(env)
        try:
            with instance_for_test() as instance:
                materialize(  # this will be interrupted and raise an exception
                    [ecs_asset],
                    instance=instance,
                    resources={"pipes_ecs_client": pipes_ecs_client},
                )
        finally:
            assert len(pipes_ecs_client._client._task_runs) > 0  # noqa  # pyright: ignore[reportAttributeAccessIssue]
            task_arn = next(iter(pipes_ecs_client._client._task_runs.keys()))  # noqa  # pyright: ignore[reportAttributeAccessIssue]
            return_dict[0] = pipes_ecs_client._client.describe_tasks(  # noqa
                cluster="test-cluster", tasks=[task_arn]
            )

    with multiprocessing.Manager() as manager:
        return_dict = manager.dict()

        p = multiprocessing.Process(
            target=materialize_asset,
            args=(
                {"SLEEP_SECONDS": "10"},
                return_dict,
            ),
        )
        p.start()

        while p.is_alive():
            # we started executing the run
            # time to interrupt it!
            time.sleep(4)
            p.terminate()

        p.join()
        assert not p.is_alive()
        # breakpoint()
        assert return_dict[0]["tasks"][0]["containers"][0]["exitCode"] == 1
        assert return_dict[0]["tasks"][0]["stoppedReason"] == "Dagster process was interrupted"


def test_ecs_pipes_waiter_config(pipes_ecs_client: PipesECSClient):
    with instance_for_test() as instance:
        """
        Test Error is thrown when the wait delay is less than the processing time.
        """
        os.environ.update({"WAIT_DELAY": "1", "WAIT_MAX_ATTEMPTS": "1", "SLEEP_SECONDS": "2"})
        with pytest.raises(botocore.exceptions.WaiterError, match=r".* Max attempts exceeded"):  # pyright: ignore (reportAttributeAccessIssue)
            materialize(
                [ecs_asset], instance=instance, resources={"pipes_ecs_client": pipes_ecs_client}
            )

        """
        Test Error is thrown when the wait attempts * wait delay is less than the processing time.
        """
        os.environ.update({"WAIT_DELAY": "1", "WAIT_MAX_ATTEMPTS": "2", "SLEEP_SECONDS": "3"})
        with pytest.raises(botocore.exceptions.WaiterError, match=r".* Max attempts exceeded"):  # pyright: ignore (reportAttributeAccessIssue)
            materialize(
                [ecs_asset], instance=instance, resources={"pipes_ecs_client": pipes_ecs_client}
            )

        """
        Test asset is materialized successfully when the wait attempts * wait delay is greater than the processing time.
        """
        os.environ.update({"WAIT_DELAY": "1", "WAIT_MAX_ATTEMPTS": "10", "SLEEP_SECONDS": "2"})
        materialize(
            [ecs_asset], instance=instance, resources={"pipes_ecs_client": pipes_ecs_client}
        )
        mat = instance.get_latest_materialization_event(ecs_asset.key)
        assert mat and mat.asset_materialization
