import random
import string
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, contextmanager
from typing import TYPE_CHECKING, Optional, Sequence, cast

import pendulum
import pytest
from dagster import (
    Any,
    AssetKey,
    DefaultScheduleStatus,
    Field,
    ScheduleDefinition,
    asset,
    define_asset_job,
    job,
    materialize,
    op,
    repository,
    schedule,
)
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.decorators.source_asset_decorator import observable_source_asset
from dagster._core.definitions.run_request import RunRequest
from dagster._core.host_representation import (
    CodeLocation,
    ExternalInstigatorOrigin,
    ExternalRepositoryOrigin,
    GrpcServerCodeLocation,
    GrpcServerCodeLocationOrigin,
)
from dagster._core.host_representation.external import ExternalRepository, ExternalSchedule
from dagster._core.host_representation.origin import ManagedGrpcPythonEnvCodeLocationOrigin
from dagster._core.instance import DagsterInstance
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    InstigatorTick,
    InstigatorType,
    ScheduleInstigatorData,
    TickData,
    TickStatus,
)
from dagster._core.scheduler.scheduler import DEFAULT_MAX_CATCHUP_RUNS
from dagster._core.storage.dagster_run import DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import PARTITION_NAME_TAG, SCHEDULED_EXECUTION_TIME_TAG
from dagster._core.test_utils import (
    SingleThreadPoolExecutor,
    create_test_daemon_workspace_context,
    instance_for_test,
    mock_system_timezone,
    wait_for_futures,
)
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import EmptyWorkspaceTarget, GrpcServerTarget, ModuleTarget
from dagster._daemon import get_default_daemon_logger
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.server import open_server_process
from dagster._scheduler.scheduler import launch_scheduled_runs
from dagster._seven import wait_for_process
from dagster._seven.compat.pendulum import create_pendulum_time, to_timezone
from dagster._utils import DebugCrashFlags, find_free_port
from dagster._utils.error import SerializableErrorInfo
from dagster._utils.partitions import DEFAULT_DATE_FORMAT

from .conftest import loadable_target_origin, workspace_load_target

if TYPE_CHECKING:
    from pendulum.datetime import DateTime


def _throw(_context):
    raise Exception("bananas")


def _throw_on_odd_day(context):
    launch_time = context.scheduled_execution_time

    if launch_time.day % 2 == 1:
        raise Exception("Not a good day sorry")
    return True


def _never(_context):
    return False


def get_schedule_executors():
    return [
        pytest.param(
            None,
            id="synchronous",
        ),
        pytest.param(
            SingleThreadPoolExecutor(),
            id="threadpool",
        ),
    ]


def evaluate_schedules(
    workspace_context: WorkspaceProcessContext,
    executor: Optional[ThreadPoolExecutor],
    end_datetime_utc: "DateTime",
    max_tick_retries: int = 0,
    max_catchup_runs: int = DEFAULT_MAX_CATCHUP_RUNS,
    debug_crash_flags: Optional[DebugCrashFlags] = None,
    timeout: int = 75,
):
    logger = get_default_daemon_logger("SchedulerDaemon")
    futures = {}
    list(
        launch_scheduled_runs(
            workspace_context,
            logger,
            end_datetime_utc,
            threadpool_executor=executor,
            scheduler_run_futures=futures,
            max_tick_retries=max_tick_retries,
            max_catchup_runs=max_catchup_runs,
            debug_crash_flags=debug_crash_flags,
        )
    )

    wait_for_futures(futures, timeout=timeout)


@op(config_schema={"time": str})
def the_op(context):
    return "Ran at this time: {}".format(context.op_config["time"])


@job
def the_job():
    the_op()


def _op_config(date: "DateTime"):
    return {
        "ops": {"the_op": {"config": {"time": date.isoformat()}}},
    }


@schedule(cron_schedule="@daily", job_name="the_job", execution_timezone="UTC")
def simple_schedule(context):
    return _op_config(context.scheduled_execution_time)


@schedule(cron_schedule="@daily", job_name="the_job")
def simple_schedule_no_timezone(context):
    return _op_config(context.scheduled_execution_time)


@schedule(
    cron_schedule="@daily",
    job_name="the_job",
    execution_timezone="US/Central",
)
def daily_central_time_schedule(context):
    return _op_config(context.scheduled_execution_time)


@schedule(
    job_name="the_job",
    cron_schedule=["0 0 * * 4", "0 0 * * 5", "0 0,12 * * 5"],
    execution_timezone="UTC",
)
def union_schedule(context):
    return _op_config(context.scheduled_execution_time)


# Schedule that runs on a different day in Central Time vs UTC
@schedule(
    cron_schedule="0 23 * * *",
    job_name="the_job",
    execution_timezone="US/Central",
)
def daily_late_schedule(context):
    return _op_config(context.scheduled_execution_time)


@schedule(
    cron_schedule="30 2 * * *",
    job_name="the_job",
    execution_timezone="US/Central",
)
def daily_dst_transition_schedule_skipped_time(context):
    return _op_config(context.scheduled_execution_time)


@schedule(
    cron_schedule="30 1 * * *",
    job_name="the_job",
    execution_timezone="US/Central",
)
def daily_dst_transition_schedule_doubled_time(context):
    return _op_config(context.scheduled_execution_time)


@schedule(
    cron_schedule="@daily",
    job_name="the_job",
    execution_timezone="US/Eastern",
)
def daily_eastern_time_schedule(context):
    return _op_config(context.scheduled_execution_time)


NUM_CALLS = {"sync": 0, "async": 0}


def get_passes_on_retry_schedule(key: str) -> ScheduleDefinition:
    @schedule(
        cron_schedule="@daily",
        job_name="the_job",
        execution_timezone="UTC",
        name=f"passes_on_retry_schedule_{key}",
    )
    def passes_on_retry_schedule(context):
        NUM_CALLS[key] = NUM_CALLS[key] + 1
        if NUM_CALLS[key] > 1:
            return _op_config(context.scheduled_execution_time)
        raise Exception("better luck next time")

    return passes_on_retry_schedule


@schedule(
    cron_schedule="@hourly",
    job_name="the_job",
    execution_timezone="UTC",
)
def simple_hourly_schedule(context):
    return _op_config(context.scheduled_execution_time)


@schedule(
    cron_schedule="@hourly",
    job_name="the_job",
    execution_timezone="US/Central",
)
def hourly_central_time_schedule(context):
    return _op_config(context.scheduled_execution_time)


@schedule(
    cron_schedule="@daily",
    job_name="the_job",
    should_execute=_throw,
    execution_timezone="UTC",
)
def bad_should_execute_schedule(context):
    return _op_config(context.scheduled_execution_time)


@schedule(
    cron_schedule="@daily",
    job_name="the_job",
    should_execute=_throw_on_odd_day,
    execution_timezone="UTC",
)
def bad_should_execute_on_odd_days_schedule(context):
    return _op_config(context.scheduled_execution_time)


@schedule(
    cron_schedule="@daily",
    job_name="the_job",
    should_execute=_never,
    execution_timezone="UTC",
)
def skip_schedule(context):
    return _op_config(context.scheduled_execution_time)


@schedule(
    cron_schedule="@daily",
    job_name="the_job",
    execution_timezone="UTC",
)
def wrong_config_schedule(context):
    return {}


