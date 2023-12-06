import base64
import inspect
import json
import re
import shutil
import textwrap
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Iterator

import boto3
import pytest
from dagster import asset, materialize, open_pipes_session
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSpec
from dagster._core.definitions.data_version import (
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import (
    MarkdownMetadataValue,
)
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.instance_for_test import instance_for_test
from dagster._core.pipes.subprocess import (
    PipesSubprocessClient,
)
from dagster._core.pipes.utils import PipesEnvContextInjector
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from dagster_aws.pipes import (
    PipesLambdaClient,
    PipesLambdaLogsMessageReader,
    PipesS3ContextInjector,
    PipesS3MessageReader,
)
from moto.server import ThreadedMotoServer

from .fake_lambda import LOG_TAIL_LIMIT, FakeLambdaClient, LambdaFunctions

_PYTHON_EXECUTABLE = shutil.which("python") or "python"


@contextmanager
def temp_script(script_fn: Callable[[], Any]) -> Iterator[str]:
    # drop the signature line
    source = textwrap.dedent(inspect.getsource(script_fn).split("\n", 1)[1])
    with NamedTemporaryFile() as file:
        file.write(source.encode())
        file.flush()
        yield file.name


_S3_TEST_BUCKET = "pipes-testing"
_S3_SERVER_PORT = 5193
_S3_SERVER_URL = f"http://localhost:{_S3_SERVER_PORT}"


@pytest.fixture
def external_script() -> Iterator[str]:
    # This is called in an external process and so cannot access outer scope
    def script_fn():
        import time

        import boto3
        from dagster_pipes import (
            PipesS3ContextLoader,
            PipesS3MessageWriter,
            open_dagster_pipes,
        )

        client = boto3.client("s3", region_name="us-east-1", endpoint_url="http://localhost:5193")
        context_loader = PipesS3ContextLoader(client=client)
        message_writer = PipesS3MessageWriter(client, interval=0.001)

        with open_dagster_pipes(
            context_loader=context_loader, message_writer=message_writer
        ) as context:
            context.log.info("hello world")
            time.sleep(0.1)  # sleep to make sure that we encompass multiple intervals for S3 IO
            context.report_asset_materialization(
                metadata={"bar": {"raw_value": context.get_extra("bar"), "type": "md"}},
                data_version="alpha",
            )
            context.report_asset_check(
                "foo_check",
                passed=True,
                severity="WARN",
                metadata={
                    "meta_1": 1,
                    "meta_2": {"raw_value": "foo", "type": "text"},
                },
            )

    with temp_script(script_fn) as script_path:
        yield script_path


@pytest.fixture
def s3_client() -> Iterator[boto3.client]:
    # We need to use the moto server for cross-process communication
    server = ThreadedMotoServer(port=5193)  # on localhost:5000 by default
    server.start()
    client = boto3.client("s3", region_name="us-east-1", endpoint_url=_S3_SERVER_URL)
    client.create_bucket(Bucket=_S3_TEST_BUCKET)
    yield client
    server.stop()


def test_s3_pipes_components(
    capsys,
    tmpdir,
    external_script,
    s3_client,
):
    context_injector = PipesS3ContextInjector(bucket=_S3_TEST_BUCKET, client=s3_client)
    message_reader = PipesS3MessageReader(bucket=_S3_TEST_BUCKET, client=s3_client, interval=0.001)

    @asset(check_specs=[AssetCheckSpec(name="foo_check", asset=AssetKey(["foo"]))])
    def foo(context: AssetExecutionContext, ext: PipesSubprocessClient):
        return ext.run(
            command=[_PYTHON_EXECUTABLE, external_script],
            context=context,
            extras={"bar": "baz"},
            env={},
        ).get_results()

    resource = PipesSubprocessClient(
        context_injector=context_injector, message_reader=message_reader
    )

    with instance_for_test() as instance:
        materialize([foo], instance=instance, resources={"ext": resource})
        mat = instance.get_latest_materialization_event(foo.key)
        assert mat and mat.asset_materialization
        assert isinstance(mat.asset_materialization.metadata["bar"], MarkdownMetadataValue)
        assert mat.asset_materialization.metadata["bar"].value == "baz"
        assert mat.asset_materialization.tags
        assert mat.asset_materialization.tags[DATA_VERSION_TAG] == "alpha"
        assert mat.asset_materialization.tags[DATA_VERSION_IS_USER_PROVIDED_TAG]

        captured = capsys.readouterr()
        assert re.search(r"dagster - INFO - [^\n]+ - hello world\n", captured.err, re.MULTILINE)

        asset_check_executions = instance.event_log_storage.get_asset_check_execution_history(
            check_key=AssetCheckKey(foo.key, name="foo_check"),
            limit=1,
        )
        assert len(asset_check_executions) == 1
        assert asset_check_executions[0].status == AssetCheckExecutionRecordStatus.SUCCEEDED


def test_fake_lambda_logs():
    event = {}
    response = FakeLambdaClient().invoke(
        FunctionName=LambdaFunctions.trunc_logs.__name__,
        InvocationType="RequestResponse",
        Payload=json.dumps(event),
        LogType="Tail",
    )

    log_result = base64.b64decode(response["LogResult"])
    assert len(log_result) == LOG_TAIL_LIMIT

    small_size = 512
    response = FakeLambdaClient().invoke(
        FunctionName=LambdaFunctions.small_logs.__name__,
        InvocationType="RequestResponse",
        Payload=json.dumps({"size": small_size}),
        LogType="Tail",
    )

    log_result = base64.b64decode(response["LogResult"])
    assert len(log_result) == small_size + 1  # size + \n


def test_manual_fake_lambda_pipes():
    @asset
    def fake_lambda_asset(context):
        context_injector = PipesEnvContextInjector()
        message_reader = PipesLambdaLogsMessageReader()

        with open_pipes_session(
            context=context,
            message_reader=message_reader,
            context_injector=context_injector,
        ) as session:
            user_event = {}
            response = FakeLambdaClient().invoke(
                FunctionName=LambdaFunctions.pipes_basic.__name__,
                InvocationType="RequestResponse",
                Payload=json.dumps(
                    {
                        **user_event,
                        **session.get_bootstrap_env_vars(),
                    }
                ),
                LogType="Tail",
            )
            message_reader.consume_lambda_logs(response)
            yield from session.get_results()

    result = materialize([fake_lambda_asset])
    assert result.success
    mat_evts = result.get_asset_materialization_events()
    assert len(mat_evts) == 1
    assert mat_evts[0].materialization.metadata["meta"].value == "data"


@pytest.mark.parametrize(
    "lambda_fn",
    [
        LambdaFunctions.pipes_basic.__name__,
        LambdaFunctions.pipes_messy_logs.__name__,
    ],
)
def test_client_lambda_pipes(lambda_fn):
    @asset
    def fake_lambda_asset(context):
        return (
            PipesLambdaClient(FakeLambdaClient())
            .run(
                context=context,
                function_name=lambda_fn,
                event={},
            )
            .get_materialize_result()
        )

    result = materialize([fake_lambda_asset])
    assert result.success
    mat_evts = result.get_asset_materialization_events()
    assert len(mat_evts) == 1
    assert mat_evts[0].materialization.metadata["meta"].value == "data"


def test_fake_client_lambda_error():
    @asset
    def fake_lambda_asset(context):
        yield from (
            PipesLambdaClient(FakeLambdaClient())
            .run(
                context=context,
                function_name=LambdaFunctions.error.__name__,
                event={},
            )
            .get_results()
        )

    with pytest.raises(Exception, match="Lambda Function Error"):
        materialize([fake_lambda_asset])


def test_lambda_s3_pipes(s3_client):
    @asset
    def fake_lambda_asset(context):
        return (
            PipesLambdaClient(
                FakeLambdaClient(),
                message_reader=PipesS3MessageReader(
                    client=s3_client,
                    bucket=_S3_TEST_BUCKET,
                    interval=0.01,
                ),
            )
            .run(
                context=context,
                function_name=LambdaFunctions.pipes_s3_messages.__name__,
                event={},
            )
            .get_materialize_result()
        )

    result = materialize([fake_lambda_asset])
    assert result.success
    mat_evts = result.get_asset_materialization_events()
    assert len(mat_evts) == 1
    assert mat_evts[0].materialization.metadata["meta"].value == "data"
