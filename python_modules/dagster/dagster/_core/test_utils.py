import asyncio
import os
import re
import sys
import tempfile
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, contextmanager
from typing import Any, Generator, Mapping, NamedTuple, Optional, Sequence, TypeVar

import pendulum
import yaml

from dagster import (
    Permissive,
    Shape,
    _check as check,
    fs_io_manager,
)
from dagster._config import Array, Field
from dagster._core.definitions.decorators.graph_decorator import graph
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.host_representation.origin import (
    ExternalPipelineOrigin,
    InProcessRepositoryLocationOrigin,
)
from dagster._core.instance import DagsterInstance
from dagster._core.launcher import RunLauncher
from dagster._core.run_coordinator import RunCoordinator, SubmitRunContext
from dagster._core.secrets import SecretsLoader
from dagster._core.storage.pipeline_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import WorkspaceLoadTarget
from dagster._legacy import ModeDefinition, pipeline, solid
from dagster._serdes import ConfigurableClass
from dagster._seven.compat.pendulum import create_pendulum_time, mock_pendulum_timezone
from dagster._utils import Counter, get_terminate_signal, traced, traced_counter
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.log import configure_loggers
from dagster._utils.merger import merge_dicts

T_NamedTuple = TypeVar("T_NamedTuple", bound=NamedTuple)


def assert_namedtuple_lists_equal(
    t1_list: Sequence[T_NamedTuple],
    t2_list: Sequence[T_NamedTuple],
    exclude_fields: Optional[Sequence[str]] = None,
) -> None:
    for t1, t2 in zip(t1_list, t2_list):
        assert_namedtuples_equal(t1, t2, exclude_fields)


def assert_namedtuples_equal(
    t1: T_NamedTuple, t2: T_NamedTuple, exclude_fields: Optional[Sequence[str]] = None
) -> None:
    exclude_fields = exclude_fields or []
    for field in type(t1)._fields:
        if field not in exclude_fields:
            assert getattr(t1, field) == getattr(t2, field)


def step_output_event_filter(pipe_iterator):
    for step_event in pipe_iterator:
        if step_event.is_successful_output:
            yield step_event


def nesting_graph_pipeline(depth, num_children, *args, **kwargs):
    """Creates a pipeline of nested composite solids up to "depth" layers, with a fan-out of
    num_children at each layer.

    Total number of solids will be num_children ^ depth
    """

    @solid
    def leaf_node(_):
        return 1

    def create_wrap(inner, name):
        @graph(name=name)
        def wrap():
            for i in range(num_children):
                solid_alias = "%s_node_%d" % (name, i)
                inner.alias(solid_alias)()

        return wrap

    @pipeline(*args, **kwargs)
    def nested_pipeline():
        comp_solid = create_wrap(leaf_node, "layer_%d" % depth)

        for i in range(depth):
            comp_solid = create_wrap(comp_solid, "layer_%d" % (depth - (i + 1)))

        comp_solid.alias("outer")()

    return nested_pipeline


@contextmanager
def environ(env):
    """Temporarily set environment variables inside the context manager and
    fully restore previous environment afterwards.
    """
    previous_values = {key: os.getenv(key) for key in env}
    for key, value in env.items():
        if value is None:
            if key in os.environ:
                del os.environ[key]
        else:
            os.environ[key] = value
    try:
        yield
    finally:
        for key, value in previous_values.items():
            if value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = value