@schedule(
    job_name="the_job",
    cron_schedule="0 0 * * *",
    execution_timezone="UTC",
)
def empty_schedule(_date):
    return []


def define_multi_run_schedule():
    def gen_runs(context):
        if not context.scheduled_execution_time:
            date = pendulum.now().subtract(days=1)
        else:
            date = pendulum.instance(context.scheduled_execution_time).subtract(days=1)

        yield RunRequest(run_key="A", run_config=_op_config(date), tags={"label": "A"})
        yield RunRequest(run_key="B", run_config=_op_config(date), tags={"label": "B"})

    return ScheduleDefinition(
        name="multi_run_schedule",
        cron_schedule="0 0 * * *",
        job_name="the_job",
        execution_timezone="UTC",
        execution_fn=gen_runs,
    )


@schedule(
    job_name="the_job",
    cron_schedule="0 0 * * *",
    execution_timezone="UTC",
)
def multi_run_list_schedule(context):
    if not context.scheduled_execution_time:
        date = pendulum.now().subtract(days=1)
    else:
        date = pendulum.instance(context.scheduled_execution_time).subtract(days=1)

    return [
        RunRequest(run_key="A", run_config=_op_config(date), tags={"label": "A"}),
        RunRequest(run_key="B", run_config=_op_config(date), tags={"label": "B"}),
    ]


def define_multi_run_schedule_with_missing_run_key():
    def gen_runs(context):
        if not context.scheduled_execution_time:
            date = pendulum.now().subtract(days=1)
        else:
            date = pendulum.instance(context.scheduled_execution_time).subtract(days=1)

        yield RunRequest(run_key="A", run_config=_op_config(date), tags={"label": "A"})
        yield RunRequest(run_key=None, run_config=_op_config(date), tags={"label": "B"})

    return ScheduleDefinition(
        name="multi_run_schedule_with_missing_run_key",
        cron_schedule="0 0 * * *",
        job_name="the_job",
        execution_timezone="UTC",
        execution_fn=gen_runs,
    )


@repository
def the_other_repo():
    return [
        the_job,
        multi_run_list_schedule,
    ]


@op(config_schema=Field(Any))
def config_op(_):
    return 1


@job
def config_job():
    config_op()


@schedule(
    cron_schedule="@daily",
    job_name="config_job",
    execution_timezone="UTC",
)
def large_schedule(_):
    REQUEST_CONFIG_COUNT = 120000

    def _random_string(length):
        return "".join(random.choice(string.ascii_lowercase) for x in range(length))

    return {
        "ops": {
            "config_op": {
                "config": {
                    "foo": {
                        _random_string(10): _random_string(20) for i in range(REQUEST_CONFIG_COUNT)
                    }
                }
            }
        }
    }


@op
def start(_, x):
    return x


@op
def end(_, x=1):
    return x


@job
def two_step_job():
    end(start())


def define_default_config_job():
    @op(config_schema=str)
    def my_op(context):
        assert context.op_config == "foo"

    @job(config={"ops": {"my_op": {"config": "foo"}}})
    def default_config_job():
        my_op()

    return default_config_job


default_config_schedule = ScheduleDefinition(
    name="default_config_schedule",
    cron_schedule="* * * * *",
    job=define_default_config_job(),
)


@asset
def asset1():
    return "asset1"


@asset
def asset2(asset1):
    return asset1 + "asset2"


asset_job = define_asset_job("asset_job")


@schedule(job=asset_job, cron_schedule="@daily")
def asset_selection_schedule():
    return RunRequest(asset_selection=[asset1.key])


@schedule(job=asset_job, cron_schedule="@daily")
def stale_asset_selection_schedule():
    return RunRequest(stale_assets_only=True)


@observable_source_asset
def source_asset():
    return DataVersion("foo")


observable_source_asset_job = define_asset_job(
    "observable_source_asset_job", selection=[source_asset]
)


@schedule(job=observable_source_asset_job, cron_schedule="@daily")
def source_asset_observation_schedule():
    return RunRequest(asset_selection=[source_asset.key])


@repository
def the_repo():
    return [
        the_job,
        config_job,
        simple_schedule,
        simple_hourly_schedule,
        simple_schedule_no_timezone,
        daily_late_schedule,
        daily_dst_transition_schedule_skipped_time,
        daily_dst_transition_schedule_doubled_time,
        daily_central_time_schedule,
        daily_eastern_time_schedule,
        hourly_central_time_schedule,
        get_passes_on_retry_schedule("sync"),
        get_passes_on_retry_schedule("async"),
        bad_should_execute_schedule,
        bad_should_execute_on_odd_days_schedule,
        skip_schedule,
        wrong_config_schedule,
        define_multi_run_schedule(),
        multi_run_list_schedule,
        define_multi_run_schedule_with_missing_run_key(),
        union_schedule,
        large_schedule,
        two_step_job,
        default_config_schedule,
        empty_schedule,
        [asset1, asset2, source_asset],
        asset_selection_schedule,
        stale_asset_selection_schedule,
        source_asset_observation_schedule,
    ]


@schedule(
    cron_schedule="@daily",
    job_name="the_job",
    execution_timezone="UTC",
    default_status=DefaultScheduleStatus.RUNNING,
)
def always_running_schedule(context):
    return _op_config(context.scheduled_execution_time)


@schedule(
    cron_schedule="@daily",
    job_name="the_job",
    execution_timezone="UTC",
    default_status=DefaultScheduleStatus.STOPPED,
)
def never_running_schedule(context):
    return _op_config(context.scheduled_execution_time)


@repository
def the_status_in_code_repo():
    return [
        the_job,
        always_running_schedule,
        never_running_schedule,
    ]


def logger():
    return get_default_daemon_logger("SchedulerDaemon")


def validate_tick(
    tick: InstigatorTick,
    external_schedule: ExternalSchedule,
    expected_datetime: "DateTime",
    expected_status: TickStatus,
    expected_run_ids: Sequence[str],
    expected_error: Optional[str] = None,
    expected_failure_count: int = 0,
    expected_skip_reason: Optional[str] = None,
) -> None:
    tick_data = tick.tick_data
    assert tick_data.instigator_origin_id == external_schedule.get_external_origin_id()
    assert tick_data.instigator_name == external_schedule.name
    assert tick_data.timestamp == expected_datetime.timestamp()
    assert tick_data.status == expected_status
    assert len(tick_data.run_ids) == len(expected_run_ids) and set(tick_data.run_ids) == set(
        expected_run_ids
    )
    if expected_error:
        assert expected_error in str(tick_data.error)
    assert tick_data.failure_count == expected_failure_count
    assert tick_data.skip_reason == expected_skip_reason


def validate_run_exists(
    run,
    execution_time,
    partition_time=None,
    partition_fmt=DEFAULT_DATE_FORMAT,
):
    assert run.tags[SCHEDULED_EXECUTION_TIME_TAG] == to_timezone(execution_time, "UTC").isoformat()

    if partition_time:
        assert run.tags[PARTITION_NAME_TAG] == partition_time.strftime(partition_fmt)


def validate_run_started(
    instance,
    run,
    execution_time,
    partition_time=None,
    partition_fmt=DEFAULT_DATE_FORMAT,
    expected_success=True,
):
    validate_run_exists(run, execution_time, partition_time, partition_fmt)

    if expected_success:
        assert instance.run_launcher.did_run_launch(run.run_id)

        if partition_time:
            assert run.run_config == _op_config(partition_time)
    else:
        assert run.status == DagsterRunStatus.FAILURE


