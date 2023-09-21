import asyncio
import os
import re
import time
import warnings
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
from signal import Signals
from threading import Event
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Dict,
    Iterator,
    Mapping,
    NamedTuple,
    NoReturn,
    Optional,
    Sequence,
    TypeVar,
    Union,
    cast,
)

import pendulum
from typing_extensions import Self

from dagster import (
    Permissive,
    Shape,
    _check as check,
    fs_io_manager,
)
from dagster._config import Array, Field
from dagster._core.definitions.decorators import op
from dagster._core.definitions.decorators.graph_decorator import graph
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.events import DagsterEvent
from dagster._core.host_representation.origin import (
    ExternalJobOrigin,
    InProcessCodeLocationOrigin,
)
from dagster._core.instance import DagsterInstance
from dagster._core.launcher import RunLauncher
from dagster._core.run_coordinator import RunCoordinator, SubmitRunContext
from dagster._core.secrets import SecretsLoader
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceProcessContext, WorkspaceRequestContext
from dagster._core.workspace.load_target import WorkspaceLoadTarget
from dagster._serdes import ConfigurableClass
from dagster._serdes.config_class import ConfigurableClassData
from dagster._seven.compat.pendulum import create_pendulum_time
from dagster._utils import Counter, get_terminate_signal, traced, traced_counter
from dagster._utils.log import configure_loggers

# test utils from separate light weight file since are exported top level
from .instance_for_test import (
    cleanup_test_instance as cleanup_test_instance,
    environ as environ,
    instance_for_test as instance_for_test,
)

if TYPE_CHECKING:
    from pendulum.datetime import DateTime

T = TypeVar("T")
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


def step_output_event_filter(pipe_iterator: Iterator[DagsterEvent]):
    for step_event in pipe_iterator:
        if step_event.is_successful_output:
            yield step_event


def nesting_graph(depth: int, num_children: int, name: Optional[str] = None) -> GraphDefinition:
    """Creates a job of nested graphs up to "depth" layers, with a fan-out of
    num_children at each layer.

    Total number of ops will be num_children ^ depth
    """

    @op
    def leaf_node(_):
        return 1

    def create_wrap(inner: NodeDefinition, name: str) -> GraphDefinition:
        @graph(name=name)
        def wrap():
            for i in range(num_children):
                op_alias = "%s_node_%d" % (name, i)
                inner.alias(op_alias)()

        return wrap

    @graph(name=name)
    def nested_graph():
        graph_def = create_wrap(leaf_node, "layer_%d" % depth)

        for i in range(depth):
            graph_def = create_wrap(graph_def, "layer_%d" % (depth - (i + 1)))

        graph_def.alias("outer")()

    return nested_graph


TEST_JOB_NAME = "_test_job_"


def create_run_for_test(
    instance: DagsterInstance,
    job_name: str = TEST_JOB_NAME,
    run_id=None,
    run_config=None,
    resolved_op_selection=None,
    step_keys_to_execute=None,
    status=None,
    tags=None,
    root_run_id=None,
    parent_run_id=None,
    job_snapshot=None,
    execution_plan_snapshot=None,
    parent_job_snapshot=None,
    external_job_origin=None,
    job_code_origin=None,
    asset_selection=None,
    asset_check_selection=None,
    op_selection=None,
):
    return instance.create_run(
        job_name=job_name,
        run_id=run_id,
        run_config=run_config,
        resolved_op_selection=resolved_op_selection,
        step_keys_to_execute=step_keys_to_execute,
        status=status,
        tags=tags,
        root_run_id=root_run_id,
        parent_run_id=parent_run_id,
        job_snapshot=job_snapshot,
        execution_plan_snapshot=execution_plan_snapshot,
        parent_job_snapshot=parent_job_snapshot,
        external_job_origin=external_job_origin,
        job_code_origin=job_code_origin,
        asset_selection=asset_selection,
        asset_check_selection=asset_check_selection,
        op_selection=op_selection,
    )


def register_managed_run_for_test(
    instance,
    job_name=TEST_JOB_NAME,
    run_id=None,
    run_config=None,
    resolved_op_selection=None,
    step_keys_to_execute=None,
    tags=None,
    root_run_id=None,
    parent_run_id=None,
    job_snapshot=None,
    execution_plan_snapshot=None,
    parent_job_snapshot=None,
):
    return instance.register_managed_run(
        job_name,
        run_id,
        run_config,
        resolved_op_selection,
        step_keys_to_execute,
        tags,
        root_run_id,
        parent_run_id,
        job_snapshot,
        execution_plan_snapshot,
        parent_job_snapshot,
    )


