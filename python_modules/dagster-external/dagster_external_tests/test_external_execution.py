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


def python_api_script_fn():
    from dagster_external import ExternalExecutionContext, init_dagster_external

    init_dagster_external()
    context = ExternalExecutionContext.get()
    context.log("hello world")
    context.report_asset_metadata("foo", "bar", context.get_extra("bar"))
    context.report_asset_data_version("foo", "alpha")


def cli_script_fn():
    import json
    import subprocess

    # Call it just to make sure it works
    context_proc = subprocess.run(
        ["dagster-external", "get-context"], capture_output=True, encoding="utf8"
    )
    context = json.loads(context_proc.stdout)

    extra_proc = subprocess.run(
        ["dagster-external", "get-extra", "--key=bar"], capture_output=True, encoding="utf8"
    )
    bar_extra = json.loads(extra_proc.stdout)
    assert bar_extra == context["extras"]["bar"]

    context_proc = subprocess.run(
        ["dagster-external", "log", "--message=hello world"],
    )
    subprocess.run(
        [
            "dagster-external",
            "report-asset-metadata",
            "--asset-key=foo",
            "--label=bar",
            # f"--value={extras['bar']}",
            f"--value={bar_extra}",
        ]
    )
    subprocess.run(
        ["dagster-external", "report-asset-data-version", "--asset-key=foo", "--data-version=alpha"]
    )


@pytest.mark.parametrize(
    ["script_fn", "input_spec", "output_spec"],
    [
        (python_api_script_fn, "stdio", "stdio"),
        (python_api_script_fn, "stdio", "file/auto"),
        (python_api_script_fn, "stdio", "file/user"),
        (python_api_script_fn, "stdio", "fifo/auto"),
        (python_api_script_fn, "stdio", "fifo/user"),
        (python_api_script_fn, "stdio", "socket"),
        (python_api_script_fn, "file/auto", "stdio"),
        (python_api_script_fn, "file/auto", "file/auto"),
        (python_api_script_fn, "file/auto", "file/user"),
        (python_api_script_fn, "file/auto", "fifo/auto"),
        (python_api_script_fn, "file/auto", "fifo/user"),
        (python_api_script_fn, "file/auto", "socket"),
        (python_api_script_fn, "file/user", "stdio"),
        (python_api_script_fn, "file/user", "file/auto"),
        (python_api_script_fn, "file/user", "file/user"),
        (python_api_script_fn, "file/user", "fifo/auto"),
        (python_api_script_fn, "file/user", "fifo/user"),
        (python_api_script_fn, "file/user", "socket"),
        (python_api_script_fn, "fifo/auto", "stdio"),
        (python_api_script_fn, "fifo/auto", "file/auto"),
        (python_api_script_fn, "fifo/auto", "file/user"),
        (python_api_script_fn, "fifo/auto", "fifo/auto"),
        (python_api_script_fn, "fifo/auto", "fifo/user"),
        (python_api_script_fn, "fifo/auto", "socket"),
        (python_api_script_fn, "fifo/user", "stdio"),
        (python_api_script_fn, "fifo/user", "file/auto"),
        (python_api_script_fn, "fifo/user", "file/user"),
        (python_api_script_fn, "fifo/user", "fifo/auto"),
        (python_api_script_fn, "fifo/user", "fifo/user"),
        (python_api_script_fn, "fifo/user", "socket"),
        (python_api_script_fn, "socket", "stdio"),
        (python_api_script_fn, "socket", "file/auto"),
        (python_api_script_fn, "socket", "file/user"),
        (python_api_script_fn, "socket", "fifo/auto"),
        (python_api_script_fn, "socket", "fifo/user"),
        (python_api_script_fn, "socket", "socket"),
        (cli_script_fn, "file/auto", "stdio"),
        (cli_script_fn, "file/auto", "file/auto"),
        (cli_script_fn, "file/auto", "file/user"),
        (cli_script_fn, "file/auto", "fifo/auto"),
        (cli_script_fn, "file/auto", "fifo/user"),
        (cli_script_fn, "file/auto", "socket"),
        (cli_script_fn, "file/user", "stdio"),
        (cli_script_fn, "file/user", "file/auto"),
        (cli_script_fn, "file/user", "file/user"),
        (cli_script_fn, "file/user", "fifo/auto"),
        (cli_script_fn, "file/user", "fifo/user"),
        (cli_script_fn, "file/user", "socket"),
        (cli_script_fn, "socket", "stdio"),
        (cli_script_fn, "socket", "file/auto"),
        (cli_script_fn, "socket", "file/user"),
        (cli_script_fn, "socket", "fifo/auto"),
        (cli_script_fn, "socket", "fifo/user"),
    ],
)
def test_external_execution_asset(
    script_fn: Callable[[], None], input_spec: str, output_spec: str, tmpdir, capsys
):
    if input_spec in ["stdio", "socket"]:
        input_mode = ExternalExecutionIOMode.stdio
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


def test_invalid_cli_invocation():
    def script_fn():
        import subprocess

        subprocess.run(
            ["dagster-external", "log", "--message=hello world"],
            check=True,
        )

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
