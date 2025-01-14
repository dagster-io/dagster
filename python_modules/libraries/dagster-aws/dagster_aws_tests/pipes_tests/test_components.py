import json
import re
import sys
import threading
import time
from datetime import datetime
from threading import Event
from typing import TYPE_CHECKING
from uuid import uuid4

from dagster import asset, materialize, open_pipes_session
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSpec
from dagster._core.definitions.data_version import (
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MarkdownMetadataValue
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.instance_for_test import instance_for_test
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster._core.pipes.utils import PipesEnvContextInjector
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from dagster_pipes import _make_message

from dagster_aws.pipes import (
    PipesCloudWatchLogReader,
    PipesCloudWatchMessageReader,
    PipesS3ContextInjector,
    PipesS3LogReader,
    PipesS3MessageReader,
)
from dagster_aws_tests.pipes_tests.utils import _PYTHON_EXECUTABLE, _S3_TEST_BUCKET

if TYPE_CHECKING:
    from mypy_boto3_logs import CloudWatchLogsClient


def test_s3_log_reader(s3_client, capsys):
    key = str(uuid4())
    log_reader = PipesS3LogReader(client=s3_client, bucket=_S3_TEST_BUCKET, key=key)
    is_session_closed = Event()

    assert not log_reader.target_is_readable({})

    s3_client.put_object(Bucket=_S3_TEST_BUCKET, Key=key, Body=b"Line 0\nLine 1")

    assert log_reader.target_is_readable({})

    log_reader.start({}, is_session_closed)
    assert log_reader.is_running()

    s3_client.put_object(Bucket=_S3_TEST_BUCKET, Key=key, Body=b"Line 0\nLine 1\nLine 2")

    is_session_closed.set()

    log_reader.stop()

    assert not log_reader.is_running()

    captured = capsys.readouterr()

    assert captured.out == "Line 0\nLine 1\nLine 2"

    assert sys.stdout is not None


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


def test_cloudwatch_logs_reader(cloudwatch_client: "CloudWatchLogsClient", capsys):
    reader = PipesCloudWatchLogReader(client=cloudwatch_client)

    is_session_closed = threading.Event()

    log_group = "/pipes/tests"
    log_stream = "test-cloudwatch-logs-reader"

    assert not reader.target_is_readable(
        {"log_group": log_group, "log_stream": log_stream}
    ), "Should not be able to read without the stream existing"

    cloudwatch_client.create_log_group(logGroupName=log_group)
    cloudwatch_client.create_log_stream(logGroupName=log_group, logStreamName=log_stream)

    cloudwatch_client.put_log_events(
        logGroupName=log_group,
        logStreamName=log_stream,
        logEvents=[{"timestamp": int(datetime.now().timestamp() * 1000), "message": "1"}],
    )

    time.sleep(0.1)

    assert reader.target_is_readable(
        {"log_group": log_group, "log_stream": log_stream}
    ), "Should be able to read after the stream is created"

    reader.start({"log_group": log_group, "log_stream": log_stream}, is_session_closed)

    cloudwatch_client.put_log_events(
        logGroupName=log_group,
        logStreamName=log_stream,
        logEvents=[
            {
                "timestamp": int(datetime.now().timestamp() * 1000),
                "message": "2",
            }
        ],
    )

    time.sleep(0.1)

    cloudwatch_client.put_log_events(
        logGroupName=log_group,
        logStreamName=log_stream,
        logEvents=[
            {
                "timestamp": int(datetime.now().timestamp() * 1000),
                "message": "3",
            }
        ],
    )

    time.sleep(0.1)

    is_session_closed.set()

    time.sleep(1)

    reader.stop()

    time.sleep(1)

    assert capsys.readouterr().out.strip() == "1\n2\n3"


def test_cloudwatch_message_reader(cloudwatch_client: "CloudWatchLogsClient", capsys):
    log_group = "/pipes/tests/messages"
    messages_log_stream = "test-cloudwatch-messages-reader"
    logs_log_stream = "test-cloudwatch-messages-reader-stdout"

    reader = PipesCloudWatchMessageReader(client=cloudwatch_client)

    @asset
    def my_asset(context: AssetExecutionContext):
        with open_pipes_session(
            context=context, message_reader=reader, context_injector=PipesEnvContextInjector()
        ) as session:
            assert not reader.messages_are_readable({})

            cloudwatch_client.create_log_group(logGroupName=log_group)
            cloudwatch_client.create_log_stream(
                logGroupName=log_group, logStreamName=messages_log_stream
            )
            cloudwatch_client.create_log_stream(
                logGroupName=log_group, logStreamName=logs_log_stream
            )

            assert not reader.messages_are_readable({})

            new_params = {
                "log_group": log_group,
                "log_stream": messages_log_stream,
            }

            session.report_launched({"extras": new_params})

            assert reader.launched_payload is not None

            assert reader.messages_are_readable(reader.launched_payload["extras"])

            def log_event(message: str):
                cloudwatch_client.put_log_events(
                    logGroupName=log_group,
                    logStreamName=messages_log_stream,
                    logEvents=[
                        {"timestamp": int(datetime.now().timestamp() * 1000), "message": message}
                    ],
                )

            def log_line(message: str):
                cloudwatch_client.put_log_events(
                    logGroupName=log_group,
                    logStreamName=logs_log_stream,
                    logEvents=[
                        {"timestamp": int(datetime.now().timestamp() * 1000), "message": message}
                    ],
                )

            log_event(json.dumps(_make_message(method="opened", params={})))

            log_event(
                json.dumps(
                    _make_message(method="log", params={"message": "Hello!", "level": "INFO"})
                )
            )

            log_event(
                json.dumps(
                    _make_message(
                        method="report_asset_materialization",
                        params={
                            "asset_key": "my_asset",
                            "metadata": {"foo": {"raw_value": "bar", "type": "text"}},
                            "data_version": "alpha",
                        },
                    )
                )
            )

            log_event(json.dumps(_make_message(method="closed", params={})))

            log_line("Hello 1")

            log_reader = PipesCloudWatchLogReader(
                client=cloudwatch_client,
                log_group=log_group,
                log_stream=logs_log_stream,
                target_stream=sys.stdout,
                start_time=int(session.created_at.timestamp() * 1000),
            )
            reader.add_log_reader(log_reader)

            log_line("Hello 2")

            assert log_reader.target_is_readable({})

        return session.get_results()

    result = materialize([my_asset])

    assert result.success

    mats = result.get_asset_materialization_events()
    assert len(mats) == 1
    mat = mats[0]
    assert mat.asset_key == AssetKey(["my_asset"])
    assert mat.materialization.metadata["foo"].value == "bar"
    assert mat.materialization.tags[DATA_VERSION_TAG] == "alpha"  # type: ignore

    captured = capsys.readouterr()
    assert "Hello 1" in captured.out
    assert "Hello 2" in captured.out
