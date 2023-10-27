import inspect
import re
import shutil
import subprocess
import textwrap
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Iterator

import boto3
import pytest
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSpec
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.data_version import (
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
)
from dagster._core.definitions.decorators.asset_decorator import asset, multi_asset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.metadata import (
    BoolMetadataValue,
    DagsterAssetMetadataValue,
    DagsterRunMetadataValue,
    FloatMetadataValue,
    IntMetadataValue,
    JsonMetadataValue,
    MarkdownMetadataValue,
    NotebookMetadataValue,
    NullMetadataValue,
    PathMetadataValue,
    TextMetadataValue,
    UrlMetadataValue,
)
from dagster._core.definitions.partition import DynamicPartitionsDefinition
from dagster._core.errors import DagsterInvariantViolationError, DagsterPipesExecutionError
from dagster._core.execution.context.compute import AssetExecutionContext, OpExecutionContext
from dagster._core.execution.context.invocation import build_asset_context
from dagster._core.instance_for_test import instance_for_test
from dagster._core.pipes.subprocess import (
    PipesSubprocessClient,
)
from dagster._core.pipes.utils import (
    PipesEnvContextInjector,
    PipesTempFileContextInjector,
    PipesTempFileMessageReader,
    open_pipes_session,
)
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from dagster_aws.pipes import PipesS3ContextInjector, PipesS3MessageReader
from moto.server import ThreadedMotoServer

_PYTHON_EXECUTABLE = shutil.which("python")


@contextmanager
def temp_script(script_fn: Callable[[], Any]) -> Iterator[str]:
    # drop the signature line
    source = textwrap.dedent(inspect.getsource(script_fn).split("\n", 1)[1])
    with NamedTemporaryFile() as file:
        file.write(source.encode())
        file.flush()
        yield file.name


_S3_TEST_BUCKET = "ext-testing"
_S3_SERVER_PORT = 5193
_S3_SERVER_URL = f"http://localhost:{_S3_SERVER_PORT}"


@pytest.fixture
def external_script() -> Iterator[str]:
    # This is called in an external process and so cannot access outer scope
    def script_fn():
        import os
        import time

        from dagster_pipes import (
            PipesS3ContextLoader,
            PipesS3MessageWriter,
            open_dagster_pipes,
        )

        context_injector_spec = os.getenv("CONTEXT_INJECTOR_SPEC")
        message_reader_spec = os.getenv("MESSAGE_READER_SPEC")

        context_loader = None
        message_writer = None
        if context_injector_spec == "user/s3" or message_reader_spec == "user/s3":
            import boto3

            client = boto3.client(
                "s3", region_name="us-east-1", endpoint_url="http://localhost:5193"
            )
            if context_injector_spec == "user/s3":
                context_loader = PipesS3ContextLoader(client=client)
            if message_reader_spec == "user/s3":
                message_writer = PipesS3MessageWriter(client, interval=0.001)

        with open_dagster_pipes(
            context_loader=context_loader, message_writer=message_writer
        ) as context:
            context.log.info("hello world")
            time.sleep(
                0.1
            )  # sleep to make sure that we encompass multiple intervals for blob store IO
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


