import inspect
import os
import textwrap
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Iterator, Mapping

import pytest
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
        ("temp_fifo", "stdio"),
        ("temp_fifo", "temp_fifo"),
        ("temp_fifo", "fifo"),
        ("fifo", "stdio"),
        ("fifo", "temp_fifo"),
        ("fifo", "fifo"),
    ],
)
def test_external_execution_asset(input_mode: str, output_mode: str, tmpdir):
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
        context.report_asset_metadata("foo", context.userdata["foo"])

    @asset
    def foo(context: AssetExecutionContext, ext: ExternalExecutionResource):
        userdata = {"foo": "bar"}
        with temp_script(script_fn) as script_path:
            cmd = ["python", script_path]
            ext.run(cmd, context, userdata)

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
        assert mat.asset_materialization.metadata["foo"].value == "bar"
