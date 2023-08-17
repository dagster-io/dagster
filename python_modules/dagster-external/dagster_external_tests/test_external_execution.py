import inspect
import re
import textwrap
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Iterator, Optional

import pytest
from dagster._check import CheckError
from dagster._core.definitions.data_version import (
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
)
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.materialize import materialize
from dagster._core.errors import DagsterExternalExecutionError
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.external_execution.resource import (
    ExternalExecutionResource,
)
from dagster._core.instance_for_test import instance_for_test
from dagster_external.protocol import ExternalExecutionIOMode


@contextmanager
def temp_script(script_fn: Callable[[], Any]) -> Iterator[str]:
    # drop the signature line
    source = textwrap.dedent(inspect.getsource(script_fn).split("\n", 1)[1])
    with NamedTemporaryFile() as file:
        file.write(source.encode())
        file.flush()
        yield file.name


@pytest.mark.parametrize(
    ["input_spec", "output_spec"],
    [
        ("stdio", "stdio"),
        ("stdio", "file/auto"),
        ("stdio", "file/user"),
        ("stdio", "fifo/auto"),
        ("stdio", "fifo/user"),
        ("stdio", "socket"),
        ("file/auto", "stdio"),
        ("file/auto", "file/auto"),
        ("file/auto", "file/user"),
        ("file/auto", "fifo/auto"),
        ("file/auto", "fifo/user"),
        ("file/auto", "socket"),
        ("file/user", "stdio"),
        ("file/user", "file/auto"),
        ("file/user", "file/user"),
        ("file/user", "fifo/auto"),
        ("file/user", "fifo/user"),
        ("file/user", "socket"),
        ("fifo/auto", "stdio"),
        ("fifo/auto", "file/auto"),
        ("fifo/auto", "file/user"),
        ("fifo/auto", "fifo/auto"),
        ("fifo/auto", "fifo/user"),
        ("fifo/auto", "socket"),
        ("fifo/user", "stdio"),
        ("fifo/user", "file/auto"),
        ("fifo/user", "file/user"),
        ("fifo/user", "fifo/auto"),
        ("fifo/user", "fifo/user"),
        ("fifo/user", "socket"),
        ("socket", "stdio"),
        ("socket", "file/auto"),
        ("socket", "file/user"),
        ("socket", "fifo/auto"),
        ("socket", "fifo/user"),
        ("socket", "socket"),
    ],
)
def test_external_execution_asset(input_spec: str, output_spec: str, tmpdir, capsys):
    if input_spec in ["stdio", "socket"]:
        input_mode = ExternalExecutionIOMode(input_spec)
        input_path = None
    else:
        input_mode_spec, input_path_spec = input_spec.split("/")
        input_mode = ExternalExecutionIOMode(input_mode_spec)
        if input_path_spec == "auto":
            input_path = None
        else:
            input_path = str(tmpdir.join("input"))

    if output_spec in ["stdio", "socket"]:
        output_mode = ExternalExecutionIOMode(output_spec)
        output_path = None
    else:
        output_mode_spec, output_path_spec = output_spec.split("/")
        output_mode = ExternalExecutionIOMode(output_mode_spec)
        if output_path_spec == "auto":
            output_path = None
        else:
            output_path = str(tmpdir.join("output"))

    def script_fn():
        from dagster_external import ExternalExecutionContext, init_dagster_external

        init_dagster_external()
        context = ExternalExecutionContext.get()
        context.log("hello world")
        context.report_asset_metadata("foo", "bar", context.get_extra("bar"))
        context.report_asset_data_version("foo", "alpha")

    @asset
    def foo(context: AssetExecutionContext, ext: ExternalExecutionResource):
        extras = {"bar": "baz"}
        with temp_script(script_fn) as script_path:
            cmd = ["python", script_path]
            ext.run(cmd, context, extras)

    resource = ExternalExecutionResource(
        input_mode=input_mode,
        output_mode=output_mode,
        input_path=input_path,
        output_path=output_path,
    )
    with instance_for_test() as instance:
        materialize(
            [foo],
            instance=instance,
            resources={"ext": resource},
        )
        mat = instance.get_latest_materialization_event(foo.key)
        assert mat and mat.asset_materialization
        assert mat.asset_materialization.metadata["bar"].value == "baz"
        assert mat.asset_materialization.tags
        assert mat.asset_materialization.tags[DATA_VERSION_TAG] == "alpha"
        assert mat.asset_materialization.tags[DATA_VERSION_IS_USER_PROVIDED_TAG]

        captured = capsys.readouterr()
        assert re.search(r"dagster - INFO - [^\n]+ - hello world\n", captured.err, re.MULTILINE)


def test_external_execution_asset_failed():
    def script_fn():
        raise Exception("foo")

    @asset
    def foo(context: AssetExecutionContext, ext: ExternalExecutionResource):
        with temp_script(script_fn) as script_path:
            cmd = ["python", script_path]
            ext.run(cmd, context)

    resource = ExternalExecutionResource(
        input_mode=ExternalExecutionIOMode.stdio,
    )
    with pytest.raises(DagsterExternalExecutionError):
        materialize([foo], resources={"ext": resource})


PATH_WITH_NONEXISTENT_DIR = "/tmp/does-not-exist/foo"


@pytest.mark.parametrize(
    ["input_mode_name", "input_path", "output_mode_name", "output_path"],
    [
        ("file", PATH_WITH_NONEXISTENT_DIR, "stdio", None),
        ("fifo", PATH_WITH_NONEXISTENT_DIR, "stdio", None),
        ("stdio", None, "file", PATH_WITH_NONEXISTENT_DIR),
        ("stdio", None, "fifo", PATH_WITH_NONEXISTENT_DIR),
    ],
)
def test_external_execution_invalid_path(
    input_mode_name: str,
    input_path: Optional[str],
    output_mode_name: str,
    output_path: Optional[str],
):
    def script_fn():
        pass

    @asset
    def foo(context: AssetExecutionContext, ext: ExternalExecutionResource):
        with temp_script(script_fn) as script_path:
            cmd = ["python", script_path]
            ext.run(cmd, context)

    resource = ExternalExecutionResource(
        input_mode=ExternalExecutionIOMode(input_mode_name),
        input_path=input_path,
        output_mode=ExternalExecutionIOMode(output_mode_name),
        output_path=output_path,
    )
    with pytest.raises(CheckError, match=r"directory \S+ does not currently exist"):
        materialize([foo], resources={"ext": resource})
