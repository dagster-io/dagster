import re
import shutil
import subprocess
import time
from multiprocessing import Process
from tempfile import NamedTemporaryFile
from typing import Iterator

import pytest
from dagster import op
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSpec
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.data_version import (
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
)
from dagster._core.definitions.decorators.asset_decorator import asset, multi_asset
from dagster._core.definitions.decorators.job_decorator import job
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
from dagster._core.instance import DagsterInstance
from dagster._core.instance_for_test import instance_for_test
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster._core.pipes.utils import (
    PipesEnvContextInjector,
    PipesTempFileContextInjector,
    PipesTempFileMessageReader,
    open_pipes_session,
)
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from dagster._utils import process_is_alive
from dagster._utils.env import environ
from dagster._utils.warnings import ExperimentalWarning
from dagster_pipes import DagsterPipesError

from dagster_tests.execution_tests.pipes_tests.utils import temp_script

_PYTHON_EXECUTABLE = shutil.which("python")


@pytest.fixture
def external_script() -> Iterator[str]:
    # This is called in an external process and so cannot access outer scope
    def script_fn():
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

    with temp_script(script_fn) as script_path:
        yield script_path


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
def test_pipes_subprocess(
    capsys, tmpdir, external_script, context_injector_spec, message_reader_spec
):
    if context_injector_spec == "default":
        context_injector = None
    elif context_injector_spec == "user/file":
        context_injector = PipesTempFileContextInjector()
    elif context_injector_spec == "user/env":
        context_injector = PipesEnvContextInjector()
    else:
        assert False, "Unreachable"

    if message_reader_spec == "default":
        message_reader = None
    elif message_reader_spec == "user/file":
        message_reader = PipesTempFileMessageReader()

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
        from dagster_pipes import PipesContext, PipesEnvVarParamsLoader, open_dagster_pipes

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
        materialize(
            [foo],
            instance=instance,
            resources={"pipes_client": PipesSubprocessClient()},
        )
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
            [foo],
            instance=instance,
            resources={"pipes_client": PipesSubprocessClient()},
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


def test_subprocess_env_precedence():
    def script_fn():
        import os

        from dagster_pipes import open_dagster_pipes

        with open_dagster_pipes() as context:
            context.report_asset_materialization(
                metadata={
                    "A": os.getenv("A"),
                    "B": os.getenv("B"),
                    "C": os.getenv("C"),
                },
            )

    @asset
    def env_test(context, pipes_client: PipesSubprocessClient):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            return pipes_client.run(
                env={"C": "callsite"},
                command=cmd,
                context=context,
            ).get_results()

    # callsite overrides client overrides inherited parent env
    with environ({"A": "parent", "B": "parent", "C": "parent"}):
        result = materialize(
            [env_test],
            resources={"pipes_client": PipesSubprocessClient(env={"B": "client", "C": "client"})},
        )
        assert result.success
        mat_evts = result.get_asset_materialization_events()
        assert len(mat_evts) == 1
        assert mat_evts[0].materialization.metadata["A"].value == "parent"
        assert mat_evts[0].materialization.metadata["B"].value == "client"
        assert mat_evts[0].materialization.metadata["C"].value == "callsite"


def test_pipes_exception():
    def script_fn():
        from dagster_pipes import open_dagster_pipes

        with open_dagster_pipes():
            raise Exception("oops")

    @asset
    def raises(context: OpExecutionContext, pipes_client: PipesSubprocessClient):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            return pipes_client.run(command=cmd, context=context).get_results()

    with instance_for_test() as instance:
        result = materialize(
            [raises],
            instance=instance,
            resources={"pipes_client": PipesSubprocessClient()},
            raise_on_error=False,
        )
        assert not result.success
        conn = instance.get_records_for_run(result.run_id)
        pipes_msgs = [
            record.event_log_entry.user_message
            for record in conn.records
            if record.event_log_entry.user_message.startswith("[pipes]")
        ]
        assert len(pipes_msgs) == 2
        assert "successfully opened" in pipes_msgs[0]
        assert "external process pipes closed with exception" in pipes_msgs[1]


def test_run_in_op():
    def script_fn():
        from dagster_pipes import open_dagster_pipes

        with open_dagster_pipes() as pipes:
            pipes.log.info("hello there")

    @op
    def just_run(context: OpExecutionContext, pipes_client: PipesSubprocessClient):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            pipes_client.run(command=cmd, context=context)

    @job
    def sample_job():
        just_run()

    result = sample_job.execute_in_process(
        resources={"pipes_client": PipesSubprocessClient()},
    )
    assert result.success


def test_pipes_expected_materialization():
    def script_fn(): ...

    @asset
    def missing_mat_result(context: OpExecutionContext, pipes_client: PipesSubprocessClient):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            return pipes_client.run(
                command=cmd,
                context=context,
            ).get_materialize_result(implicit_materialization=False)

    with pytest.raises(
        DagsterPipesError,
        match="No materialization results received from external process",
    ):
        materialize(
            [missing_mat_result],
            resources={"pipes_client": PipesSubprocessClient()},
        )

    @asset
    def missing_results(context: OpExecutionContext, pipes_client: PipesSubprocessClient):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            return pipes_client.run(
                command=cmd,
                context=context,
            ).get_results(implicit_materializations=False)

    with pytest.raises(
        DagsterInvariantViolationError,
        # less then ideal error message
        match=r"op 'missing_results' did not yield or return expected outputs {'result'}",
    ):
        materialize(
            [missing_results],
            resources={"pipes_client": PipesSubprocessClient()},
        )


