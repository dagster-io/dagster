import inspect
import re
import textwrap
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Iterator, Mapping, Optional

import pytest
from dagster._check import CheckError
from dagster._core.definitions.data_version import (
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
)
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.materialize import materialize
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
        ("file/auto", "stdio"),
        ("file/auto", "file/auto"),
        ("file/auto", "file/user"),
        ("file/auto", "fifo/auto"),
        ("file/auto", "fifo/user"),
        ("file/user", "stdio"),
        ("file/user", "file/auto"),
        ("file/user", "file/user"),
        ("file/user", "fifo/auto"),
        ("file/user", "fifo/user"),
        ("fifo/auto", "stdio"),
        ("fifo/auto", "file/auto"),
        ("fifo/auto", "file/user"),
        ("fifo/auto", "fifo/auto"),
        ("fifo/auto", "fifo/user"),
        ("fifo/user", "stdio"),
        ("fifo/user", "file/auto"),
        ("fifo/user", "file/user"),
        ("fifo/user", "fifo/auto"),
        ("fifo/user", "fifo/user"),
    ],
)
def test_external_execution_asset(input_spec: str, output_spec: str, tmpdir, capsys):
    if input_spec == "stdio":
        input_mode = ExternalExecutionIOMode.stdio
        input_path = None
    else:
        input_mode_spec, input_path_spec = input_spec.split("/")
        input_mode = ExternalExecutionIOMode(input_mode_spec)
        if input_path_spec == "auto":
            input_path = None
        else:
            input_path = str(tmpdir.join("input"))

    if output_spec == "stdio":
        output_mode = ExternalExecutionIOMode.stdio
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

    resource_kwargs: Mapping[str, Any] = {
        "input_mode": input_mode,
        "output_mode": output_mode,
        "input_path": input_path,
        "output_path": output_path,
    }
    with instance_for_test() as instance:
        materialize(
            [foo],
            instance=instance,
            resources={"ext": ExternalExecutionResource(**resource_kwargs)},
        )
        mat = instance.get_latest_materialization_event(foo.key)
        assert mat and mat.asset_materialization
        assert mat.asset_materialization.metadata["bar"].value == "baz"
        assert mat.asset_materialization.tags
        assert mat.asset_materialization.tags[DATA_VERSION_TAG] == "alpha"
        assert mat.asset_materialization.tags[DATA_VERSION_IS_USER_PROVIDED_TAG]

        captured = capsys.readouterr()
        assert re.search(r"dagster - INFO - [^\n]+ - hello world\n", captured.err, re.MULTILINE)


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
