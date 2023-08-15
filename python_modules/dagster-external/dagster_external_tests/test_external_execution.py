import inspect
import os
import re
import textwrap
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Iterator, Mapping

import pytest
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


@contextmanager
def temp_script(script_fn: Callable[[], Any]) -> Iterator[str]:
    # drop the signature line
    source = textwrap.dedent(inspect.getsource(script_fn).split("\n", 1)[1])
    with NamedTemporaryFile() as file:
        file.write(source.encode())
        file.flush()
        yield file.name


@pytest.mark.parametrize(
    ["input_mode", "output_mode"],
    [
        ("stdio", "stdio"),
        ("stdio", "temp_fifo"),
        ("stdio", "fifo"),
        ("stdio", "temp_file"),
        ("temp_file", "stdio"),
        ("temp_file", "temp_fifo"),
        ("temp_file", "fifo"),
        ("temp_file", "temp_file"),
        ("temp_fifo", "stdio"),
        ("temp_fifo", "temp_fifo"),
        ("temp_fifo", "fifo"),
        ("temp_fifo", "temp_file"),
        ("fifo", "stdio"),
        ("fifo", "temp_fifo"),
        ("fifo", "fifo"),
        ("fifo", "temp_file"),
    ],
)
def test_external_execution_asset(input_mode: str, output_mode: str, tmpdir, capsys):
    if input_mode == "fifo":
        input_fifo = str(tmpdir.join("input"))
        os.mkfifo(input_fifo)
    else:
        input_fifo = None

    if output_mode == "fifo":
        output_fifo = str(tmpdir.join("output"))
        os.mkfifo(output_fifo)
    else:
        output_fifo = None

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
        "input_fifo": input_fifo,
        "output_fifo": output_fifo,
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
