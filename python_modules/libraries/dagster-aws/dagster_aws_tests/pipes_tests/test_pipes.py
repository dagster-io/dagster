import base64
import inspect
import json
import multiprocessing
import os
import re
import shutil
import sys
import textwrap
import time
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any, Callable, Iterator, Literal, Tuple
from uuid import uuid4

import boto3
import pytest
from dagster import AssetsDefinition, asset, materialize, open_pipes_session
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
from moto.server import ThreadedMotoServer  # type: ignore  # (pyright bug)

from dagster_aws.pipes import (
    PipesCloudWatchMessageReader,
    PipesECSClient,
    PipesEMRServerlessClient,
    PipesGlueClient,
    PipesLambdaClient,
    PipesLambdaLogsMessageReader,
    PipesS3ContextInjector,
    PipesS3MessageReader,
)
from dagster_aws_tests.pipes_tests.fake_ecs import LocalECSMockClient
from dagster_aws_tests.pipes_tests.fake_glue import LocalGlueMockClient
from dagster_aws_tests.pipes_tests.fake_lambda import (
    LOG_TAIL_LIMIT,
    FakeLambdaClient,
    LambdaFunctions,
)

if TYPE_CHECKING:
    from mypy_boto3_ecs import ECSClient
    from mypy_boto3_emr_serverless import EMRServerlessClient

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
_MOTO_SERVER_PORT = 5193
_MOTO_SERVER_URL = f"http://localhost:{_MOTO_SERVER_PORT}"


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
        import time

        import boto3
        from dagster_pipes import PipesS3ContextLoader, PipesS3MessageWriter, open_dagster_pipes

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
def moto_server() -> Iterator[ThreadedMotoServer]:
    # We need to use the moto server for cross-process communication
    server = ThreadedMotoServer(port=_MOTO_SERVER_PORT)  # on localhost:5000 by default
    server.start()
    yield server
    server.stop()


@pytest.fixture
def s3_client(moto_server):
    client = boto3.client("s3", region_name="us-east-1", endpoint_url=_MOTO_SERVER_URL)
    client.create_bucket(Bucket=_S3_TEST_BUCKET)
    return client


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
def cloudwatch_client(moto_server, external_s3_glue_script, s3_client):
    return boto3.client("logs", region_name="us-east-1", endpoint_url=_MOTO_SERVER_URL)


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
            job_name=GLUE_JOB_NAME,
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
        client=LocalGlueMockClient(
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


@pytest.mark.parametrize("pipes_messages_backend", ["s3", "cloudwatch"])
def test_glue_pipes_params_argument(
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
            extras={"bar": "baz"},
            start_job_run_params={"JobName": GLUE_JOB_NAME, "Arguments": {"FOO": "BAR"}},
        ).get_results()
        return results

    context_injector = PipesS3ContextInjector(bucket=_S3_TEST_BUCKET, client=s3_client)
    message_reader = (
        PipesS3MessageReader(bucket=_S3_TEST_BUCKET, client=s3_client, interval=0.001)
        if pipes_messages_backend == "s3"
        else PipesCloudWatchMessageReader(client=cloudwatch_client)
    )

    pipes_glue_client = PipesGlueClient(
        client=LocalGlueMockClient(
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


@pytest.fixture
def glue_asset(long_glue_job: str) -> AssetsDefinition:
    @asset
    def foo(context: AssetExecutionContext, pipes_glue_client: PipesGlueClient):
        results = pipes_glue_client.run(
            context=context,
            job_name=long_glue_job,
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


@pytest.fixture
def ecs_client(moto_server, external_s3_glue_script, s3_client) -> "ECSClient":
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
                "name": "test-container",
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
                        "name": "test-container",
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
            assert len(pipes_ecs_client._client._task_runs) > 0  # noqa
            task_arn = next(iter(pipes_ecs_client._client._task_runs.keys()))  # noqa
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


EMR_SERVERLESS_APP_NAME = "Example"


@pytest.fixture
def emr_serverless_setup(
    moto_server, external_s3_glue_script, s3_client
) -> Tuple["EMRServerlessClient", str]:
    client = boto3.client("emr-serverless", region_name="us-east-1", endpoint_url=_MOTO_SERVER_URL)
    resp = client.create_application(
        type="SPARK",
        releaseLabel="emr-7.2.0-latest",
        clientToken=str(uuid4()),
    )
    return client, resp["applicationId"]


def test_emr_serverless_manual(emr_serverless_setup: Tuple["EMRServerlessClient", str]):
    client, application_id = emr_serverless_setup

    @asset
    def my_asset(context: AssetExecutionContext, emr_serverless_client: PipesEMRServerlessClient):
        message_reader = PipesCloudWatchMessageReader()
        context_injector = PipesEnvContextInjector()

        with open_pipes_session(
            context=context,
            message_reader=message_reader,
            context_injector=context_injector,
        ) as session:
            params = emr_serverless_client._enrich_start_params(  # noqa: SLF001
                context=context,
                session=session,
                params={
                    "applicationId": application_id,
                    "executionRoleArn": "arn:aws:iam::123456789012:role/EMRServerlessRole",
                    "jobDriver": {
                        "sparkSubmit": {
                            "entryPoint": "s3://my-bucket/my-script.py",
                        }
                    },
                    "clientToken": str(uuid4()),
                },
            )

            assert params["tags"]["dagster/run_id"] == context.run_id  # pyright: ignore[reportTypedDictNotRequiredAccess]
            assert (
                "--conf spark.emr-serverless.driverEnv.DAGSTER_PIPES_CONTEXT="
                in params["jobDriver"]["sparkSubmit"]["sparkSubmitParameters"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
            )
            assert (
                "--conf spark.emr-serverless.driverEnv.DAGSTER_PIPES_MESSAGES="
                in params["jobDriver"]["sparkSubmit"]["sparkSubmitParameters"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
            )

            # moto doesn't have start_job_run implemented so this is as far as we can get with it right now

            return session.get_results()

    with instance_for_test() as instance:
        materialize(
            [my_asset],
            resources={
                "emr_serverless_client": PipesEMRServerlessClient(
                    client=client,
                )
            },
            instance=instance,
        )