@pytest.mark.parametrize(
    ("context_injector_spec", "message_reader_spec"),
    [
        ("default", "default"),
        ("default", "user/file"),
        ("default", "user/s3"),
        ("user/file", "default"),
        ("user/file", "user/file"),
        ("user/env", "default"),
        ("user/env", "user/file"),
        ("user/s3", "default"),
    ],
)
def test_pipes_subprocess(
    capsys, tmpdir, external_script, s3_client, context_injector_spec, message_reader_spec
):
    if context_injector_spec == "default":
        context_injector = None
    elif context_injector_spec == "user/file":
        context_injector = PipesTempFileContextInjector()
    elif context_injector_spec == "user/env":
        context_injector = PipesEnvContextInjector()
    elif context_injector_spec == "user/s3":
        context_injector = PipesS3ContextInjector(bucket=_S3_TEST_BUCKET, client=s3_client)
    else:
        assert False, "Unreachable"

    if message_reader_spec == "default":
        message_reader = None
    elif message_reader_spec == "user/file":
        message_reader = PipesTempFileMessageReader()
    elif message_reader_spec == "user/s3":
        message_reader = PipesS3MessageReader(
            bucket=_S3_TEST_BUCKET, client=s3_client, interval=0.001
        )
    else:
        assert False, "Unreachable"

    @asset(check_specs=[AssetCheckSpec(name="foo_check", asset=AssetKey(["foo"]))])
    def foo(context: AssetExecutionContext, ext: PipesSubprocessClient):
        extras = {"bar": "baz"}
        cmd = [_PYTHON_EXECUTABLE, external_script]
        return ext.run(
            command=cmd,
            context=context,
            extras=extras,
            env={
                "CONTEXT_INJECTOR_SPEC": context_injector_spec,
                "MESSAGE_READER_SPEC": message_reader_spec,
            },
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


def test_pipes_subprocess_client_no_return():
    def script_fn():
        from dagster_pipes import open_dagster_pipes

        with open_dagster_pipes() as context:
            context.report_asset_materialization()

    @asset
    def foo(context: OpExecutionContext, client: PipesSubprocessClient):
        with temp_script(script_fn) as external_script:
            cmd = [_PYTHON_EXECUTABLE, external_script]
            client.run(command=cmd, context=context).get_results()

    client = PipesSubprocessClient()
    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            r"did not yield or return expected outputs.*Did you forget to `yield from"
            r" pipes_session.get_results\(\)` or `return"
            r" <PipesClient>\.run\(\.\.\.\)\.get_results`?"
        ),
    ):
        materialize([foo], resources={"client": client})


