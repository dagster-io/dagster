import inspect
import re
import subprocess
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
from dagster._core.execution.context.invocation import build_asset_context
from dagster._core.external_execution.subprocess import (
    SubprocessExecutionResource,
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
    ["input_file_spec", "output_file_spec"],
    [
        ("auto", "auto"),
        ("auto", "user"),
        ("user", "auto"),
        ("user", "user"),
    ],
)
def test_external_subprocess_asset(input_file_spec: str, output_file_spec: str, tmpdir, capsys):
    input_path = None if input_file_spec == "auto" else str(tmpdir.join("input"))
    output_path = None if output_file_spec == "auto" else str(tmpdir.join("output"))

    def script_fn():
        from dagster_external import ExternalExecutionContext, init_dagster_external

        init_dagster_external()
        context = ExternalExecutionContext.get()
        context.log("hello world")
        context.report_asset_metadata("foo", "bar", context.get_extra("bar"))
        context.report_asset_data_version("foo", "alpha")

    @asset
    def foo(context: AssetExecutionContext, ext: SubprocessExecutionResource):
        extras = {"bar": "baz"}
        with temp_script(script_fn) as script_path:
            cmd = ["python", script_path]
            ext.run(cmd, context=context, extras=extras)

    resource = SubprocessExecutionResource(
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
    def foo(context: AssetExecutionContext, ext: SubprocessExecutionResource):
        with temp_script(script_fn) as script_path:
            cmd = ["python", script_path]
            ext.run(cmd, context=context)

    with pytest.raises(DagsterExternalExecutionError):
        materialize([foo], resources={"ext": SubprocessExecutionResource()})


def test_external_execution_asset_invocation():
    def script_fn():
        from dagster_external import init_dagster_external

        context = init_dagster_external()
        context.log("hello world")

    @asset
    def foo(context: AssetExecutionContext, ext: SubprocessExecutionResource):
        with temp_script(script_fn) as script_path:
            cmd = ["python", script_path]
            ext.run(cmd, context=context)

    foo(context=build_asset_context(), ext=SubprocessExecutionResource())


PATH_WITH_NONEXISTENT_DIR = "/tmp/does-not-exist/foo"


@pytest.mark.parametrize(
    ["input_path", "output_path"],
    [
        (PATH_WITH_NONEXISTENT_DIR, None),
        (None, PATH_WITH_NONEXISTENT_DIR),
    ],
)
def test_external_execution_invalid_path(
    input_path: Optional[str],
    output_path: Optional[str],
):
    def script_fn():
        pass

    @asset
    def foo(context: AssetExecutionContext, ext: SubprocessExecutionResource):
        with temp_script(script_fn) as script_path:
            cmd = ["python", script_path]
            ext.run(cmd, context=context)

    resource = SubprocessExecutionResource(
        input_path=input_path,
        output_path=output_path,
    )
    with pytest.raises(CheckError, match=r"directory \S+ does not currently exist"):
        materialize([foo], resources={"ext": resource})


def test_external_execution_no_orchestration():
    def script_fn():
        from dagster_external import (
            ExternalExecutionContext,
            init_dagster_external,
            is_dagster_orchestration_active,
        )

        assert not is_dagster_orchestration_active()

        init_dagster_external()
        context = ExternalExecutionContext.get()
        context.log("hello world")
        context.report_asset_metadata("foo", "bar", context.get_extra("bar"))
        context.report_asset_data_version("foo", "alpha")

    with temp_script(script_fn) as script_path:
        cmd = ["python", script_path]
        _, stderr = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
        assert re.search(
            r"This process was not launched by a Dagster orchestration process. All calls to the"
            r" `dagster-external` context are no-ops.",
            stderr.decode(),
        )