def wait_for_all_runs_to_start(instance, timeout=10):
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            raise Exception("Timed out waiting for runs to start")
        time.sleep(0.5)

        not_started_runs = [
            run for run in instance.get_runs() if run.status == DagsterRunStatus.NOT_STARTED
        ]

        if len(not_started_runs) == 0:
            break


def feb_27_2019_one_second_to_midnight() -> "DateTime":
    return to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )


def feb_27_2019_start_of_day() -> "DateTime":
    return to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0, tz="UTC"),
        "US/Central",
    )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_simple_schedule(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    freeze_datetime = feb_27_2019_one_second_to_midnight()
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("simple_schedule")

        schedule_origin = external_schedule.get_external_origin()

        instance.start_schedule(external_schedule)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

        # launch_scheduled_runs does nothing before the first tick
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        expected_datetime = create_pendulum_time(year=2019, month=2, day=28)

        validate_tick(
            ticks[0],
            external_schedule,
            expected_datetime,
            TickStatus.SUCCESS,
            [run.run_id for run in instance.get_runs()],
        )

        wait_for_all_runs_to_start(instance)
        validate_run_started(
            instance,
            next(iter(instance.get_runs())),
            execution_time=create_pendulum_time(2019, 2, 28),
        )

        # Verify idempotence
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS

    # Verify advancing in time but not going past a tick doesn't add any new runs
    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS

    freeze_datetime = freeze_datetime.add(days=2)
    with pendulum.test(freeze_datetime):
        # Traveling two more days in the future passes two ticks times, but only the most recent
        # will be created as a tick with a corresponding run.
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 2
        assert len([tick for tick in ticks if tick.status == TickStatus.SUCCESS]) == 2

        # Check idempotence again
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 2


# Verify that the scheduler uses selector and not origin to dedupe schedules
@pytest.mark.parametrize("executor", get_schedule_executors())
def test_schedule_with_different_origin(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    external_schedule = external_repo.get_external_schedule("simple_schedule")
    existing_origin = external_schedule.get_external_origin()

    code_location_origin = existing_origin.external_repository_origin.code_location_origin
    assert isinstance(code_location_origin, ManagedGrpcPythonEnvCodeLocationOrigin)
    modified_loadable_target_origin = code_location_origin.loadable_target_origin._replace(
        executable_path="/different/executable_path"
    )

    # Change metadata on the origin that shouldn't matter for execution
    modified_origin = existing_origin._replace(
        external_repository_origin=existing_origin.external_repository_origin._replace(
            code_location_origin=code_location_origin._replace(
                loadable_target_origin=modified_loadable_target_origin
            )
        )
    )

    freeze_datetime = feb_27_2019_one_second_to_midnight()
    with pendulum.test(freeze_datetime):
        schedule_state = InstigatorState(
            modified_origin,
            InstigatorType.SCHEDULE,
            InstigatorStatus.RUNNING,
            ScheduleInstigatorData(
                external_schedule.cron_schedule, pendulum.now("UTC").timestamp()
            ),
        )
        instance.add_instigator_state(schedule_state)

        freeze_datetime = freeze_datetime.add(seconds=2)

    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(existing_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_old_tick_schedule(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    freeze_datetime = feb_27_2019_one_second_to_midnight()
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("simple_schedule")

        # Create an old tick from several days ago
        instance.create_tick(
            TickData(
                instigator_origin_id=external_schedule.get_external_origin_id(),
                instigator_name="simple_schedule",
                instigator_type=InstigatorType.SCHEDULE,
                status=TickStatus.STARTED,
                timestamp=pendulum.now("UTC").subtract(days=3).timestamp(),
                selector_id=external_schedule.selector_id,
            )
        )

        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 2


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_no_started_schedules(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    external_schedule = external_repo.get_external_schedule("simple_schedule")
    schedule_origin = external_schedule.get_external_origin()

    evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
    assert instance.get_runs_count() == 0

    ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
    assert len(ticks) == 0


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_schedule_without_timezone(instance: DagsterInstance, executor: ThreadPoolExecutor):
    with mock_system_timezone("US/Eastern"):
        with create_test_daemon_workspace_context(
            workspace_load_target=workspace_load_target(),
            instance=instance,
        ) as workspace_context:
            code_location = next(
                iter(workspace_context.create_request_context().get_workspace_snapshot().values())
            ).code_location
            assert code_location is not None
            external_repo = code_location.get_repository("the_repo")
            external_schedule = external_repo.get_external_schedule("simple_schedule_no_timezone")
            schedule_origin = external_schedule.get_external_origin()
            initial_datetime = create_pendulum_time(
                year=2019, month=2, day=27, hour=0, minute=0, second=0, tz="UTC"
            )

            with pendulum.test(initial_datetime):
                instance.start_schedule(external_schedule)

                evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

                assert instance.get_runs_count() == 1

                ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)

                assert len(ticks) == 1

                expected_datetime = create_pendulum_time(year=2019, month=2, day=27, tz="UTC")

                validate_tick(
                    ticks[0],
                    external_schedule,
                    expected_datetime,
                    TickStatus.SUCCESS,
                    [run.run_id for run in instance.get_runs()],
                )

                wait_for_all_runs_to_start(instance)
                validate_run_started(
                    instance,
                    next(iter(instance.get_runs())),
                    execution_time=expected_datetime,
                )

                # Verify idempotence
                evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
                assert instance.get_runs_count() == 1
                ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
                assert len(ticks) == 1


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_bad_eval_fn_no_retries(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    external_schedule = external_repo.get_external_schedule("wrong_config_schedule")
    schedule_origin = external_schedule.get_external_origin()
    freeze_datetime = create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0)
    with pendulum.test(freeze_datetime):
        instance.start_schedule(external_schedule)

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            freeze_datetime,
            TickStatus.FAILURE,
            [run.run_id for run in instance.get_runs()],
            "DagsterInvalidConfigError",
            expected_failure_count=1,
        )

        # Idempotency (tick does not retry)
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            freeze_datetime,
            TickStatus.FAILURE,
            [],
            "DagsterInvalidConfigError",
            expected_failure_count=1,
        )

    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 2

        validate_tick(
            ticks[0],
            external_schedule,
            freeze_datetime,
            TickStatus.FAILURE,
            [],
            "DagsterInvalidConfigError",
            expected_failure_count=1,
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_invalid_eval_fn_with_retries(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    external_schedule = external_repo.get_external_schedule("wrong_config_schedule")
    schedule_origin = external_schedule.get_external_origin()
    freeze_datetime = create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0)
    with pendulum.test(freeze_datetime):
        instance.start_schedule(external_schedule)

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"), max_tick_retries=2)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            freeze_datetime,
            TickStatus.FAILURE,
            [],
            "Missing required config entry",
            expected_failure_count=1,
        )

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"), max_tick_retries=2)
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"), max_tick_retries=2)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            freeze_datetime,
            TickStatus.FAILURE,
            [],
            "Missing required config entry",
            expected_failure_count=3,
        )

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"), max_tick_retries=2)
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            freeze_datetime,
            TickStatus.FAILURE,
            [],
            "Missing required config entry",
            expected_failure_count=3,
        )

    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 2

        validate_tick(
            ticks[0],
            external_schedule,
            freeze_datetime,
            TickStatus.FAILURE,
            [],
            "Missing required config entry",
            expected_failure_count=1,
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_passes_on_retry(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    # We need to use different keys across sync and async executors, as the dictionary is persisted across processes.
    if isinstance(executor, SingleThreadPoolExecutor):
        schedule_name = "passes_on_retry_schedule_sync"
    else:
        schedule_name = "passes_on_retry_schedule_async"
    external_schedule = external_repo.get_external_schedule(schedule_name)
    schedule_origin = external_schedule.get_external_origin()
    freeze_datetime = create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0)
    with pendulum.test(freeze_datetime):
        instance.start_schedule(external_schedule)

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"), max_tick_retries=1)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            freeze_datetime,
            TickStatus.FAILURE,
            [],
            f"Error occurred during the evaluation of schedule {schedule_name}",
            expected_failure_count=1,
        )

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"), max_tick_retries=1)

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            freeze_datetime,
            TickStatus.SUCCESS,
            [run.run_id for run in instance.get_runs()],
            expected_failure_count=1,
        )

    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"), max_tick_retries=1)

        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 2

        validate_tick(
            ticks[0],
            external_schedule,
            freeze_datetime,
            TickStatus.SUCCESS,
            [next(iter(instance.get_runs())).run_id],
            expected_failure_count=0,
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_bad_should_execute(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    external_schedule = external_repo.get_external_schedule("bad_should_execute_schedule")
    schedule_origin = external_schedule.get_external_origin()
    initial_datetime = create_pendulum_time(
        year=2019,
        month=2,
        day=27,
        hour=0,
        minute=0,
        second=0,
    )
    with pendulum.test(initial_datetime):
        instance.start_schedule(external_schedule)

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            initial_datetime,
            TickStatus.FAILURE,
            [run.run_id for run in instance.get_runs()],
            (
                "Error occurred during the execution of should_execute for schedule"
                " bad_should_execute_schedule"
            ),
            expected_failure_count=1,
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_skip(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    external_schedule = external_repo.get_external_schedule("skip_schedule")
    schedule_origin = external_schedule.get_external_origin()
    freeze_datetime = feb_27_2019_start_of_day()
    with pendulum.test(freeze_datetime):
        instance.start_schedule(external_schedule)

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            external_schedule,
            freeze_datetime,
            TickStatus.SKIPPED,
            [run.run_id for run in instance.get_runs()],
            expected_skip_reason="should_execute function for skip_schedule returned false.",
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_wrong_config_schedule(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    external_schedule = external_repo.get_external_schedule("wrong_config_schedule")
    schedule_origin = external_schedule.get_external_origin()
    freeze_datetime = create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0)
    with pendulum.test(freeze_datetime):
        instance.start_schedule(external_schedule)

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0

        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            external_schedule,
            freeze_datetime,
            TickStatus.FAILURE,
            [],
            "DagsterInvalidConfigError",
            expected_failure_count=1,
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_schedule_run_default_config(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    external_schedule = external_repo.get_external_schedule("default_config_schedule")
    schedule_origin = external_schedule.get_external_origin()
    initial_datetime = create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0)
    with pendulum.test(initial_datetime):
        instance.start_schedule(external_schedule)

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1

        wait_for_all_runs_to_start(instance)

        run = next(iter(instance.get_runs()))

        validate_run_started(
            instance,
            run,
            execution_time=initial_datetime,
            expected_success=True,
        )

        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            external_schedule,
            initial_datetime,
            TickStatus.SUCCESS,
            [run.run_id for run in instance.get_runs()],
        )

        assert instance.run_launcher.did_run_launch(run.run_id)  # type: ignore  # (unspecified instance subclass)


def _get_unloadable_schedule_origin():
    load_target = workspace_load_target()
    return ExternalRepositoryOrigin(
        load_target.create_origins()[0], "fake_repository"
    ).get_instigator_origin("doesnt_exist")


def _get_unloadable_workspace_load_target():
    return ModuleTarget(
        module_name="doesnt_exist_module",
        attribute=None,
        location_name="unloadable_location",
        working_directory=None,
    )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_bad_schedules_mixed_with_good_schedule(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    good_schedule = external_repo.get_external_schedule("simple_schedule")
    bad_schedule = external_repo.get_external_schedule("bad_should_execute_on_odd_days_schedule")

    good_origin = good_schedule.get_external_origin()
    bad_origin = bad_schedule.get_external_origin()
    unloadable_origin = _get_unloadable_schedule_origin()
    freeze_datetime = feb_27_2019_start_of_day()
    with pendulum.test(freeze_datetime):
        instance.start_schedule(good_schedule)
        instance.start_schedule(bad_schedule)

        unloadable_schedule_state = InstigatorState(
            unloadable_origin,
            InstigatorType.SCHEDULE,
            InstigatorStatus.RUNNING,
            ScheduleInstigatorData("0 0 * * *", pendulum.now("UTC").timestamp()),
        )
        instance.add_instigator_state(unloadable_schedule_state)

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        wait_for_all_runs_to_start(instance)
        validate_run_started(
            instance,
            next(iter(instance.get_runs())),
            execution_time=freeze_datetime,
        )

        good_ticks = instance.get_ticks(good_origin.get_id(), good_schedule.selector_id)
        assert len(good_ticks) == 1
        validate_tick(
            good_ticks[0],
            good_schedule,
            freeze_datetime,
            TickStatus.SUCCESS,
            [run.run_id for run in instance.get_runs()],
        )

        bad_ticks = instance.get_ticks(bad_origin.get_id(), bad_schedule.selector_id)
        assert len(bad_ticks) == 1

        assert bad_ticks[0].status == TickStatus.FAILURE

        assert "Error occurred during the execution of should_execute for schedule bad_should_execute_on_odd_days_schedule" in bad_ticks[0].error.message  # type: ignore  # (possible none)

        unloadable_ticks = instance.get_ticks(unloadable_origin.get_id(), "fake_selector")
        assert len(unloadable_ticks) == 0

    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        new_now = pendulum.now("UTC")
        evaluate_schedules(workspace_context, executor, new_now)

        assert instance.get_runs_count() == 3
        wait_for_all_runs_to_start(instance)

        good_schedule_runs = instance.get_runs(filters=RunsFilter.for_schedule(good_schedule))
        assert len(good_schedule_runs) == 2
        validate_run_started(
            instance,
            good_schedule_runs[0],
            execution_time=new_now,
        )

        good_ticks = instance.get_ticks(good_origin.get_id(), good_schedule.selector_id)
        assert len(good_ticks) == 2
        validate_tick(
            good_ticks[0],
            good_schedule,
            new_now,
            TickStatus.SUCCESS,
            [good_schedule_runs[0].run_id],
        )

        bad_schedule_runs = instance.get_runs(filters=RunsFilter.for_schedule(bad_schedule))
        assert len(bad_schedule_runs) == 1
        validate_run_started(
            instance,
            bad_schedule_runs[0],
            execution_time=new_now,
        )

        bad_ticks = instance.get_ticks(bad_origin.get_id(), bad_schedule.selector_id)
        assert len(bad_ticks) == 2
        validate_tick(
            bad_ticks[0],
            bad_schedule,
            new_now,
            TickStatus.SUCCESS,
            [bad_schedule_runs[0].run_id],
        )

        unloadable_ticks = instance.get_ticks(unloadable_origin.get_id(), "fake_selector")
        assert len(unloadable_ticks) == 0


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_run_scheduled_on_time_boundary(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    external_schedule = external_repo.get_external_schedule("simple_schedule")

    schedule_origin = external_schedule.get_external_origin()
    freeze_datetime = feb_27_2019_start_of_day()  # 00:00:00
    with pendulum.test(freeze_datetime):
        # Start schedule exactly at midnight
        instance.start_schedule(external_schedule)

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_bad_load_repository(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    caplog: pytest.LogCaptureFixture,
    executor: ThreadPoolExecutor,
):
    freeze_datetime = feb_27_2019_one_second_to_midnight()
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        valid_schedule_origin = external_schedule.get_external_origin()

        # Swap out a new repository name
        invalid_repo_origin = ExternalInstigatorOrigin(
            ExternalRepositoryOrigin(
                valid_schedule_origin.external_repository_origin.code_location_origin,
                "invalid_repo_name",
            ),
            valid_schedule_origin.instigator_name,
        )

        schedule_state = InstigatorState(
            invalid_repo_origin,
            InstigatorType.SCHEDULE,
            InstigatorStatus.RUNNING,
            ScheduleInstigatorData("0 0 * * *", pendulum.now("UTC").timestamp()),
        )
        instance.add_instigator_state(schedule_state)

    initial_datetime = freeze_datetime.add(seconds=1)
    with pendulum.test(initial_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0

        ticks = instance.get_ticks(invalid_repo_origin.get_id(), external_schedule.selector_id)

        assert len(ticks) == 0

        assert (
            "Could not find repository invalid_repo_name in location test_location to run schedule"
            " simple_schedule"
            in caplog.text
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_bad_load_schedule(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    caplog,
    executor: ThreadPoolExecutor,
):
    freeze_datetime = feb_27_2019_one_second_to_midnight()
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        valid_schedule_origin = external_schedule.get_external_origin()

        # Swap out a new schedule name
        invalid_repo_origin = ExternalInstigatorOrigin(
            valid_schedule_origin.external_repository_origin,
            "invalid_schedule",
        )

        schedule_state = InstigatorState(
            invalid_repo_origin,
            InstigatorType.SCHEDULE,
            InstigatorStatus.RUNNING,
            ScheduleInstigatorData("0 0 * * *", pendulum.now("UTC").timestamp()),
        )
        instance.add_instigator_state(schedule_state)

    initial_datetime = freeze_datetime.add(seconds=1)
    with pendulum.test(initial_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0

        ticks = instance.get_ticks(invalid_repo_origin.get_id(), schedule_state.selector_id)

        assert len(ticks) == 0

        assert "Could not find schedule invalid_schedule in repository the_repo." in caplog.text


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_error_load_code_location(instance: DagsterInstance, executor: ThreadPoolExecutor):
    with create_test_daemon_workspace_context(
        _get_unloadable_workspace_load_target(), instance
    ) as workspace_context:
        fake_origin = _get_unloadable_schedule_origin()
        freeze_datetime = feb_27_2019_one_second_to_midnight()
        with pendulum.test(freeze_datetime):
            schedule_state = InstigatorState(
                fake_origin,
                InstigatorType.SCHEDULE,
                InstigatorStatus.RUNNING,
                ScheduleInstigatorData("0 0 * * *", pendulum.now("UTC").timestamp()),
            )
            instance.add_instigator_state(schedule_state)

        freeze_datetime = freeze_datetime.add(seconds=1)
        with pendulum.test(freeze_datetime):
            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

            assert instance.get_runs_count() == 0

            ticks = instance.get_ticks(fake_origin.get_id(), schedule_state.selector_id)

            assert len(ticks) == 0

        freeze_datetime = freeze_datetime.add(days=1)
        with pendulum.test(freeze_datetime):
            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
            assert instance.get_runs_count() == 0
            ticks = instance.get_ticks(fake_origin.get_id(), schedule_state.selector_id)
            assert len(ticks) == 0


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_load_code_location_not_in_workspace(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    caplog: pytest.LogCaptureFixture,
    executor: ThreadPoolExecutor,
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )

    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        valid_schedule_origin = external_schedule.get_external_origin()

        code_location_origin = valid_schedule_origin.external_repository_origin.code_location_origin
        assert isinstance(code_location_origin, ManagedGrpcPythonEnvCodeLocationOrigin)

        # Swap out a new location name
        invalid_repo_origin = ExternalInstigatorOrigin(
            ExternalRepositoryOrigin(
                code_location_origin._replace(location_name="missing_location"),
                valid_schedule_origin.external_repository_origin.repository_name,
            ),
            valid_schedule_origin.instigator_name,
        )

        schedule_state = InstigatorState(
            invalid_repo_origin,
            InstigatorType.SCHEDULE,
            InstigatorStatus.RUNNING,
            ScheduleInstigatorData("0 0 * * *", pendulum.now("UTC").timestamp()),
        )
        instance.add_instigator_state(schedule_state)

    initial_datetime = freeze_datetime.add(seconds=1)
    with pendulum.test(initial_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0

        ticks = instance.get_ticks(invalid_repo_origin.get_id(), schedule_state.selector_id)

        assert len(ticks) == 0

        assert (
            "Schedule simple_schedule was started from a location missing_location that can no"
            " longer be found in the workspace"
            in caplog.text
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_multiple_schedules_on_different_time_ranges(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    external_schedule = external_repo.get_external_schedule("simple_schedule")
    external_hourly_schedule = external_repo.get_external_schedule("simple_hourly_schedule")
    freeze_datetime = feb_27_2019_one_second_to_midnight()
    with pendulum.test(freeze_datetime):
        instance.start_schedule(external_schedule)
        instance.start_schedule(external_hourly_schedule)

    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(
            external_schedule.get_external_origin_id(), external_schedule.selector_id
        )
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS

        hourly_ticks = instance.get_ticks(
            external_hourly_schedule.get_external_origin_id(),
            external_hourly_schedule.selector_id,
        )
        assert len(hourly_ticks) == 1
        assert hourly_ticks[0].status == TickStatus.SUCCESS

    freeze_datetime = freeze_datetime.add(hours=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 3

        ticks = instance.get_ticks(
            external_schedule.get_external_origin_id(), external_schedule.selector_id
        )
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS

        hourly_ticks = instance.get_ticks(
            external_hourly_schedule.get_external_origin_id(),
            external_hourly_schedule.selector_id,
        )
        assert len(hourly_ticks) == 2
        assert len([tick for tick in hourly_ticks if tick.status == TickStatus.SUCCESS]) == 2


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_launch_failure(
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster._core.test_utils",
                "class": "ExplodingRunLauncher",
            },
        },
    ) as instance:
        external_schedule = external_repo.get_external_schedule("simple_schedule")

        schedule_origin = external_schedule.get_external_origin()
        freeze_datetime = feb_27_2019_start_of_day()
        with pendulum.test(freeze_datetime):
            exploding_ctx = workspace_context.copy_for_test_instance(instance)
            instance.start_schedule(external_schedule)

            evaluate_schedules(exploding_ctx, executor, pendulum.now("UTC"))

            assert instance.get_runs_count() == 1

            run = next(iter(instance.get_runs()))

            validate_run_started(
                instance,
                run,
                execution_time=freeze_datetime,
                expected_success=False,
            )

            ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_schedule,
                freeze_datetime,
                TickStatus.SUCCESS,
                [run.run_id for run in instance.get_runs()],
            )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_union_schedule(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    # This is a Wednesday.
    freeze_datetime = feb_27_2019_start_of_day()
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("union_schedule")
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

    # No new runs should be launched
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 0

        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 1

        wait_for_all_runs_to_start(instance)

        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            create_pendulum_time(year=2019, month=2, day=28, tz="UTC"),
            TickStatus.SUCCESS,
            [next(iter(instance.get_runs())).run_id],
        )

        validate_run_started(
            instance,
            next(iter(instance.get_runs())),
            execution_time=create_pendulum_time(year=2019, month=2, day=28, tz="UTC"),
            partition_time=None,
        )

    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 2

        wait_for_all_runs_to_start(instance)

        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 2

        validate_tick(
            ticks[0],
            external_schedule,
            create_pendulum_time(year=2019, month=3, day=1, tz="UTC"),
            TickStatus.SUCCESS,
            [next(iter(instance.get_runs())).run_id],
        )

        validate_run_started(
            instance,
            next(iter(instance.get_runs())),
            execution_time=create_pendulum_time(year=2019, month=3, day=1, tz="UTC"),
        )

    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 3

        wait_for_all_runs_to_start(instance)

        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 3

        validate_tick(
            ticks[0],
            external_schedule,
            create_pendulum_time(year=2019, month=3, day=1, hour=12, tz="UTC"),
            TickStatus.SUCCESS,
            [next(iter(instance.get_runs())).run_id],
        )

        validate_run_started(
            instance,
            next(iter(instance.get_runs())),
            execution_time=create_pendulum_time(year=2019, month=3, day=1, hour=12, tz="UTC"),
            partition_time=None,
        )

    # No new runs should be launched
    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 3

        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 3


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_multi_runs(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    freeze_datetime = feb_27_2019_one_second_to_midnight()
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("multi_run_schedule")
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

        # launch_scheduled_runs does nothing before the first tick
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        expected_datetime = create_pendulum_time(year=2019, month=2, day=28)

        runs = instance.get_runs()
        validate_tick(
            ticks[0],
            external_schedule,
            expected_datetime,
            TickStatus.SUCCESS,
            [run.run_id for run in runs],
        )

        wait_for_all_runs_to_start(instance)
        runs = instance.get_runs()
        validate_run_started(instance, runs[0], execution_time=create_pendulum_time(2019, 2, 28))
        validate_run_started(instance, runs[1], execution_time=create_pendulum_time(2019, 2, 28))

        # Verify idempotence
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS

    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        # Traveling one more day in the future before running results in a tick
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 4
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 2
        assert len([tick for tick in ticks if tick.status == TickStatus.SUCCESS]) == 2
        runs = instance.get_runs()


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_multi_run_list(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    freeze_datetime = feb_27_2019_one_second_to_midnight()
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("multi_run_list_schedule")
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

        # launch_scheduled_runs does nothing before the first tick
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        expected_datetime = create_pendulum_time(year=2019, month=2, day=28)

        runs = instance.get_runs()
        validate_tick(
            ticks[0],
            external_schedule,
            expected_datetime,
            TickStatus.SUCCESS,
            [run.run_id for run in runs],
        )

        wait_for_all_runs_to_start(instance)
        runs = instance.get_runs()
        validate_run_started(instance, runs[0], execution_time=create_pendulum_time(2019, 2, 28))
        validate_run_started(instance, runs[1], execution_time=create_pendulum_time(2019, 2, 28))

        # Verify idempotence
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS

    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        # Traveling one more day in the future before running results in a tick
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 4
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 2
        assert len([tick for tick in ticks if tick.status == TickStatus.SUCCESS]) == 2
        runs = instance.get_runs()


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_multi_runs_missing_run_key(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    freeze_datetime = feb_27_2019_start_of_day()
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule(
            "multi_run_schedule_with_missing_run_key"
        )
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            freeze_datetime,
            TickStatus.FAILURE,
            [],
            (
                "Error occurred during the execution function for schedule "
                "multi_run_schedule_with_missing_run_key"
            ),
            expected_failure_count=1,
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_large_schedule(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    freeze_datetime = feb_27_2019_one_second_to_midnight()
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("large_schedule")
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

        freeze_datetime = freeze_datetime.add(seconds=2)

    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1


@contextmanager
def _grpc_server_external_repo(port: int, instance: DagsterInstance):
    server_process = open_server_process(
        instance_ref=instance.get_ref(),
        port=port,
        socket=None,
        loadable_target_origin=loadable_target_origin(),
    )
    try:
        location_origin: GrpcServerCodeLocationOrigin = GrpcServerCodeLocationOrigin(
            host="localhost", port=port, location_name="test_location"
        )
        with GrpcServerCodeLocation(origin=location_origin) as location:
            yield location.get_repository("the_repo")
    finally:
        DagsterGrpcClient(port=port, socket=None).shutdown_server()
        if server_process.poll() is None:
            wait_for_process(server_process, timeout=30)


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_skip_reason_schedule(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    freeze_datetime = feb_27_2019_start_of_day()
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("empty_schedule")

        schedule_origin = external_schedule.get_external_origin()

        instance.start_schedule(external_schedule)

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            freeze_datetime,
            TickStatus.SKIPPED,
            [],
            expected_skip_reason="Schedule function returned an empty result",
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_grpc_server_down(instance: DagsterInstance, executor: ThreadPoolExecutor):
    port = find_free_port()
    location_origin = GrpcServerCodeLocationOrigin(
        host="localhost", port=port, location_name="test_location"
    )
    schedule_origin = ExternalInstigatorOrigin(
        external_repository_origin=ExternalRepositoryOrigin(
            code_location_origin=location_origin,
            repository_name="the_repo",
        ),
        instigator_name="simple_schedule",
    )

    freeze_datetime = feb_27_2019_start_of_day()
    stack = ExitStack()
    external_repo = stack.enter_context(_grpc_server_external_repo(port, instance))
    workspace_context = stack.enter_context(
        create_test_daemon_workspace_context(
            GrpcServerTarget(
                host="localhost", port=port, socket=None, location_name="test_location"
            ),
            instance,
        )
    )
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        instance.start_schedule(external_schedule)
        # freeze the working workspace snapshot
        server_up_ctx = workspace_context.copy_for_test_instance(instance)

        # shut down the server
        stack.close()

        # Server is no longer running, ticks fail but indicate it will resume once it is reachable
        for _trial in range(3):
            evaluate_schedules(server_up_ctx, executor, pendulum.now("UTC"))
            assert instance.get_runs_count() == 0
            ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
            assert len(ticks) == 1

            validate_tick(
                ticks[0],
                external_schedule,
                freeze_datetime,
                TickStatus.FAILURE,
                [],
                (
                    "Unable to reach the user code server for schedule simple_schedule. Schedule"
                    " will resume execution once the server is available."
                ),
                expected_failure_count=0,
            )

        # Server starts back up, tick now succeeds
        with _grpc_server_external_repo(port, instance) as external_repo:
            evaluate_schedules(server_up_ctx, executor, pendulum.now("UTC"))
            assert instance.get_runs_count() == 1
            ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
            assert len(ticks) == 1

            expected_datetime = create_pendulum_time(year=2019, month=2, day=27)

            validate_tick(
                ticks[0],
                external_schedule,
                expected_datetime,
                TickStatus.SUCCESS,
                [run.run_id for run in instance.get_runs()],
            )


# Schedules with status defined in code have that status applied
@pytest.mark.parametrize("executor", get_schedule_executors())
def test_status_in_code_schedule(instance: DagsterInstance, executor: ThreadPoolExecutor):
    freeze_datetime = feb_27_2019_one_second_to_midnight()
    with create_test_daemon_workspace_context(
        workspace_load_target(attribute="the_status_in_code_repo"),
        instance,
    ) as workspace_context:
        code_location = next(
            iter(workspace_context.create_request_context().get_workspace_snapshot().values())
        ).code_location
        assert code_location
        external_repo = code_location.get_repository("the_status_in_code_repo")

        with pendulum.test(freeze_datetime):
            running_schedule = external_repo.get_external_schedule("always_running_schedule")
            not_running_schedule = external_repo.get_external_schedule("never_running_schedule")

            always_running_origin = running_schedule.get_external_origin()
            never_running_origin = not_running_schedule.get_external_origin()

            assert instance.get_runs_count() == 0
            assert (
                len(
                    instance.get_ticks(always_running_origin.get_id(), running_schedule.selector_id)
                )
                == 0
            )
            assert (
                len(
                    instance.get_ticks(
                        never_running_origin.get_id(), not_running_schedule.selector_id
                    )
                )
                == 0
            )

            assert len(instance.all_instigator_state()) == 0

            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

            # No runs, but the job state is updated to set a checkpoing
            assert instance.get_runs_count() == 0

            assert len(instance.all_instigator_state()) == 1

            instigator_state = instance.get_instigator_state(
                always_running_origin.get_id(), running_schedule.selector_id
            )
            assert instigator_state
            assert isinstance(instigator_state.instigator_data, ScheduleInstigatorData)

            assert instigator_state.status == InstigatorStatus.AUTOMATICALLY_RUNNING
            assert (
                instigator_state.instigator_data.start_timestamp == pendulum.now("UTC").timestamp()
            )

            ticks = instance.get_ticks(always_running_origin.get_id(), running_schedule.selector_id)
            assert len(ticks) == 0

            assert (
                len(
                    instance.get_ticks(
                        never_running_origin.get_id(), not_running_schedule.selector_id
                    )
                )
                == 0
            )

        freeze_datetime = freeze_datetime.add(seconds=2)
        with pendulum.test(freeze_datetime):
            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

            assert instance.get_runs_count() == 1

            assert (
                len(
                    instance.get_ticks(
                        never_running_origin.get_id(), not_running_schedule.selector_id
                    )
                )
                == 0
            )

            ticks = instance.get_ticks(always_running_origin.get_id(), running_schedule.selector_id)

            assert len(ticks) == 1

            expected_datetime = create_pendulum_time(year=2019, month=2, day=28)

            validate_tick(
                ticks[0],
                running_schedule,
                expected_datetime,
                TickStatus.SUCCESS,
                [run.run_id for run in instance.get_runs()],
            )

            wait_for_all_runs_to_start(instance)
            validate_run_started(
                instance,
                next(iter(instance.get_runs())),
                execution_time=create_pendulum_time(2019, 2, 28),
            )

            # Verify idempotence
            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
            assert instance.get_runs_count() == 1
            ticks = instance.get_ticks(always_running_origin.get_id(), running_schedule.selector_id)
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS

        freeze_datetime = freeze_datetime.add(days=1)
        with pendulum.test(freeze_datetime):
            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
            assert instance.get_runs_count() == 2
            ticks = instance.get_ticks(always_running_origin.get_id(), running_schedule.selector_id)
            assert len(ticks) == 2
            assert len([tick for tick in ticks if tick.status == TickStatus.SUCCESS]) == 2

        # Now try with an error workspace - the job state should not be deleted
        # since its associated with an errored out location
        with pendulum.test(freeze_datetime):
            workspace_context._location_entry_dict[  # noqa: SLF001
                "test_location"
            ] = workspace_context._location_entry_dict[  # noqa: SLF001
                "test_location"
            ]._replace(
                code_location=None,
                load_error=SerializableErrorInfo("error", [], "error"),
            )

            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
            ticks = instance.get_ticks(always_running_origin.get_id(), running_schedule.selector_id)
            assert len(ticks) == 2
            assert len(instance.all_instigator_state()) == 1

    # Now try with an empty workspace - ticks are still there, but the job state is deleted
    # once it's no longer present in the workspace
    with create_test_daemon_workspace_context(
        EmptyWorkspaceTarget(), instance
    ) as empty_workspace_ctx:
        with pendulum.test(freeze_datetime):
            evaluate_schedules(empty_workspace_ctx, executor, pendulum.now("UTC"))
            ticks = instance.get_ticks(always_running_origin.get_id(), running_schedule.selector_id)
            assert len(ticks) == 2
            assert len(instance.all_instigator_state()) == 0


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_change_default_status(instance: DagsterInstance, executor: ThreadPoolExecutor):
    # Simulate the case where a schedule previously had a default running status set, but is now changed back to default status stopped
    freeze_datetime = feb_27_2019_start_of_day()
    with create_test_daemon_workspace_context(
        workspace_load_target(attribute="the_status_in_code_repo"),
        instance,
    ) as workspace_context:
        code_location = next(
            iter(workspace_context.create_request_context().get_workspace_snapshot().values())
        ).code_location
        assert code_location
        external_repo = code_location.get_repository("the_status_in_code_repo")

        not_running_schedule = external_repo.get_external_schedule("never_running_schedule")

        never_running_origin = not_running_schedule.get_external_origin()

        # never_running_schedule used to have default status RUNNING
        schedule_state = InstigatorState(
            not_running_schedule.get_external_origin(),
            InstigatorType.SCHEDULE,
            InstigatorStatus.AUTOMATICALLY_RUNNING,
            ScheduleInstigatorData(
                not_running_schedule.cron_schedule,
                freeze_datetime.timestamp(),
            ),
        )
        instance.add_instigator_state(schedule_state)

        freeze_datetime = freeze_datetime.add(days=2)
        with pendulum.test(freeze_datetime):
            # Traveling two more days in the future before running results in two new ticks
            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

            ticks = instance.get_ticks(
                never_running_origin.get_id(), not_running_schedule.selector_id
            )
            assert len(ticks) == 0

            # AUTOMATICALLY_RUNNING row has been removed from the database
            instigator_state = instance.get_instigator_state(
                never_running_origin.get_id(), not_running_schedule.selector_id
            )
            assert not instigator_state

            # schedule can still be manually started

            schedule_state = InstigatorState(
                not_running_schedule.get_external_origin(),
                InstigatorType.SCHEDULE,
                InstigatorStatus.RUNNING,
                ScheduleInstigatorData(
                    not_running_schedule.cron_schedule,
                    freeze_datetime.timestamp(),
                ),
            )
            instance.add_instigator_state(schedule_state)

            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

            ticks = instance.get_ticks(
                never_running_origin.get_id(), not_running_schedule.selector_id
            )
            assert len(ticks) == 1
            assert len(ticks[0].run_ids) == 1
            assert ticks[0].timestamp == freeze_datetime.timestamp()
            assert ticks[0].status == TickStatus.SUCCESS


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_repository_namespacing(instance: DagsterInstance, executor):
    # ensure dupe schedules in different repos do not conflict on idempotence

    freeze_datetime = feb_27_2019_one_second_to_midnight()
    with create_test_daemon_workspace_context(
        workspace_load_target=workspace_load_target(attribute=None),  # load all repos
        instance=instance,
    ) as full_workspace_context:
        with pendulum.test(freeze_datetime):
            full_location = cast(
                CodeLocation,
                next(
                    iter(
                        full_workspace_context.create_request_context()
                        .get_workspace_snapshot()
                        .values()
                    )
                ).code_location,
            )
            external_repo = full_location.get_repository("the_repo")
            other_repo = full_location.get_repository("the_other_repo")

            # stop always on schedule
            status_in_code_repo = full_location.get_repository("the_status_in_code_repo")
            running_sched = status_in_code_repo.get_external_schedule("always_running_schedule")
            instance.stop_schedule(
                running_sched.get_external_origin_id(),
                running_sched.selector_id,
                running_sched,
            )

            external_schedule = external_repo.get_external_schedule("multi_run_list_schedule")
            schedule_origin = external_schedule.get_external_origin()
            instance.start_schedule(external_schedule)

            other_schedule = other_repo.get_external_schedule("multi_run_list_schedule")
            other_origin = external_schedule.get_external_origin()
            instance.start_schedule(other_schedule)

            assert instance.get_runs_count() == 0

            ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
            assert len(ticks) == 0

            ticks = instance.get_ticks(other_origin.get_id(), other_schedule.selector_id)
            assert len(ticks) == 0

            # launch_scheduled_runs does nothing before the first tick
            evaluate_schedules(full_workspace_context, executor, pendulum.now("UTC"))
            assert instance.get_runs_count() == 0

            ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
            assert len(ticks) == 0

            ticks = instance.get_ticks(other_origin.get_id(), other_schedule.selector_id)
            assert len(ticks) == 0

        freeze_datetime = freeze_datetime.add(seconds=2)
        with pendulum.test(freeze_datetime):
            evaluate_schedules(full_workspace_context, executor, pendulum.now("UTC"))

            assert (
                instance.get_runs_count() == 4
            )  # 2 from each copy of multi_run_schedule in each repo
            ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS

            ticks = instance.get_ticks(other_origin.get_id(), other_schedule.selector_id)
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS

            # Verify run idempotence by dropping ticks
            instance.purge_ticks(
                schedule_origin.get_id(),
                external_schedule.selector_id,
                pendulum.now("UTC").timestamp(),
            )
            instance.purge_ticks(
                other_origin.get_id(),
                other_schedule.selector_id,
                pendulum.now("UTC").timestamp(),
            )

            evaluate_schedules(full_workspace_context, executor, pendulum.now("UTC"))
            assert instance.get_runs_count() == 4  # still 4
            ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS

            ticks = instance.get_ticks(other_origin.get_id(), other_schedule.selector_id)
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_asset_selection(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    freeze_datetime = feb_27_2019_one_second_to_midnight()
    external_schedule = external_repo.get_external_schedule("asset_selection_schedule")
    schedule_origin = external_schedule.get_external_origin()

    with pendulum.test(freeze_datetime):
        instance.start_schedule(external_schedule)

        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)

        # launch_scheduled_runs does nothing before the first tick
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)

    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        expected_datetime = create_pendulum_time(year=2019, month=2, day=28)

        validate_tick(
            ticks[0],
            external_schedule,
            expected_datetime,
            TickStatus.SUCCESS,
            [run.run_id for run in instance.get_runs()],
        )

        wait_for_all_runs_to_start(instance)
        run = next(iter(instance.get_runs()))
        assert run.asset_selection == {AssetKey("asset1")}

        validate_run_started(instance, run, execution_time=create_pendulum_time(2019, 2, 28))


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_stale_asset_selection_never_materialized(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    freeze_datetime = feb_27_2019_one_second_to_midnight()
    external_schedule = external_repo.get_external_schedule("stale_asset_selection_schedule")

    with pendulum.test(freeze_datetime):
        instance.start_schedule(external_schedule)

    # never materialized so all assets stale
    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        wait_for_all_runs_to_start(instance)
        schedule_run = next((r for r in instance.get_runs() if r.job_name == "asset_job"), None)
        assert schedule_run is not None
        assert schedule_run.asset_selection == {AssetKey("asset1"), AssetKey("asset2")}
        validate_run_started(
            instance, schedule_run, execution_time=create_pendulum_time(2019, 2, 28)
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_stale_asset_selection_empty(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    freeze_datetime = feb_27_2019_one_second_to_midnight()
    external_schedule = external_repo.get_external_schedule("stale_asset_selection_schedule")

    with pendulum.test(freeze_datetime):
        instance.start_schedule(external_schedule)

    materialize([asset1, asset2], instance=instance)

    # assets previously materialized so we expect empy set
    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        wait_for_all_runs_to_start(instance)
        schedule_run = next((r for r in instance.get_runs() if r.job_name == "asset_job"), None)
        assert schedule_run is None


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_stale_asset_selection_subset(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    freeze_datetime = feb_27_2019_one_second_to_midnight()
    external_schedule = external_repo.get_external_schedule("stale_asset_selection_schedule")

    with pendulum.test(freeze_datetime):
        instance.start_schedule(external_schedule)

    materialize([asset1], instance=instance)

    # assets previously materialized so we expect empy set
    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        wait_for_all_runs_to_start(instance)
        schedule_run = next((r for r in instance.get_runs() if r.job_name == "asset_job"), None)
        assert schedule_run is not None
        assert schedule_run.asset_selection == {AssetKey("asset2")}
        validate_run_started(
            instance, schedule_run, execution_time=create_pendulum_time(2019, 2, 28)
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_source_asset_observation(
    instance: DagsterInstance, workspace_context, external_repo, executor
):
    freeze_datetime = feb_27_2019_one_second_to_midnight()
    external_schedule = external_repo.get_external_schedule("source_asset_observation_schedule")
    schedule_origin = external_schedule.get_external_origin()

    with pendulum.test(freeze_datetime):
        instance.start_schedule(external_schedule)

        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)

        # launch_scheduled_runs does nothing before the first tick
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)

    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        expected_datetime = create_pendulum_time(year=2019, month=2, day=28)

        validate_tick(
            ticks[0],
            external_schedule,
            expected_datetime,
            TickStatus.SUCCESS,
            [run.run_id for run in instance.get_runs()],
        )

        wait_for_all_runs_to_start(instance)
        run = next(iter(instance.get_runs()))
        assert run.asset_selection == {AssetKey("source_asset")}

        validate_run_started(instance, run, execution_time=create_pendulum_time(2019, 2, 28))


def test_settings():
    settings = {"use_threads": True, "num_workers": 4}
    with instance_for_test(overrides={"schedules": settings}) as thread_inst:
        assert thread_inst.get_settings("schedules") == settings