def test_pipes_multi_asset():
    def script_fn():
        from dagster_pipes import open_dagster_pipes

        with open_dagster_pipes() as context:
            context.report_asset_materialization(
                {"foo_meta": "ok"}, data_version="alpha", asset_key="foo"
            )
            context.report_asset_materialization(data_version="alpha", asset_key="bar")

    @multi_asset(specs=[AssetSpec("foo"), AssetSpec("bar")])
    def foo_bar(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            return pipes_subprocess_client.run(command=cmd, context=context).get_results()

    with instance_for_test() as instance:
        materialize(
            [foo_bar],
            instance=instance,
            resources={"pipes_subprocess_client": PipesSubprocessClient()},
        )
        foo_mat = instance.get_latest_materialization_event(AssetKey(["foo"]))
        assert foo_mat and foo_mat.asset_materialization
        assert foo_mat.asset_materialization.metadata["foo_meta"].value == "ok"
        assert foo_mat.asset_materialization.tags
        assert foo_mat.asset_materialization.tags[DATA_VERSION_TAG] == "alpha"
        bar_mat = instance.get_latest_materialization_event(AssetKey(["foo"]))
        assert bar_mat and bar_mat.asset_materialization
        assert bar_mat.asset_materialization.tags
        assert bar_mat.asset_materialization.tags[DATA_VERSION_TAG] == "alpha"


def test_pipes_dynamic_partitions():
    def script_fn():
        from dagster_pipes import open_dagster_pipes

        with open_dagster_pipes() as _:
            pass

    @asset(partitions_def=DynamicPartitionsDefinition(name="blah"))
    def foo(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            return pipes_subprocess_client.run(command=cmd, context=context).get_results()

    with instance_for_test() as instance:
        instance.add_dynamic_partitions("blah", ["bar"])
        materialize(
            [foo],
            instance=instance,
            resources={"pipes_subprocess_client": PipesSubprocessClient()},
            partition_key="bar",
        )
        foo_mat = instance.get_latest_materialization_event(AssetKey(["foo"]))
        assert foo_mat and foo_mat.asset_materialization
        assert foo_mat.asset_materialization.partition == "bar"


def test_pipes_typed_metadata():
    def script_fn():
        from dagster_pipes import open_dagster_pipes

        with open_dagster_pipes() as context:
            context.report_asset_materialization(
                metadata={
                    "infer_meta": "bar",
                    "text_meta": {"raw_value": "bar", "type": "text"},
                    "url_meta": {"raw_value": "http://bar.com", "type": "url"},
                    "path_meta": {"raw_value": "/bar", "type": "path"},
                    "notebook_meta": {"raw_value": "/bar.ipynb", "type": "notebook"},
                    "json_meta": {"raw_value": ["bar"], "type": "json"},
                    "md_meta": {"raw_value": "bar", "type": "md"},
                    "float_meta": {"raw_value": 1.0, "type": "float"},
                    "int_meta": {"raw_value": 1, "type": "int"},
                    "bool_meta": {"raw_value": True, "type": "bool"},
                    "dagster_run_meta": {"raw_value": "foo", "type": "dagster_run"},
                    "asset_meta": {"raw_value": "bar/baz", "type": "asset"},
                    "null_meta": {"raw_value": None, "type": "null"},
                }
            )

    @asset
    def foo(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            return pipes_subprocess_client.run(command=cmd, context=context).get_results()

    with instance_for_test() as instance:
        materialize(
            [foo],
            instance=instance,
            resources={"pipes_subprocess_client": PipesSubprocessClient()},
        )
        mat = instance.get_latest_materialization_event(foo.key)
        assert mat and mat.asset_materialization
        metadata = mat.asset_materialization.metadata
        # assert isinstance(metadata["infer_meta"], TextMetadataValue)
        # assert metadata["infer_meta"].value == "bar"
        assert isinstance(metadata["text_meta"], TextMetadataValue)
        assert metadata["text_meta"].value == "bar"
        assert isinstance(metadata["url_meta"], UrlMetadataValue)
        assert metadata["url_meta"].value == "http://bar.com"
        assert isinstance(metadata["path_meta"], PathMetadataValue)
        assert metadata["path_meta"].value == "/bar"
        assert isinstance(metadata["notebook_meta"], NotebookMetadataValue)
        assert metadata["notebook_meta"].value == "/bar.ipynb"
        assert isinstance(metadata["json_meta"], JsonMetadataValue)
        assert metadata["json_meta"].value == ["bar"]
        assert isinstance(metadata["md_meta"], MarkdownMetadataValue)
        assert metadata["md_meta"].value == "bar"
        assert isinstance(metadata["float_meta"], FloatMetadataValue)
        assert metadata["float_meta"].value == 1.0
        assert isinstance(metadata["int_meta"], IntMetadataValue)
        assert metadata["int_meta"].value == 1
        assert isinstance(metadata["bool_meta"], BoolMetadataValue)
        assert metadata["bool_meta"].value is True
        assert isinstance(metadata["dagster_run_meta"], DagsterRunMetadataValue)
        assert metadata["dagster_run_meta"].value == "foo"
        assert isinstance(metadata["asset_meta"], DagsterAssetMetadataValue)
        assert metadata["asset_meta"].value == AssetKey(["bar", "baz"])
        assert isinstance(metadata["null_meta"], NullMetadataValue)
        assert metadata["null_meta"].value is None


def test_pipes_asset_failed():
    def script_fn():
        raise Exception("foo")

    @asset
    def foo(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            return pipes_subprocess_client.run(command=cmd, context=context).get_results()

    with pytest.raises(DagsterPipesExecutionError):
        materialize([foo], resources={"pipes_subprocess_client": PipesSubprocessClient()})


def test_pipes_asset_invocation():
    def script_fn():
        from dagster_pipes import open_dagster_pipes

        with open_dagster_pipes() as context:
            context.log.info("hello world")

    @asset
    def foo(context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            yield from pipes_subprocess_client.run(command=cmd, context=context).get_results()

    foo(context=build_asset_context(), pipes_subprocess_client=PipesSubprocessClient())


PATH_WITH_NONEXISTENT_DIR = "/tmp/does-not-exist/foo"


def test_pipes_no_orchestration():
    def script_fn():
        from dagster_pipes import (
            PipesContext,
            PipesEnvVarParamsLoader,
            open_dagster_pipes,
        )

        loader = PipesEnvVarParamsLoader()
        assert not loader.is_dagster_pipes_process()
        with open_dagster_pipes(params_loader=loader) as _:
            context = PipesContext.get()
            context.log.info("hello world")
            context.report_asset_materialization(
                metadata={"bar": context.get_extra("bar")},
                data_version="alpha",
            )

    with temp_script(script_fn) as script_path:
        cmd = ["python", script_path]
        _, stderr = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
        assert re.search(
            r"This process was not launched by a Dagster orchestration process.",
            stderr.decode(),
        )


def test_pipes_no_client(external_script):
    @asset(check_specs=[AssetCheckSpec(name="foo_check", asset=AssetKey(["subproc_run"]))])
    def subproc_run(context: AssetExecutionContext):
        extras = {"bar": "baz"}
        cmd = [_PYTHON_EXECUTABLE, external_script]

        with open_pipes_session(
            context,
            PipesTempFileContextInjector(),
            PipesTempFileMessageReader(),
            extras=extras,
        ) as pipes_session:
            subprocess.run(cmd, env=pipes_session.get_bootstrap_env_vars(), check=False)
        yield from pipes_session.get_results()

    with instance_for_test() as instance:
        materialize(
            [subproc_run],
            instance=instance,
        )
        mat = instance.get_latest_materialization_event(subproc_run.key)
        assert mat and mat.asset_materialization
        assert mat.asset_materialization.metadata["bar"].value == "baz"
        assert mat.asset_materialization.tags
        assert mat.asset_materialization.tags[DATA_VERSION_TAG] == "alpha"
        assert mat.asset_materialization.tags[DATA_VERSION_IS_USER_PROVIDED_TAG]

        asset_check_executions = instance.event_log_storage.get_asset_check_execution_history(
            AssetCheckKey(
                asset_key=subproc_run.key,
                name="foo_check",
            ),
            limit=1,
        )
        assert len(asset_check_executions) == 1
        assert asset_check_executions[0].status == AssetCheckExecutionRecordStatus.SUCCEEDED


def test_pipes_no_client_no_yield():
    def script_fn():
        from dagster_pipes import open_dagster_pipes

        with open_dagster_pipes() as _:
            pass

    @asset
    def foo(context: OpExecutionContext):
        with temp_script(script_fn) as external_script:
            with open_pipes_session(
                context,
                PipesTempFileContextInjector(),
                PipesTempFileMessageReader(),
            ) as pipes_session:
                cmd = [_PYTHON_EXECUTABLE, external_script]
                subprocess.run(cmd, env=pipes_session.get_bootstrap_env_vars(), check=False)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            r"did not yield or return expected outputs.*Did you forget to `yield from"
            r" pipes_session.get_results\(\)` or `return"
            r" <PipesClient>\.run\(\.\.\.\)\.get_results`?"
        ),
    ):
        materialize([foo])


def test_pipes_manual_close():
    def script_fn():
        from dagster_pipes import open_dagster_pipes

        context = open_dagster_pipes()
        context.report_asset_materialization(data_version="alpha")
        context.close()

    @asset
    def foo(context: OpExecutionContext, pipes_client: PipesSubprocessClient):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            return pipes_client.run(command=cmd, context=context).get_results()

    with instance_for_test() as instance:
        materialize([foo], instance=instance, resources={"pipes_client": PipesSubprocessClient()})
        mat = instance.get_latest_materialization_event(foo.key)
        assert mat and mat.asset_materialization


def test_pipes_no_close():
    def script_fn():
        from dagster_pipes import open_dagster_pipes

        context = open_dagster_pipes()
        context.report_asset_materialization(data_version="alpha")

    @asset
    def foo(context: OpExecutionContext, pipes_client: PipesSubprocessClient):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            return pipes_client.run(command=cmd, context=context).get_results()

    with instance_for_test() as instance:
        result = materialize(
            [foo], instance=instance, resources={"pipes_client": PipesSubprocessClient()}
        )
        assert result.success  # doesn't fail out, just warns
        conn = instance.get_records_for_run(result.run_id)
        pipes_msgs = [
            record.event_log_entry.user_message
            for record in conn.records
            if record.event_log_entry.user_message.startswith("[pipes]")
        ]
        assert len(pipes_msgs) == 2
        assert "successfully opened" in pipes_msgs[0]
        assert "did not receive closed message" in pipes_msgs[1]
