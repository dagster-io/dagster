import inspect
import os
import re
import shutil
import subprocess
import textwrap
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Iterator

import pytest
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
from dagster._core.external_execution.utils import (
    get_env_context_injector,
    get_file_context_injector,
    get_file_message_reader,
)
from dagster._core.instance_for_test import instance_for_test

_PYTHON_EXECUTABLE = shutil.which("python")


@contextmanager
def temp_script(script_fn: Callable[[], Any]) -> Iterator[str]:
    # drop the signature line
    source = textwrap.dedent(inspect.getsource(script_fn).split("\n", 1)[1])
    with NamedTemporaryFile() as file:
        file.write(source.encode())
        file.flush()
        yield file.name


@pytest.mark.parametrize(
    ("context_injector_spec", "message_reader_spec"),
    [
        ("default", "default"),
        ("default", "user/file"),
        ("user/file", "default"),
        ("user/file", "user/file"),
        ("user/env", "default"),
        ("user/env", "user/file"),
    ],
)
def test_external_subprocess_asset(capsys, tmpdir, context_injector_spec, message_reader_spec):
    if context_injector_spec == "default":
        context_injector = None
    elif context_injector_spec == "user/file":
        context_injector = get_file_context_injector(os.path.join(tmpdir, "input"))
    elif context_injector_spec == "user/env":
        context_injector = get_env_context_injector()
    else:
        assert False, "Unreachable"

    if message_reader_spec == "default":
        message_reader = None
    elif message_reader_spec == "user/file":
        message_reader = get_file_message_reader(os.path.join(tmpdir, "output"))
    else:
        assert False, "Unreachable"

    def script_fn():
        import os

        from dagster_externals import (
            ExternalExecutionContext,
            ExternalExecutionEnvContextLoader,
            init_dagster_externals,
        )

        context_loader = (
            ExternalExecutionEnvContextLoader()
            if os.getenv("CONTEXT_INJECTOR_SPEC") == "user/env"
            else None
        )

        init_dagster_externals(context_loader=context_loader)
        context = ExternalExecutionContext.get()
        context.log("hello world")
        context.report_asset_metadata("foo", "bar", context.get_extra("bar"))
        context.report_asset_data_version("foo", "alpha")

    @asset
    def foo(context: AssetExecutionContext, ext: SubprocessExecutionResource):
        extras = {"bar": "baz"}
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            ext.run(
                cmd,
                context=context,
                extras=extras,
                context_injector=context_injector,
                message_reader=message_reader,
                env={"CONTEXT_INJECTOR_SPEC": context_injector_spec},
            )

    resource = SubprocessExecutionResource()
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
            cmd = [_PYTHON_EXECUTABLE, script_path]
            ext.run(cmd, context=context)

    with pytest.raises(DagsterExternalExecutionError):
        materialize([foo], resources={"ext": SubprocessExecutionResource()})


def test_external_execution_asset_invocation():
    def script_fn():
        from dagster_externals import init_dagster_externals

        context = init_dagster_externals()
        context.log("hello world")

    @asset
    def foo(context: AssetExecutionContext, ext: SubprocessExecutionResource):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            ext.run(cmd, context=context)

    foo(context=build_asset_context(), ext=SubprocessExecutionResource())


PATH_WITH_NONEXISTENT_DIR = "/tmp/does-not-exist/foo"


def test_external_execution_no_orchestration():
    def script_fn():
        from dagster_externals import (
            ExternalExecutionContext,
            init_dagster_externals,
            is_dagster_orchestration_active,
        )

        assert not is_dagster_orchestration_active()

        init_dagster_externals()
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
            r"This process was not launched by a Dagster orchestration process.",
            stderr.decode(),
        )
