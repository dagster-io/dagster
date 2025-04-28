from collections.abc import Iterator
from typing import TYPE_CHECKING

import boto3
import pytest
from moto.server import ThreadedMotoServer  # type: ignore  # (pyright bug)

from dagster_aws_tests.pipes_tests.utils import (
    _MOTO_SERVER_PORT,
    _MOTO_SERVER_URL,
    _S3_TEST_BUCKET,
    temp_script,
)

if TYPE_CHECKING:
    from mypy_boto3_logs import CloudWatchLogsClient


@pytest.fixture
def moto_server() -> Iterator[ThreadedMotoServer]:
    # We need to use the moto server for cross-process communication
    server = ThreadedMotoServer(port=_MOTO_SERVER_PORT)  # on localhost:5000 by default
    server.start()
    yield server
    server.stop()


@pytest.fixture
def s3_client(moto_server: ThreadedMotoServer):
    client = boto3.client("s3", region_name="us-east-1", endpoint_url=_MOTO_SERVER_URL)
    client.create_bucket(Bucket=_S3_TEST_BUCKET)
    return client


@pytest.fixture
def cloudwatch_client(moto_server, s3_client) -> "CloudWatchLogsClient":
    return boto3.client("logs", region_name="us-east-1", endpoint_url=_MOTO_SERVER_URL)


@pytest.fixture
def external_script_default_components() -> Iterator[str]:
    # This is called in an external process and so cannot access outer scope
    def script_fn():
        import os
        import time

        from dagster_pipes import open_dagster_pipes

        with open_dagster_pipes() as context:
            context.log.info("hello world")
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
            time.sleep(float(os.getenv("SLEEP_SECONDS", "0.1")))

    with temp_script(script_fn) as script_path:
        yield script_path


@pytest.fixture
def external_script() -> Iterator[str]:
    # This is called in an external process and so cannot access outer scope
    def script_fn():
        import os  # noqa
        import time

        import boto3
        from dagster_pipes import PipesS3ContextLoader, PipesS3MessageWriter, open_dagster_pipes

        # this url has to be hardcoded because it's an external script
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
