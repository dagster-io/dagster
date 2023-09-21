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
from dagster._core.definitions.data_version import (
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
)
from dagster._core.definitions.decorators.asset_decorator import asset
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
from dagster._core.errors import DagsterExternalExecutionError
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.execution.context.invocation import build_asset_context
from dagster._core.ext.subprocess import (
    ExtSubprocess,
)
from dagster._core.ext.utils import (
    ExtEnvContextInjector,
    ExtTempFileContextInjector,
    ExtTempFileMessageReader,
    ext_protocol,
)
from dagster._core.instance_for_test import instance_for_test
from dagster_aws.ext import ExtS3MessageReader
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

        from dagster_ext import (
            ExtContext,
            ExtS3MessageWriter,
            init_dagster_ext,
        )

        if os.getenv("MESSAGE_READER_SPEC") == "user/s3":
            import boto3

            client = boto3.client(
                "s3", region_name="us-east-1", endpoint_url="http://localhost:5193"
            )
            message_writer = ExtS3MessageWriter(client, interval=0.001)
        else:
            message_writer = None  # use default

        init_dagster_ext(message_writer=message_writer)
        context = ExtContext.get()
        context.log("hello world")
        time.sleep(0.1)  # sleep to make sure that we encompass multiple intervals for blob store IO
        context.report_asset_materialization(
            metadata={"bar": {"raw_value": context.get_extra("bar"), "type": "md"}},
            data_version="alpha",
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
    ],
)
def test_ext_subprocess(
    capsys, tmpdir, external_script, s3_client, context_injector_spec, message_reader_spec
):
    if context_injector_spec == "default":
        context_injector = None
    elif context_injector_spec == "user/file":
        context_injector = ExtTempFileContextInjector()
    elif context_injector_spec == "user/env":
        context_injector = ExtEnvContextInjector()
    else:
        assert False, "Unreachable"

    if message_reader_spec == "default":
        message_reader = None
    elif message_reader_spec == "user/file":
        message_reader = ExtTempFileMessageReader()
    elif message_reader_spec == "user/s3":
        message_reader = ExtS3MessageReader(
            bucket=_S3_TEST_BUCKET, client=s3_client, interval=0.001
        )
    else:
        assert False, "Unreachable"

    @asset
    def foo(context: AssetExecutionContext, ext: ExtSubprocess):
        extras = {"bar": "baz"}
        cmd = [_PYTHON_EXECUTABLE, external_script]
        ext.run(
            cmd,
            context=context,
            extras=extras,
            env={
                "CONTEXT_INJECTOR_SPEC": context_injector_spec,
                "MESSAGE_READER_SPEC": message_reader_spec,
            },
        )

    resource = ExtSubprocess(context_injector=context_injector, message_reader=message_reader)

    with instance_for_test() as instance:
        materialize(
            [foo],
            instance=instance,
            resources={"ext": resource},
        )
        mat = instance.get_latest_materialization_event(foo.key)
        assert mat and mat.asset_materialization
        assert isinstance(mat.asset_materialization.metadata["bar"], MarkdownMetadataValue)
        assert mat.asset_materialization.metadata["bar"].value == "baz"
        assert mat.asset_materialization.tags
        assert mat.asset_materialization.tags[DATA_VERSION_TAG] == "alpha"
        assert mat.asset_materialization.tags[DATA_VERSION_IS_USER_PROVIDED_TAG]

        captured = capsys.readouterr()
        assert re.search(r"dagster - INFO - [^\n]+ - hello world\n", captured.err, re.MULTILINE)


def test_ext_typed_metadata():
    def script_fn():
        from dagster_ext import init_dagster_ext

        context = init_dagster_ext()
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
    def foo(context: AssetExecutionContext, ext: ExtSubprocess):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            ext.run(cmd, context=context)

    with instance_for_test() as instance:
        materialize(
            [foo],
            instance=instance,
            resources={"ext": ExtSubprocess()},
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


def test_ext_asset_failed():
    def script_fn():
        raise Exception("foo")

    @asset
    def foo(context: AssetExecutionContext, ext: ExtSubprocess):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            ext.run(cmd, context=context)

    with pytest.raises(DagsterExternalExecutionError):
        materialize([foo], resources={"ext": ExtSubprocess()})


def test_ext_asset_invocation():
    def script_fn():
        from dagster_ext import init_dagster_ext

        context = init_dagster_ext()
        context.log("hello world")

    @asset
    def foo(context: AssetExecutionContext, ext: ExtSubprocess):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            ext.run(cmd, context=context)

    foo(context=build_asset_context(), ext=ExtSubprocess())


PATH_WITH_NONEXISTENT_DIR = "/tmp/does-not-exist/foo"


def test_ext_no_orchestration():
    def script_fn():
        from dagster_ext import (
            ExtContext,
            init_dagster_ext,
            is_dagster_ext_process,
        )

        assert not is_dagster_ext_process()

        init_dagster_ext()
        context = ExtContext.get()
        context.log("hello world")
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


def test_ext_no_client(external_script):
    @asset
    def subproc_run(context: AssetExecutionContext):
        extras = {"bar": "baz"}
        cmd = [_PYTHON_EXECUTABLE, external_script]

        with ext_protocol(
            context,
            ExtTempFileContextInjector(),
            ExtTempFileMessageReader(),
            extras=extras,
        ) as ext_context:
            subprocess.run(cmd, env=ext_context.get_external_process_env_vars(), check=False)

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
