import multiprocessing
import os
import re
import time
from collections.abc import Iterator
from typing import Literal

import boto3
import pytest
from dagster import AssetsDefinition, asset, materialize
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

from dagster_aws.pipes import (
    PipesCloudWatchMessageReader,
    PipesGlueClient,
    PipesS3ContextInjector,
    PipesS3MessageReader,
)
from dagster_aws_tests.pipes_tests.fake_glue import LocalGlueMockClient
from dagster_aws_tests.pipes_tests.utils import _MOTO_SERVER_URL, _S3_TEST_BUCKET, temp_script

GLUE_JOB_NAME = "test-job"


@pytest.fixture
def external_s3_glue_script(s3_client) -> Iterator[str]:
    # This is called in an external process and so cannot access outer scope
    def script_fn():
        import os
        import time

        import boto3
        from dagster_pipes import (
            PipesCliArgsParamsLoader,
            PipesS3ContextLoader,
            PipesS3MessageWriter,
            open_dagster_pipes,
        )

        s3_client = boto3.client(
            "s3", region_name="us-east-1", endpoint_url="http://localhost:5193"
        )

        messages_backend = os.environ["TESTING_PIPES_MESSAGES_BACKEND"]
        if messages_backend == "s3":
            message_writer = PipesS3MessageWriter(s3_client, interval=0.001)
        else:
            message_writer = None

        with open_dagster_pipes(
            context_loader=PipesS3ContextLoader(client=s3_client),
            message_writer=message_writer,
            params_loader=PipesCliArgsParamsLoader(),
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
        s3_client.upload_file(script_path, _S3_TEST_BUCKET, "glue_script.py")
        # yield path on s3
        yield f"s3://{_S3_TEST_BUCKET}/glue_script.py"


@pytest.fixture
def glue_client(moto_server, external_s3_glue_script, s3_client):
    client = boto3.client("glue", region_name="us-east-1", endpoint_url=_MOTO_SERVER_URL)
    client.create_job(
        Name=GLUE_JOB_NAME,
        Description="Test job",
        Command={
            "Name": "glueetl",  # Spark job type
            "ScriptLocation": external_s3_glue_script,
            "PythonVersion": "3.10",
        },
        GlueVersion="4.0",
        Role="arn:aws:iam::012345678901:role/service-role/AWSGlueServiceRole-test",
    )
    return client


@pytest.fixture
def long_glue_job(s3_client, glue_client) -> Iterator[str]:
    job_name = "Very Long Job"

    def script_fn():
        import os
        import time

        import boto3
        from dagster_pipes import PipesCliArgsParamsLoader, PipesS3ContextLoader, open_dagster_pipes

        s3_client = boto3.client(
            "s3", region_name="us-east-1", endpoint_url="http://localhost:5193"
        )

        with open_dagster_pipes(
            context_loader=PipesS3ContextLoader(client=s3_client),
            params_loader=PipesCliArgsParamsLoader(),
        ) as context:
            context.log.info("Glue job sleeping...")
            time.sleep(int(os.getenv("SLEEP_SECONDS", "1")))

    with temp_script(script_fn) as script_path:
        s3_key = "long_glue_script.py"
        s3_client.upload_file(script_path, _S3_TEST_BUCKET, s3_key)

        glue_client.create_job(
            Name=job_name,
            Description="Test job",
            Command={
                "Name": "glueetl",  # Spark job type
                "ScriptLocation": f"s3://{_S3_TEST_BUCKET}/{s3_key}",
                "PythonVersion": "3.10",
            },
            GlueVersion="4.0",
            Role="arn:aws:iam::012345678901:role/service-role/AWSGlueServiceRole-test",
        )

        yield job_name


@pytest.fixture
def glue_asset(long_glue_job: str) -> AssetsDefinition:
    @asset
    def foo(context: AssetExecutionContext, pipes_glue_client: PipesGlueClient):
        results = pipes_glue_client.run(
            context=context,
            start_job_run_params={"JobName": long_glue_job},
        ).get_results()
        return results

    return foo


@pytest.fixture
def local_glue_mock_client(glue_client, s3_client, cloudwatch_client) -> LocalGlueMockClient:
    return LocalGlueMockClient(
        aws_endpoint_url=_MOTO_SERVER_URL,
        glue_client=glue_client,
        s3_client=s3_client,
        cloudwatch_client=cloudwatch_client,
        pipes_messages_backend="cloudwatch",
    )


@pytest.fixture
def pipes_glue_client(local_glue_mock_client, s3_client, cloudwatch_client) -> PipesGlueClient:
    return PipesGlueClient(
        client=local_glue_mock_client,
        context_injector=PipesS3ContextInjector(bucket=_S3_TEST_BUCKET, client=s3_client),
        message_reader=PipesCloudWatchMessageReader(client=cloudwatch_client),
    )


@pytest.mark.parametrize("pipes_messages_backend", ["s3", "cloudwatch"])
def test_glue_pipes(
    capsys,
    s3_client,
    glue_client,
    cloudwatch_client,
    pipes_messages_backend: Literal["s3", "cloudwatch"],
):
    @asset(check_specs=[AssetCheckSpec(name="foo_check", asset=AssetKey(["foo"]))])
    def foo(context: AssetExecutionContext, pipes_glue_client: PipesGlueClient):
        results = pipes_glue_client.run(
            context=context,
            start_job_run_params={"JobName": GLUE_JOB_NAME},
            extras={"bar": "baz"},
        ).get_results()
        return results

    context_injector = PipesS3ContextInjector(bucket=_S3_TEST_BUCKET, client=s3_client)
    message_reader = (
        PipesS3MessageReader(bucket=_S3_TEST_BUCKET, client=s3_client, interval=0.001)
        if pipes_messages_backend == "s3"
        else PipesCloudWatchMessageReader(client=cloudwatch_client)
    )

    pipes_glue_client = PipesGlueClient(
        client=LocalGlueMockClient(  # pyright: ignore[reportArgumentType]
            aws_endpoint_url=_MOTO_SERVER_URL,
            glue_client=glue_client,
            s3_client=s3_client,
            cloudwatch_client=cloudwatch_client,
            pipes_messages_backend=pipes_messages_backend,
        ),
        context_injector=context_injector,
        message_reader=message_reader,
    )

    with instance_for_test() as instance:
        materialize([foo], instance=instance, resources={"pipes_glue_client": pipes_glue_client})
        mat = instance.get_latest_materialization_event(foo.key)
        assert mat and mat.asset_materialization
        assert isinstance(mat.asset_materialization.metadata["bar"], MarkdownMetadataValue)
        assert mat.asset_materialization.metadata["bar"].value == "baz"
        assert "AWS Glue Job Run ID" in mat.asset_materialization.metadata
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


def test_glue_pipes_interruption_forwarding_asset_is_valid(glue_asset, pipes_glue_client):
    # make sure this runs without multiprocessing first

    with instance_for_test() as instance:
        materialize(
            [glue_asset], instance=instance, resources={"pipes_glue_client": pipes_glue_client}
        )


def test_glue_pipes_interruption_forwarding(long_glue_job, glue_asset, pipes_glue_client):
    def materialize_asset(env, return_dict):
        os.environ.update(env)
        try:
            with instance_for_test() as instance:
                materialize(  # this will be interrupted and raise an exception
                    [glue_asset],
                    instance=instance,
                    resources={"pipes_glue_client": pipes_glue_client},
                )
        finally:
            job_run_id = next(iter(pipes_glue_client._client._job_runs.keys()))  # noqa
            return_dict[0] = pipes_glue_client._client.get_job_run(long_glue_job, job_run_id)  # noqa

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
            time.sleep(3)
            p.terminate()

        p.join()
        assert not p.is_alive()
        assert return_dict[0]["JobRun"]["JobRunState"] == "STOPPED"
