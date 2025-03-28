import asyncio
import datetime
import os
import re
import sys
import time
import unittest.mock
import warnings
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
from functools import update_wrapper
from pathlib import Path
from signal import Signals
from threading import Event
from typing import (  # noqa: UP035
    AbstractSet,
    Any,
    Callable,
    NamedTuple,
    NoReturn,
    Optional,
    TypeVar,
    Union,
)

from typing_extensions import Self

from dagster import (
    Permissive,
    Shape,
    __file__ as dagster_init_py,
    _check as check,
    fs_io_manager,
)
from dagster._config import Array, Field
from dagster._core.definitions.asset_selection import CoercibleToAssetSelection
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators import op
from dagster._core.definitions.decorators.graph_decorator import graph
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.events import DagsterEvent
from dagster._core.instance import DagsterInstance

# test utils from separate light weight file since are exported top level
from dagster._core.instance_for_test import (
    cleanup_test_instance as cleanup_test_instance,
    environ as environ,
    instance_for_test as instance_for_test,
)
from dagster._core.launcher import RunLauncher
from dagster._core.remote_representation import RemoteRepository
from dagster._core.remote_representation.code_location import CodeLocation
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._core.remote_representation.origin import InProcessCodeLocationOrigin
from dagster._core.run_coordinator import RunCoordinator, SubmitRunContext
from dagster._core.secrets import SecretsLoader
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceProcessContext, WorkspaceRequestContext
from dagster._core.workspace.load_target import (
    InProcessWorkspaceLoadTarget as InProcessTestWorkspaceLoadTarget,
    WorkspaceLoadTarget,
)
from dagster._core.workspace.workspace import CodeLocationEntry, CurrentWorkspace
from dagster._serdes import ConfigurableClass
from dagster._serdes.config_class import ConfigurableClassData
from dagster._time import create_datetime, get_timezone
from dagster._utils import Counter, get_terminate_signal, traced, traced_counter
from dagster._utils.log import configure_loggers

T = TypeVar("T")
T_NamedTuple = TypeVar("T_NamedTuple", bound=NamedTuple)


def assert_namedtuple_lists_equal(
    t1_list: Sequence[T_NamedTuple],
    t2_list: Sequence[T_NamedTuple],
    exclude_fields: Optional[Sequence[str]] = None,
) -> None:
    assert len(t1_list) == len(t2_list)
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
                op_alias = "%s_node_%d" % (name, i)  # noqa: UP031
                inner.alias(op_alias)()

        return wrap

    @graph(name=name)
    def nested_graph():
        graph_def = create_wrap(leaf_node, "layer_%d" % depth)  # noqa: UP031

        for i in range(depth):
            graph_def = create_wrap(graph_def, "layer_%d" % (depth - (i + 1)))  # noqa: UP031

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
    remote_job_origin=None,
    job_code_origin=None,
    asset_selection=None,
    asset_check_selection=None,
    op_selection=None,
    asset_graph=None,
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
        remote_job_origin=remote_job_origin,
        job_code_origin=job_code_origin,
        asset_selection=asset_selection,
        asset_check_selection=asset_check_selection,
        op_selection=op_selection,
        asset_graph=asset_graph,
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


def poll_for_step_start(instance: DagsterInstance, run_id: str, timeout: float = 30, message=None):
    poll_for_event(instance, run_id, event_type="STEP_START", message=message, timeout=timeout)


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


def today_at_midnight(timezone_name="UTC") -> datetime.datetime:
    check.str_param(timezone_name, "timezone_name")
    tzinfo = get_timezone(timezone_name)
    now = datetime.datetime.now(tz=tzinfo)
    return create_datetime(now.year, now.month, now.day, tz=timezone_name)


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
        return cls(inst_data=inst_data)

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

    def launch_run(self, context):  # pyright: ignore[reportIncompatibleMethodOverride]
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
        check.not_none(dagster_run.remote_job_origin)
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
    def __init__(self, inst_data: Optional[ConfigurableClassData], env_vars: dict[str, str]):
        self._inst_data = inst_data
        self.env_vars = env_vars

    def get_secrets_for_environment(self, location_name: str) -> dict[str, str]:  # pyright: ignore[reportIncompatibleMethodOverride]
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
        return cls(inst_data=inst_data, **config_value)