@contextmanager
def instance_for_test(
    overrides: Optional[Mapping[str, Any]] = None,
    set_dagster_home: bool = True,
    temp_dir: Optional[str] = None,
) -> Generator[DagsterInstance, None, None]:
    """Creates a persistent :py:class:`~dagster.DagsterInstance` available within a context manager.

    When a context manager is opened, if no `temp_dir` parameter is set, a new
    temporary directory will be created for the duration of the context
    manager's opening. If the `set_dagster_home` parameter is set to True
    (True by default), the `$DAGSTER_HOME` environment variable will be
    overridden to be this directory (or the directory passed in by `temp_dir`)
    for the duration of the context manager being open.

    Args:
        overrides (Optional[Mapping[str, Any]]):
            Config to provide to instance (config format follows that typically found in an `instance.yaml` file).
        set_dagster_home (Optional[bool]):
            If set to True, the `$DAGSTER_HOME` environment variable will be
            overridden to be the directory used by this instance for the
            duration that the context manager is open. Upon the context
            manager closing, the `$DAGSTER_HOME` variable will be re-set to the original value. (Defaults to True).
        temp_dir (Optional[str]):
            The directory to use for storing local artifacts produced by the
            instance. If not set, a temporary directory will be created for
            the duration of the context manager being open, and all artifacts
            will be torn down afterward.
    """
    with ExitStack() as stack:
        if not temp_dir:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())

        # If using the default run launcher, wait for any grpc processes that created runs
        # during test disposal to finish, since they might also be using this instance's tempdir
        instance_overrides = merge_dicts(
            {
                "run_launcher": {
                    "class": "DefaultRunLauncher",
                    "module": "dagster._core.launcher.default_run_launcher",
                    "config": {
                        "wait_for_processes": True,
                    },
                },
                "telemetry": {"enabled": False},
            },
            (overrides if overrides else {}),
        )

        if set_dagster_home:
            stack.enter_context(
                environ({"DAGSTER_HOME": temp_dir, "DAGSTER_DISABLE_TELEMETRY": "yes"})
            )

        with open(os.path.join(temp_dir, "dagster.yaml"), "w", encoding="utf8") as fd:
            yaml.dump(instance_overrides, fd, default_flow_style=False)

        with DagsterInstance.from_config(temp_dir) as instance:
            try:
                yield instance
            except:
                sys.stderr.write(
                    "Test raised an exception, attempting to clean up instance:"
                    + serializable_error_info_from_exc_info(sys.exc_info()).to_string()
                    + "\n"
                )
                raise
            finally:
                cleanup_test_instance(instance)


def cleanup_test_instance(instance):
    check.inst_param(instance, "instance", DagsterInstance)
    # To avoid filesystem contention when we close the temporary directory, wait for
    # all runs to reach a terminal state, and close any subprocesses or threads
    # that might be accessing the run history DB.

    # Since launcher is lazy loaded, we don't need to do anyting if it's None
    if instance._run_launcher:  # pylint: disable=protected-access
        instance._run_launcher.join()  # pylint: disable=protected-access


TEST_PIPELINE_NAME = "_test_pipeline_"


def create_run_for_test(
    instance: DagsterInstance,
    pipeline_name=TEST_PIPELINE_NAME,
    run_id=None,
    run_config=None,
    mode=None,
    solids_to_execute=None,
    step_keys_to_execute=None,
    status=None,
    tags=None,
    root_run_id=None,
    parent_run_id=None,
    pipeline_snapshot=None,
    execution_plan_snapshot=None,
    parent_pipeline_snapshot=None,
    external_pipeline_origin=None,
    pipeline_code_origin=None,
):
    return instance.create_run(
        pipeline_name=pipeline_name,
        run_id=run_id,
        run_config=run_config,
        mode=mode,
        solids_to_execute=solids_to_execute,
        step_keys_to_execute=step_keys_to_execute,
        status=status,
        tags=tags,
        root_run_id=root_run_id,
        parent_run_id=parent_run_id,
        pipeline_snapshot=pipeline_snapshot,
        execution_plan_snapshot=execution_plan_snapshot,
        parent_pipeline_snapshot=parent_pipeline_snapshot,
        external_pipeline_origin=external_pipeline_origin,
        pipeline_code_origin=pipeline_code_origin,
        asset_selection=None,
        solid_selection=None,
    )


def register_managed_run_for_test(
    instance,
    pipeline_name=TEST_PIPELINE_NAME,
    run_id=None,
    run_config=None,
    mode=None,
    solids_to_execute=None,
    step_keys_to_execute=None,
    tags=None,
    root_run_id=None,
    parent_run_id=None,
    pipeline_snapshot=None,
    execution_plan_snapshot=None,
    parent_pipeline_snapshot=None,
):
    return instance.register_managed_run(
        pipeline_name,
        run_id,
        run_config,
        mode,
        solids_to_execute,
        step_keys_to_execute,
        tags,
        root_run_id,
        parent_run_id,
        pipeline_snapshot,
        execution_plan_snapshot,
        parent_pipeline_snapshot,
    )


def wait_for_runs_to_finish(instance, timeout=20, run_tags=None):
    total_time = 0
    interval = 0.1

    filters = RunsFilter(tags=run_tags) if run_tags else None

    while True:
        runs = instance.get_runs(filters)
        if all([run.is_finished for run in runs]):
            return

        if total_time > timeout:
            raise Exception("Timed out")

        time.sleep(interval)
        total_time += interval
        interval = interval * 2