def wait_for_runs_to_finish(
    instance: DagsterInstance, timeout: float = 20, run_tags: Optional[Mapping[str, str]] = None
) -> None:
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


def poll_for_finished_run(
    instance: DagsterInstance,
    run_id: Optional[str] = None,
    timeout: float = 20,
    run_tags: Optional[Mapping[str, str]] = None,
) -> DagsterRun:
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


def poll_for_step_start(instance: DagsterInstance, run_id: str, timeout: float = 30):
    poll_for_event(instance, run_id, event_type="STEP_START", message=None, timeout=timeout)


def poll_for_event(
    instance: DagsterInstance,
    run_id: str,
    event_type: str,
    message: Optional[str],
    timeout: float = 30,
) -> None:
    total_time = 0
    backoff = 0.01

    while True:
        time.sleep(backoff)
        logs = instance.all_logs(run_id)
        matching_events = [
            log_record.get_dagster_event()
            for log_record in logs
            if log_record.is_dagster_event
            and log_record.get_dagster_event().event_type_value == event_type
        ]
        if matching_events:
            if message is None:
                return
            for matching_message in (event.message for event in matching_events):
                if matching_message and message in matching_message:
                    return

        total_time += backoff
        backoff = backoff * 2
        if total_time > timeout:
            raise Exception("Timed out")


@contextmanager
def new_cwd(path: str) -> Iterator[None]:
    old = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old)


def today_at_midnight(timezone_name="UTC") -> "DateTime":
    check.str_param(timezone_name, "timezone_name")
    now = pendulum.now(timezone_name)
    return create_pendulum_time(now.year, now.month, now.day, tz=now.timezone.name)


from dagster._core.storage.runs import SqliteRunStorage


class ExplodeOnInitRunStorage(SqliteRunStorage):
    def __init__(self, inst_data: Optional[ConfigurableClassData] = None):
        raise NotImplementedError("Init was called")

    @classmethod
    def from_config_value(
        cls, inst_data: Optional[ConfigurableClassData], config_value
    ) -> "SqliteRunStorage":
        raise NotImplementedError("from_config_value was called")


class ExplodingRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data: Optional[ConfigurableClassData] = None):
        self._inst_data = inst_data

        super().__init__()

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls) -> Mapping[str, Any]:
        return {}

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return ExplodingRunLauncher(inst_data=inst_data)

    def launch_run(self, context) -> NoReturn:
        raise NotImplementedError("The entire purpose of this is to throw on launch")

    def join(self, timeout: float = 30) -> None:
        """Nothing to join on since all executions are synchronous."""

    def terminate(self, run_id):
        check.not_implemented("Termination not supported")


class MockedRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(
        self,
        inst_data: Optional[ConfigurableClassData] = None,
        bad_run_ids=None,
        bad_user_code_run_ids=None,
    ):
        self._inst_data = inst_data
        self._queue = []
        self._launched_run_ids = set()
        self.bad_run_ids = bad_run_ids or set()
        self.bad_user_code_run_ids = bad_user_code_run_ids or set()

        super().__init__()

    def launch_run(self, context):
        run = context.dagster_run
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
    def __init__(self, inst_data: Optional[ConfigurableClassData] = None):
        self._inst_data = inst_data
        self._queue = []

        super().__init__()

    def submit_run(self, context: SubmitRunContext):
        dagster_run = context.dagster_run
        check.inst(dagster_run.external_job_origin, ExternalJobOrigin)
        self._queue.append(dagster_run)
        return dagster_run

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
    def __init__(self, inst_data: Optional[ConfigurableClassData], env_vars: Dict[str, str]):
        self._inst_data = inst_data
        self.env_vars = env_vars

    def get_secrets_for_environment(self, location_name: str) -> Dict[str, str]:
        return self.env_vars.copy()

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls) -> Mapping[str, Any]:
        return {"env_vars": Field(Permissive())}

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return TestSecretsLoader(inst_data=inst_data, **config_value)


def get_crash_signals() -> Sequence[Signals]:
    return [get_terminate_signal()]


_mocked_system_timezone: Dict[str, Optional[str]] = {"timezone": None}