def test_user_messages():
    def script_fn():
        from dagster_pipes import open_dagster_pipes

        with open_dagster_pipes() as pipes:
            pipes.report_custom_message({"some": "junk"})
            pipes.report_custom_message("cool message")
            pipes.report_custom_message(2)

    @asset
    def extra_msg(context: OpExecutionContext, pipes_client: PipesSubprocessClient):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            response = pipes_client.run(command=cmd, context=context)
            messages = response.get_custom_messages()
            assert len(messages) == 3
            assert messages[0]["some"] == "junk"
            assert messages[1] == "cool message"
            assert messages[2] == 2
            return response.get_materialize_result()

    result = materialize(
        [extra_msg],
        resources={"pipes_client": PipesSubprocessClient()},
    )
    assert result.success


def test_bad_user_message():
    def script_fn():
        from dagster_pipes import open_dagster_pipes

        class Cursed: ...

        with open_dagster_pipes() as pipes:
            pipes.report_custom_message(Cursed())

    @asset
    def bad_msg(context: OpExecutionContext, pipes_client: PipesSubprocessClient):
        with temp_script(script_fn) as script_path:
            cmd = [_PYTHON_EXECUTABLE, script_path]
            response = pipes_client.run(command=cmd, context=context)
            return response.get_materialize_result()

    with instance_for_test() as instance:
        result = materialize(
            [bad_msg],
            instance=instance,
            resources={"pipes_client": PipesSubprocessClient()},
            raise_on_error=False,
        )
        assert not result.success
        conn = instance.get_records_for_run(result.run_id)
        pipes_events = [
            record.event_log_entry
            for record in conn.records
            if record.event_log_entry.user_message.startswith("[pipes]")
        ]
        assert len(pipes_events) == 2
        assert "successfully opened" in pipes_events[0].user_message
        assert "external process pipes closed with exception" in pipes_events[1].user_message
        assert pipes_events[1].dagster_event
        assert pipes_events[1].dagster_event.engine_event_data.error
        assert (
            "Object of type Cursed is not JSON serializable"
            in pipes_events[1].dagster_event.engine_event_data.error.message
        )


def _execute_job(spin_timeout, subproc_log_path):
    def script_fn():
        import os
        import time

        from dagster_pipes import open_dagster_pipes

        with open_dagster_pipes() as pipes:
            timeout = pipes.get_extra("timeout")
            log_path = pipes.get_extra("log_path")
            with open(log_path, "w") as f:
                f.write(f"{os.getpid()}")
                f.flush()
                start = time.time()
                while time.time() - start < timeout:
                    ...

    with temp_script(script_fn) as script_path:

        @op
        def stalling_pipes_op(
            context: OpExecutionContext,
        ):
            cmd = [_PYTHON_EXECUTABLE, script_path]
            PipesSubprocessClient().run(
                command=cmd,
                context=context,
                extras={
                    "timeout": spin_timeout,
                    "log_path": subproc_log_path,
                },
            )

        @job
        def pipes_job():
            stalling_pipes_op()

        return pipes_job.execute_in_process(
            instance=DagsterInstance.get(),
            raise_on_error=False,
        )


def test_cancellation():
    spin_timeout = 600
    with instance_for_test(), NamedTemporaryFile() as subproc_log_path:
        p = Process(target=_execute_job, args=(spin_timeout, subproc_log_path.name))
        p.start()
        pid = None
        while p.is_alive():
            data = subproc_log_path.read().decode("utf-8")
            if data:
                pid = int(data)
                time.sleep(0.1)
                p.terminate()
                break

        p.join(timeout=1)
        assert not p.is_alive()
        assert pid
        assert not process_is_alive(pid)


def test_pipes_cli_args_params_loader():
    # let's use non-trivial message/context channels to make sure the CLI args are being used to pass important params

    def script_fn():
        from dagster_pipes import (
            PipesCliArgsParamsLoader,
            PipesDefaultContextLoader,
            PipesDefaultMessageWriter,
            open_dagster_pipes,
        )

        with open_dagster_pipes(
            params_loader=PipesCliArgsParamsLoader(),
            context_loader=PipesDefaultContextLoader(),
            message_writer=PipesDefaultMessageWriter(),
        ) as pipes:
            # this assert will only pass if PipesCliArgsParamsLoader is working correctly
            assert pipes.asset_key == "asset_with_pipes_cli_args_params_loader"

    @asset
    def asset_with_pipes_cli_args_params_loader(
        context: OpExecutionContext, pipes_client: PipesSubprocessClient
    ):
        with (
            temp_script(script_fn) as script_path,
            open_pipes_session(
                context=context,
                context_injector=PipesTempFileContextInjector(),  # this doesn't really matter
                message_reader=PipesTempFileMessageReader(),  # this doesn't really matter
            ) as session,
        ):
            pipes_args = session.get_bootstrap_cli_arguments()

            cmd = [_PYTHON_EXECUTABLE, script_path] + sum(  # noqa: RUF017
                [list(pair) for pair in pipes_args.items()], []
            )

            return pipes_client.run(command=cmd, context=context).get_materialize_result()

    result = materialize(
        [asset_with_pipes_cli_args_params_loader],
        resources={"pipes_client": PipesSubprocessClient()},
    )
    assert result.success


def test_pipes_subprocess_client_no_experimental_warning():
    def script_fn():
        pass

    @asset
    def foo(context: OpExecutionContext, pipes_client: PipesSubprocessClient):
        # print("blah")
        with temp_script(script_fn) as external_script:
            cmd = [_PYTHON_EXECUTABLE, external_script]
            return pipes_client.run(command=cmd, context=context).get_materialize_result()

    with pytest.warns() as record:
        materialize(
            [foo],
            resources={"pipes_client": PipesSubprocessClient()},
        )

    experimental_warnings = [w for w in record if issubclass(w.category, ExperimentalWarning)]

    if experimental_warnings:
        for warning in experimental_warnings:
            assert "Pipes" not in str(warning.message)