def poll_for_finished_run(instance, run_id=None, timeout=20, run_tags=None):
    total_time = 0
    interval = 0.01

    filters = RunsFilter(
        run_ids=[run_id] if run_id else None,
        tags=run_tags,
        statuses=[
            DagsterRunStatus.SUCCESS,
            DagsterRunStatus.FAILURE,
            DagsterRunStatus.CANCELED,
        ],
    )

    while True:
        runs = instance.get_runs(filters, limit=1)
        if runs:
            return runs[0]
        else:
            time.sleep(interval)
            total_time += interval
            if total_time > timeout:
                raise Exception("Timed out")


def poll_for_step_start(instance, run_id, timeout=30):
    poll_for_event(instance, run_id, event_type="STEP_START", message=None, timeout=timeout)


def poll_for_event(instance, run_id, event_type, message, timeout=30):
    total_time = 0
    backoff = 0.01

    while True:
        time.sleep(backoff)
        logs = instance.all_logs(run_id)
        matching_events = [
            log_record.dagster_event
            for log_record in logs
            if log_record.is_dagster_event
            and log_record.dagster_event.event_type_value == event_type
        ]
        if matching_events:
            if message is None:
                return
            for matching_message in (event.message for event in matching_events):
                if message in matching_message:
                    return

        total_time += backoff
        backoff = backoff * 2
        if total_time > timeout:
            raise Exception("Timed out")


@contextmanager
def new_cwd(path):
    old = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old)


def today_at_midnight(timezone_name="UTC"):
    check.str_param(timezone_name, "timezone_name")
    now = pendulum.now(timezone_name)
    return create_pendulum_time(now.year, now.month, now.day, tz=now.timezone.name)


class ExplodingRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data=None):
        self._inst_data = inst_data

        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return ExplodingRunLauncher(inst_data=inst_data)

    def launch_run(self, context):
        raise NotImplementedError("The entire purpose of this is to throw on launch")

    def join(self, timeout=30):
        """Nothing to join on since all executions are synchronous."""

    def terminate(self, run_id):
        check.not_implemented("Termination not supported")


class MockedRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data=None, bad_run_ids=None, bad_user_code_run_ids=None):
        self._inst_data = inst_data
        self._queue = []
        self._launched_run_ids = set()
        self.bad_run_ids = bad_run_ids or set()
        self.bad_user_code_run_ids = bad_user_code_run_ids or set()

        super().__init__()

    def launch_run(self, context):
        run = context.pipeline_run
        check.inst_param(run, "run", DagsterRun)
        check.invariant(run.status == DagsterRunStatus.STARTING)

        if run.run_id in self.bad_run_ids:
            raise Exception(f"Bad run {run.run_id}")

        if run.run_id in self.bad_user_code_run_ids:
            raise DagsterUserCodeUnreachableError(f"User code error launching run {run.run_id}")

        self._queue.append(run)
        self._launched_run_ids.add(run.run_id)
        return run

    def queue(self):
        return self._queue

    def did_run_launch(self, run_id):
        return run_id in self._launched_run_ids

    @classmethod
    def config_type(cls):
        return Shape(
            {
                "bad_run_ids": Field(Array(str), is_required=False),
                "bad_user_code_run_ids": Field(Array(str), is_required=False),
            }
        )

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data, **config_value)

    @property
    def inst_data(self):
        return self._inst_data

    def terminate(self, run_id):
        check.not_implemented("Termintation not supported")


class MockedRunCoordinator(RunCoordinator, ConfigurableClass):
    def __init__(self, inst_data=None):
        self._inst_data = inst_data
        self._queue = []

        super().__init__()

    def submit_run(self, context: SubmitRunContext):
        pipeline_run = context.pipeline_run
        check.inst(pipeline_run.external_pipeline_origin, ExternalPipelineOrigin)
        self._queue.append(pipeline_run)
        return pipeline_run

    def queue(self):
        return self._queue

    @classmethod
    def config_type(cls):
        return Shape({})

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(
            inst_data=inst_data,
        )

    @property
    def inst_data(self):
        return self._inst_data

    def cancel_run(self, run_id):
        check.not_implemented("Cancellation not supported")


class TestSecretsLoader(SecretsLoader, ConfigurableClass):
    def __init__(
        self,
        inst_data,
        env_vars,
    ):
        self._inst_data = inst_data
        self.env_vars = env_vars

    def get_secrets_for_environment(self, location_name):
        return self.env_vars.copy()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {"env_vars": Field(Permissive())}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return TestSecretsLoader(inst_data=inst_data, **config_value)


def get_crash_signals():
    return [get_terminate_signal()]


