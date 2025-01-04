from typing import Iterator, Literal

import boto3
import pytest
from dagster import asset, materialize
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSpec
from dagster._core.definitions.events import AssetKey
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from moto.server import ThreadedMotoServer  # type: ignore  # (pyright bug)

from dagster_aws.pipes import PipesS3ContextInjector, PipesS3MessageReader
from dagster_aws.pipes.clients.sfn import PipesSFNClient
from dagster_aws_tests.pipes_tests.fake_sfn import LocalSfnMockClient

_S3_TEST_BUCKET = "pipes-testing"
_MOTO_SERVER_PORT = 5193
_MOTO_SERVER_URL = f"http://localhost:{_MOTO_SERVER_PORT}"


@pytest.fixture
def sfn_mock_client():
    return LocalSfnMockClient()


@pytest.fixture
def moto_server() -> Iterator[ThreadedMotoServer]:
    # We need to use the moto server for cross-process communication
    server = ThreadedMotoServer(port=_MOTO_SERVER_PORT)  # on localhost:5000 by default
    server.start()
    yield server
    server.stop()


@pytest.fixture
def s3_client(moto_server):
    s3_client = boto3.client(
        "s3",
        endpoint_url=_MOTO_SERVER_URL,
    )
    response = s3_client.create_bucket(Bucket=_S3_TEST_BUCKET)
    if not response:
        raise Exception("Failed to create bucket")
    return s3_client


@pytest.mark.parametrize("pipes_messages_backend", ["s3"])
def test_step_function_pipes(
    sfn_mock_client,
    s3_client,
    # cloudwatch_client,
    pipes_messages_backend: Literal["s3", "cloudwatch"],
) -> None:
    @asset(check_specs=[AssetCheckSpec(name="foo_check", asset=AssetKey(["foo"]))])
    def foo(context: AssetExecutionContext, pipes_sfn_client: PipesSFNClient):
        result = pipes_sfn_client.run(
            context=context,
            start_execution_input={
                "stateMachineArn": "arn:aws:states:us-east-1:123456789012:stateMachine:TestSFN"
            },
        ).get_results()
        return result

    context_injector = PipesS3ContextInjector(bucket=_S3_TEST_BUCKET, client=s3_client)
    message_reader = (
        PipesS3MessageReader(bucket=_S3_TEST_BUCKET, client=s3_client, interval=0.001)
        # if pipes_messages_backend == "s3"
        # else PipesCloudWatchMessageReader(client=cloudwatch_client)
    )
    with instance_for_test() as instance:
        materialize(
            [foo],
            resources={
                "pipes_sfn_client": PipesSFNClient(
                    client=sfn_mock_client,
                    context_injector=context_injector,
                    message_reader=message_reader,
                )
            },
            instance=instance,
        )
        mat = instance.get_latest_materialization_event(foo.key)
        assert mat and mat.asset_materialization
        assert "executionArn" in mat.asset_materialization.metadata
        assert mat.asset_materialization.metadata["status"].value == "SUCCEEDED"
        asset_check_executions = instance.event_log_storage.get_asset_check_execution_history(
            check_key=AssetCheckKey(foo.key, name="foo_check"),
            limit=1,
        )
        assert len(asset_check_executions) == 1
        assert asset_check_executions[0].status == AssetCheckExecutionRecordStatus.SUCCEEDED