# Test utility for creating a test workspace for a function
class InProcessTestWorkspaceLoadTarget(WorkspaceLoadTarget):
    def __init__(
        self, origin: Union[InProcessCodeLocationOrigin, Sequence[InProcessCodeLocationOrigin]]
    ):
        self._origins = cast(
            Sequence[InProcessCodeLocationOrigin],
            origin if isinstance(origin, list) else [origin],
        )

    def create_origins(self) -> Sequence[InProcessCodeLocationOrigin]:
        return self._origins


@contextmanager
def in_process_test_workspace(
    instance: DagsterInstance,
    loadable_target_origin: LoadableTargetOrigin,
    container_image: Optional[str] = None,
) -> Iterator[WorkspaceRequestContext]:
    with WorkspaceProcessContext(
        instance,
        InProcessTestWorkspaceLoadTarget(
            InProcessCodeLocationOrigin(
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
) -> Iterator[WorkspaceProcessContext]:
    """Creates a DynamicWorkspace suitable for passing into a DagsterDaemon loop when running tests."""
    from dagster._daemon.controller import create_daemon_grpc_server_registry

    configure_loggers()
    with create_daemon_grpc_server_registry(instance) as grpc_server_registry:
        with WorkspaceProcessContext(
            instance,
            workspace_load_target,
            grpc_server_registry=grpc_server_registry,
        ) as workspace_process_context:
            yield workspace_process_context


def remove_none_recursively(obj: T) -> T:
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


default_resources_for_test = {"io_manager": fs_io_manager}


def strip_ansi(input_str: str) -> str:
    ansi_escape = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")
    return ansi_escape.sub("", input_str)


def get_logger_output_from_capfd(capfd: Any, logger_name: str) -> str:
    return "\n".join(
        [
            line
            for line in strip_ansi(capfd.readouterr().out.replace("\r\n", "\n")).split("\n")
            if logger_name in line
        ]
    )


def _step_events(instance: DagsterInstance, run: DagsterRun) -> Mapping[str, AbstractSet[str]]:
    events_by_step = defaultdict(set)
    logs = instance.all_logs(run.run_id)
    for record in logs:
        if not record.is_dagster_event or not record.step_key:
            continue
        events_by_step[record.step_key].add(record.get_dagster_event().event_type_value)
    return events_by_step


def step_did_not_run(instance: DagsterInstance, run: DagsterRun, step_name: str) -> bool:
    step_events = _step_events(instance, run)[step_name]
    return len(step_events) == 0


def step_succeeded(instance: DagsterInstance, run: DagsterRun, step_name: str) -> bool:
    step_events = _step_events(instance, run)[step_name]
    return "STEP_SUCCESS" in step_events


def step_failed(instance: DagsterInstance, run: DagsterRun, step_name: str) -> bool:
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
    asyncio.run(run())
    counter = traced_counter.get()
    assert isinstance(counter, Counter)
    counts = counter.counts()
    assert counts["foo"] == 20
    assert counts["bar"] == 10


def wait_for_futures(futures: Dict[str, Future], timeout: Optional[float] = None):
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
    """Utility class for testing threadpool executor logic which executes functions in a single
    thread, for easier unit testing.
    """

    def __init__(self):
        super().__init__(max_workers=1, thread_name_prefix="single_threaded_worker")


class SynchronousThreadPoolExecutor:
    """Utility class for testing threadpool executor logic which executes functions synchronously for
    easier unit testing.
    """

    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

    def submit(self, fn, *args, **kwargs):
        future = Future()
        future.set_result(fn(*args, **kwargs))
        return future

    def shutdown(self, wait=True):
        pass


class BlockingThreadPoolExecutor(ThreadPoolExecutor):
    """Utility class for testing thread timing by allowing for manual unblocking of the submitted threaded work."""

    def __init__(self) -> None:
        self._proceed = Event()
        super().__init__()

    def submit(self, fn, *args, **kwargs):
        def _blocked_fn():
            proceed = self._proceed.wait(60)
            assert proceed
            return fn(*args, **kwargs)

        return super().submit(_blocked_fn)

    def allow(self):
        self._proceed.set()

    def block(self):
        self._proceed.clear()


def ignore_warning(message_substr: str):
    """Ignores warnings within the decorated function that contain the given string."""

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            warnings.filterwarnings("ignore", message=message_substr)
            return func(*args, **kwargs)

        return wrapper

    return decorator