_mocked_system_timezone = {"timezone": None}


@contextmanager
def mock_system_timezone(override_timezone):
    with mock_pendulum_timezone(override_timezone):
        try:
            _mocked_system_timezone["timezone"] = override_timezone
            yield
        finally:
            _mocked_system_timezone["timezone"] = None


def get_mocked_system_timezone():
    return _mocked_system_timezone["timezone"]


# Test utility for creating a test workspace for a function
class InProcessTestWorkspaceLoadTarget(WorkspaceLoadTarget):
    def __init__(self, origin: InProcessRepositoryLocationOrigin):
        self._origin = origin

    def create_origins(self):
        return [self._origin]


@contextmanager
def in_process_test_workspace(instance, loadable_target_origin, container_image=None):
    with WorkspaceProcessContext(
        instance,
        InProcessTestWorkspaceLoadTarget(
            InProcessRepositoryLocationOrigin(
                loadable_target_origin,
                container_image=container_image,
            ),
        ),
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


@contextmanager
def create_test_daemon_workspace_context(
    workspace_load_target: WorkspaceLoadTarget,
    instance: DagsterInstance,
):
    """Creates a DynamicWorkspace suitable for passing into a DagsterDaemon loop when running tests.
    """
    from dagster._daemon.controller import create_daemon_grpc_server_registry

    configure_loggers()
    with create_daemon_grpc_server_registry(instance) as grpc_server_registry:
        with WorkspaceProcessContext(
            instance,
            workspace_load_target,
            grpc_server_registry=grpc_server_registry,
        ) as workspace_process_context:
            yield workspace_process_context


def remove_none_recursively(obj):
    """Remove none values from a dict. This can be used to support comparing provided config vs.
    config we retrive from kubernetes, which returns all fields, even those which have no value
    configured.
    """
    if isinstance(obj, (list, tuple, set)):
        return type(obj)(remove_none_recursively(x) for x in obj if x is not None)
    elif isinstance(obj, dict):
        return type(obj)(
            (remove_none_recursively(k), remove_none_recursively(v))
            for k, v in obj.items()
            if k is not None and v is not None
        )
    else:
        return obj


default_mode_def_for_test = ModeDefinition(resource_defs={"io_manager": fs_io_manager})  # type: ignore[has-type]


def strip_ansi(input_str):
    ansi_escape = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")
    return ansi_escape.sub("", input_str)


def get_logger_output_from_capfd(capfd, logger_name):
    return "\n".join(
        [
            line
            for line in strip_ansi(capfd.readouterr().out.replace("\r\n", "\n")).split("\n")
            if logger_name in line
        ]
    )


def _step_events(instance, run):
    events_by_step = defaultdict(set)
    logs = instance.all_logs(run.run_id)
    for record in logs:
        if not record.is_dagster_event or not record.step_key:
            continue
        events_by_step[record.step_key] = record.dagster_event.event_type_value
    return events_by_step


def step_did_not_run(instance, run, step_name):
    step_events = _step_events(instance, run)[step_name]
    return len(step_events) == 0


def step_succeeded(instance, run, step_name):
    step_events = _step_events(instance, run)[step_name]
    return "STEP_SUCCESS" in step_events


def step_failed(instance, run, step_name):
    step_events = _step_events(instance, run)[step_name]
    return "STEP_FAILURE" in step_events


def test_counter():
    @traced
    async def foo():
        pass

    @traced
    async def bar():
        pass

    async def call_foo(num):
        await asyncio.gather(*[foo() for _ in range(num)])

    async def call_bar(num):
        await asyncio.gather(*[bar() for _ in range(num)])

    async def run():
        await call_foo(10)
        await call_foo(10)
        await call_bar(10)

    traced_counter.set(Counter())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    counter = traced_counter.get()
    assert isinstance(counter, Counter)
    counts = counter.counts()
    assert counts["foo"] == 20
    assert counts["bar"] == 10


def wait_for_futures(futures, timeout=None):
    start_time = time.time()
    for target_id, future in futures.copy().items():
        if timeout is not None:
            future_timeout = max(0, timeout - (time.time() - start_time))
        else:
            future_timeout = None

        if not future.done():
            future.result(timeout=future_timeout)
            del futures[target_id]


class SingleThreadPoolExecutor(ThreadPoolExecutor):
    """
    Utility class for testing threadpool executor logic which executes functions in a single
    thread, for easier unit testing.
    """

    def __init__(self):
        super().__init__(max_workers=1, thread_name_prefix="sensor_daemon_worker")