def get_crash_signals() -> Sequence[Signals]:
    return [get_terminate_signal()]


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


def load_remote_repo(
    workspace_context: WorkspaceProcessContext, repo_name: str
) -> RemoteRepository:
    code_location_entry = next(
        iter(workspace_context.create_request_context().get_code_location_entries().values())
    )
    assert code_location_entry.code_location, code_location_entry.load_error
    return code_location_entry.code_location.get_repository(repo_name)


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


def wait_for_futures(futures: dict[str, Future], timeout: Optional[float] = None):
    start_time = time.time()
    results = {}
    for target_id, future in futures.copy().items():
        if timeout is not None:
            future_timeout = max(0, timeout - (time.time() - start_time))
        else:
            future_timeout = None

        if not future.done():
            results[target_id] = future.result(timeout=future_timeout)
            del futures[target_id]

    return results


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

    def decorator(func: Callable[..., Any]):
        def wrapper(*args, **kwargs):
            warnings.filterwarnings("ignore", message=message_substr)
            return func(*args, **kwargs)

        update_wrapper(wrapper, func)
        return wrapper

    return decorator


def raise_exception_on_warnings():
    # turn off any outer warnings filters, e.g. ignores that are set in pyproject.toml
    warnings.resetwarnings()
    warnings.filterwarnings("error")

    # This resource warning can sometimes appear (nondeterministically) when ephemeral instances are
    # used in tests. There seems to be an issue at the intersection of `DagsterInstance` weakrefs
    # and guaranteeing timely cleanup of the LocalArtifactStorage for the instance
    # LocalArtifactStorage.
    warnings.filterwarnings(
        "ignore", category=ResourceWarning, message=r".*Implicitly cleaning up.*"
    )


def ensure_dagster_tests_import() -> None:
    dagster_package_root = (Path(dagster_init_py) / ".." / "..").resolve()
    assert (
        dagster_package_root / "dagster_tests"
    ).exists(), "Could not find dagster_tests where expected"
    sys.path.append(dagster_package_root.as_posix())


def create_test_asset_job(
    assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    *,
    selection: Optional[CoercibleToAssetSelection] = None,
    name: str = "asset_job",
    resources: Mapping[str, object] = {},
    **kwargs: Any,
) -> JobDefinition:
    selection = selection or [a for a in assets if a.is_executable]
    return Definitions(
        assets=assets,
        jobs=[define_asset_job(name, selection, **kwargs)],
        resources=resources,
    ).get_job_def(name)


@contextmanager
def freeze_time(new_now: Union[datetime.datetime, float]):
    new_dt = (
        new_now
        if isinstance(new_now, datetime.datetime)
        else datetime.datetime.fromtimestamp(new_now, datetime.timezone.utc)
    )

    with (
        unittest.mock.patch("dagster._time._mockable_get_current_datetime", return_value=new_dt),
        unittest.mock.patch(
            "dagster._time._mockable_get_current_timestamp", return_value=new_dt.timestamp()
        ),
    ):
        yield


def mock_workspace_from_repos(repos: Sequence[RepositoryDefinition]) -> CurrentWorkspace:
    remote_repos = {}
    for repo in repos:
        remote_repos[repo.name] = RemoteRepository(
            RepositorySnap.from_def(repo),
            repository_handle=RepositoryHandle.for_test(
                location_name="test",
                repository_name=repo.name,
            ),
            auto_materialize_use_sensors=True,
        )
    mock_entry = unittest.mock.MagicMock(spec=CodeLocationEntry)
    mock_location = unittest.mock.MagicMock(spec=CodeLocation)
    mock_location.get_repositories.return_value = remote_repos
    type(mock_entry).code_location = unittest.mock.PropertyMock(return_value=mock_location)
    return CurrentWorkspace(code_location_entries={"test": mock_entry})
