import datetime
import random
import string
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import Dict, Optional, Sequence, cast

import pytest
from dagster import (
    Any,
    AssetExecutionContext,
    AssetKey,
    DefaultScheduleStatus,
    Field,
    ScheduleDefinition,
    StaticPartitionsDefinition,
    asset,
    build_schedule_from_partitioned_job,
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
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation import (
    CodeLocation,
    GrpcServerCodeLocation,
    GrpcServerCodeLocationOrigin,
    RemoteInstigatorOrigin,
    RemoteRepositoryOrigin,
)
from dagster._core.remote_representation.external import ExternalRepository, ExternalSchedule
from dagster._core.remote_representation.origin import ManagedGrpcPythonEnvCodeLocationOrigin
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
    BlockingThreadPoolExecutor,
    SingleThreadPoolExecutor,
    create_test_daemon_workspace_context,
    freeze_time,
    instance_for_test,
    wait_for_futures,
)
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import EmptyWorkspaceTarget, ModuleTarget
from dagster._daemon import get_default_daemon_logger
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.server import open_server_process
from dagster._record import copy
from dagster._scheduler.scheduler import ScheduleIterationTimes, launch_scheduled_runs
from dagster._time import create_datetime, get_current_datetime, get_current_timestamp, get_timezone
from dagster._utils import DebugCrashFlags
from dagster._utils.error import SerializableErrorInfo
from dagster._utils.partitions import DEFAULT_DATE_FORMAT
from dagster._vendored.dateutil.relativedelta import relativedelta

from dagster_tests.scheduler_tests.conftest import loadable_target_origin, workspace_load_target


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


FUTURES_TIMEOUT = 75


def evaluate_schedules(
    workspace_context: WorkspaceProcessContext,
    executor: Optional[ThreadPoolExecutor],
    end_datetime_utc: datetime.datetime,
    max_tick_retries: int = 0,
    max_catchup_runs: int = DEFAULT_MAX_CATCHUP_RUNS,
    debug_crash_flags: Optional[DebugCrashFlags] = None,
    timeout: int = FUTURES_TIMEOUT,
    submit_executor: Optional[ThreadPoolExecutor] = None,
    iteration_times: Optional[Dict[str, ScheduleIterationTimes]] = None,
):
    logger = get_default_daemon_logger("SchedulerDaemon")
    futures = {}
    iteration_times = iteration_times or {}

    list(
        launch_scheduled_runs(
            workspace_context,
            logger,
            end_datetime_utc,
            iteration_times=iteration_times,
            threadpool_executor=executor,
            scheduler_run_futures=futures,
            max_tick_retries=max_tick_retries,
            max_catchup_runs=max_catchup_runs,
            debug_crash_flags=debug_crash_flags,
            submit_threadpool_executor=submit_executor,
        )
    )

    iteration_times = {**iteration_times, **wait_for_futures(futures, timeout=timeout)}

    return iteration_times


@op(config_schema={"time": str})
def the_op(context):
    return "Ran at this time: {}".format(context.op_config["time"])


@job
def the_job():
    the_op()


def _op_config(date: datetime.datetime):
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


@schedule(
    job_name="the_job",
    cron_schedule="0 0 * * *",
    execution_timezone="UTC",
)
def many_requests_schedule(context):
    REQUEST_COUNT = 15

    return [
        RunRequest(run_key=str(i), run_config=_op_config(context.scheduled_execution_time))
        for i in range(REQUEST_COUNT)
    ]


def define_multi_run_schedule():
    def gen_runs(context):
        if not context.scheduled_execution_time:
            date = get_current_datetime() - relativedelta(days=1)
        else:
            date = context.scheduled_execution_time - relativedelta(days=1)

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
        date = get_current_datetime() - relativedelta(days=1)
    else:
        date = context.scheduled_execution_time - relativedelta(days=1)

    return [
        RunRequest(run_key="A", run_config=_op_config(date), tags={"label": "A"}),
        RunRequest(run_key="B", run_config=_op_config(date), tags={"label": "B"}),
    ]


def define_multi_run_schedule_with_missing_run_key():
    def gen_runs(context):
        if not context.scheduled_execution_time:
            date = get_current_datetime() - relativedelta(days=1)
        else:
            date = context.scheduled_execution_time - relativedelta(days=1)

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


static_partition_def = StaticPartitionsDefinition(["a", "b", "c"])


@asset(partitions_def=static_partition_def)
def static_partitioned_asset1(context: AssetExecutionContext):
    return f"static_partitioned_asset1[{context.partition_key}]"


static_partitioned_asset1_schedule = build_schedule_from_partitioned_job(
    name="static_partitioned_asset1_schedule",
    job=define_asset_job(
        "static_paritioned_asset1_job",
        selection=[static_partitioned_asset1],
        partitions_def=static_partition_def,
    ),
    cron_schedule="* * * * *",
)


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
        many_requests_schedule,
        [asset1, asset2, source_asset],
        asset_selection_schedule,
        stale_asset_selection_schedule,
        source_asset_observation_schedule,
        static_partitioned_asset1,
        static_partitioned_asset1_schedule,
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
    cron_schedule=["@daily", "0 0 * * 5"],
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
    expected_datetime: datetime.datetime,
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
    assert (
        run.tags[SCHEDULED_EXECUTION_TIME_TAG]
        == execution_time.astimezone(datetime.timezone.utc).isoformat()
    )

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


def feb_27_2019_one_second_to_midnight() -> datetime.datetime:
    return create_datetime(year=2019, month=2, day=27, hour=23, minute=59, second=59).astimezone(
        get_timezone("US/Central")
    )


def feb_27_2019_start_of_day() -> datetime.datetime:
    return create_datetime(year=2019, month=2, day=27, hour=0, minute=0, second=0).astimezone(
        get_timezone("US/Central")
    )


def _get_unloadable_schedule_origin():
    load_target = workspace_load_target()
    return RemoteRepositoryOrigin(
        load_target.create_origins()[0], "fake_repository"
    ).get_instigator_origin("doesnt_exist")


def _get_unloadable_workspace_load_target():
    return ModuleTarget(
        module_name="doesnt_exist_module",
        attribute=None,
        location_name="unloadable_location",
        working_directory=None,
    )


def test_settings():
    settings = {"use_threads": True, "num_workers": 4}
    with instance_for_test(overrides={"schedules": settings}) as thread_inst:
        assert thread_inst.get_settings("schedules") == settings


@contextmanager
def _grpc_server_external_repo(port: int, scheduler_instance: DagsterInstance):
    server_process = open_server_process(
        instance_ref=scheduler_instance.get_ref(),
        port=port,
        socket=None,
        loadable_target_origin=loadable_target_origin(),
    )
    try:
        location_origin: GrpcServerCodeLocationOrigin = GrpcServerCodeLocationOrigin(
            host="localhost", port=port, location_name="test_location"
        )
        with GrpcServerCodeLocation(
            origin=location_origin, instance=scheduler_instance
        ) as location:
            yield location.get_repository("the_repo")
    finally:
        DagsterGrpcClient(port=port, socket=None).shutdown_server()
        if server_process.poll() is None:
            server_process.communicate(timeout=30)


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_error_load_code_location(instance: DagsterInstance, executor: ThreadPoolExecutor):
    with create_test_daemon_workspace_context(
        _get_unloadable_workspace_load_target(), instance
    ) as workspace_context:
        fake_origin = _get_unloadable_schedule_origin()
        freeze_datetime = feb_27_2019_one_second_to_midnight()
        with freeze_time(freeze_datetime):
            schedule_state = InstigatorState(
                fake_origin,
                InstigatorType.SCHEDULE,
                InstigatorStatus.RUNNING,
                ScheduleInstigatorData("0 0 * * *", get_current_timestamp()),
            )
            instance.add_instigator_state(schedule_state)

        freeze_datetime = freeze_datetime + relativedelta(seconds=1)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert instance.get_runs_count() == 0

            ticks = instance.get_ticks(fake_origin.get_id(), schedule_state.selector_id)

            assert len(ticks) == 0

        freeze_datetime = freeze_datetime + relativedelta(days=1)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert instance.get_runs_count() == 0
            ticks = instance.get_ticks(fake_origin.get_id(), schedule_state.selector_id)
            assert len(ticks) == 0


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

        with freeze_time(freeze_datetime):
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

            evaluate_schedules(workspace_context, executor, get_current_datetime())

            # No runs, but the job state is updated to set a checkpoing
            assert instance.get_runs_count() == 0

            assert len(instance.all_instigator_state()) == 1

            instigator_state = instance.get_instigator_state(
                always_running_origin.get_id(), running_schedule.selector_id
            )
            assert instigator_state
            assert isinstance(instigator_state.instigator_data, ScheduleInstigatorData)

            assert instigator_state.status == InstigatorStatus.DECLARED_IN_CODE
            assert instigator_state.instigator_data.start_timestamp == get_current_timestamp()

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

            # The instigator state status can be manually updated, as well as reset.
            instance.stop_schedule(
                always_running_origin.get_id(), running_schedule.selector_id, running_schedule
            )
            stopped_instigator_state = instance.get_instigator_state(
                always_running_origin.get_id(), running_schedule.selector_id
            )

            assert stopped_instigator_state
            assert stopped_instigator_state.status == InstigatorStatus.STOPPED

            instance.reset_schedule(running_schedule)
            reset_instigator_state = instance.get_instigator_state(
                always_running_origin.get_id(), running_schedule.selector_id
            )

            assert reset_instigator_state
            assert reset_instigator_state.status == InstigatorStatus.DECLARED_IN_CODE

            running_to_not_running_schedule = ExternalSchedule(
                external_schedule_data=copy(
                    running_schedule._external_schedule_data,  # noqa: SLF001
                    default_status=DefaultScheduleStatus.STOPPED,
                ),
                handle=running_schedule.handle.repository_handle,
            )
            current_state = running_to_not_running_schedule.get_current_instigator_state(
                stored_state=reset_instigator_state
            )

            assert current_state.status == InstigatorStatus.STOPPED
            assert current_state.instigator_data == reset_instigator_state.instigator_data

        freeze_datetime = freeze_datetime + relativedelta(seconds=2)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())

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

            expected_datetime = create_datetime(year=2019, month=2, day=28)

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
                execution_time=create_datetime(2019, 2, 28),
            )

            # Verify idempotence
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert instance.get_runs_count() == 1
            ticks = instance.get_ticks(always_running_origin.get_id(), running_schedule.selector_id)
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS

        freeze_datetime = freeze_datetime + relativedelta(days=1)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert instance.get_runs_count() == 2
            ticks = instance.get_ticks(always_running_origin.get_id(), running_schedule.selector_id)
            assert len(ticks) == 2
            assert len([tick for tick in ticks if tick.status == TickStatus.SUCCESS]) == 2

        # Now try with an error workspace - the job state should not be deleted
        # since its associated with an errored out location
        with freeze_time(freeze_datetime):
            workspace_context._location_entry_dict[  # noqa: SLF001
                "test_location"
            ] = workspace_context._location_entry_dict["test_location"]._replace(  # noqa: SLF001
                code_location=None,
                load_error=SerializableErrorInfo("error", [], "error"),
            )

            evaluate_schedules(workspace_context, executor, get_current_datetime())
            ticks = instance.get_ticks(always_running_origin.get_id(), running_schedule.selector_id)
            assert len(ticks) == 2
            assert len(instance.all_instigator_state()) == 1

    # Now try with an empty workspace - ticks are still there, but the job state is deleted
    # once it's no longer present in the workspace
    with create_test_daemon_workspace_context(
        EmptyWorkspaceTarget(), instance
    ) as empty_workspace_ctx:
        with freeze_time(freeze_datetime):
            evaluate_schedules(empty_workspace_ctx, executor, get_current_datetime())
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
            InstigatorStatus.DECLARED_IN_CODE,
            ScheduleInstigatorData(
                not_running_schedule.cron_schedule,
                freeze_datetime.timestamp(),
            ),
        )
        instance.add_instigator_state(schedule_state)

        freeze_datetime = freeze_datetime + relativedelta(days=2)
        with freeze_time(freeze_datetime):
            # Traveling two more days in the future before running results in two new ticks
            evaluate_schedules(workspace_context, executor, get_current_datetime())

            ticks = instance.get_ticks(
                never_running_origin.get_id(), not_running_schedule.selector_id
            )
            assert len(ticks) == 0

            # DECLARED_IN_CODE row has been removed from the database
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

            evaluate_schedules(workspace_context, executor, get_current_datetime())

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
        with freeze_time(freeze_datetime):
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
            evaluate_schedules(full_workspace_context, executor, get_current_datetime())
            assert instance.get_runs_count() == 0

            ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
            assert len(ticks) == 0

            ticks = instance.get_ticks(other_origin.get_id(), other_schedule.selector_id)
            assert len(ticks) == 0

        freeze_datetime = freeze_datetime + relativedelta(seconds=2)
        with freeze_time(freeze_datetime):
            evaluate_schedules(full_workspace_context, executor, get_current_datetime())

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
                get_current_timestamp(),
            )
            instance.purge_ticks(
                other_origin.get_id(),
                other_schedule.selector_id,
                get_current_timestamp(),
            )

            evaluate_schedules(full_workspace_context, executor, get_current_datetime())
            assert instance.get_runs_count() == 4  # still 4
            ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS

            ticks = instance.get_ticks(other_origin.get_id(), other_schedule.selector_id)
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS


def test_stale_request_context(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
):
    freeze_datetime = feb_27_2019_start_of_day()
    with freeze_time(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("many_requests_schedule")

        schedule_origin = external_schedule.get_external_origin()

        instance.start_schedule(external_schedule)
        executor = ThreadPoolExecutor()
        blocking_executor = BlockingThreadPoolExecutor()

        futures = {}
        iteration_times = {}
        list(
            launch_scheduled_runs(
                workspace_context,
                get_default_daemon_logger("SchedulerDaemon"),
                get_current_datetime(),
                iteration_times=iteration_times,
                threadpool_executor=executor,
                scheduler_run_futures=futures,
                submit_threadpool_executor=blocking_executor,
            )
        )

        # Reload the workspace (and kill previous server) before unblocking the threads.
        # This will cause failures if the threads do not refresh their request contexts.
        p = workspace_context._grpc_server_registry._all_processes[0]  # noqa: SLF001
        workspace_context.reload_workspace()
        p.server_process.kill()
        p.wait()
        blocking_executor.allow()
        wait_for_futures(futures, timeout=FUTURES_TIMEOUT)

        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        runs = instance.get_runs()
        assert len(runs) == 15, ticks[0].error
        validate_tick(
            ticks[0],
            external_schedule,
            freeze_datetime,
            TickStatus.SUCCESS,
            [run.run_id for run in runs],
        )


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
    ) as scheduler_instance:
        external_schedule = external_repo.get_external_schedule("simple_schedule")

        schedule_origin = external_schedule.get_external_origin()
        freeze_datetime = feb_27_2019_start_of_day()
        with freeze_time(freeze_datetime):
            exploding_ctx = workspace_context.copy_for_test_instance(scheduler_instance)
            scheduler_instance.start_schedule(external_schedule)

            evaluate_schedules(exploding_ctx, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 1

            run = next(iter(scheduler_instance.get_runs()))

            validate_run_started(
                scheduler_instance,
                run,
                execution_time=freeze_datetime,
                expected_success=False,
            )

            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_schedule,
                freeze_datetime,
                TickStatus.SUCCESS,
                [run.run_id for run in scheduler_instance.get_runs()],
            )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_schedule_mutation(
    instance: DagsterInstance,
    workspace_one: WorkspaceProcessContext,
    workspace_two: WorkspaceProcessContext,
    executor: ThreadPoolExecutor,
):
    repo_one = next(
        iter(workspace_one.create_request_context().get_workspace_snapshot().values())
    ).code_location.get_repository(  # type: ignore
        "the_repo"
    )
    repo_two = next(
        iter(workspace_two.create_request_context().get_workspace_snapshot().values())
    ).code_location.get_repository(  # type: ignore
        "the_repo"
    )
    schedule_one = repo_one.get_external_schedule("simple_schedule")
    origin_one = schedule_one.get_external_origin()
    assert schedule_one.cron_schedule == "0 2 * * *"
    schedule_two = repo_two.get_external_schedule("simple_schedule")
    origin_two = schedule_two.get_external_origin()
    assert schedule_two.cron_schedule == "0 1 * * *"

    assert schedule_one.selector_id == schedule_two.selector_id

    freeze_datetime = create_datetime(year=2023, month=2, day=1)
    with freeze_time(freeze_datetime):
        # start the schedule at 12:00 AM, it is scheduled to go at 2:00 AM
        instance.start_schedule(schedule_one)
        evaluate_schedules(workspace_one, executor, get_current_datetime())
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(origin_one.get_id(), schedule_one.selector_id)
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime + relativedelta(hours=1, minutes=59)
    with freeze_time(freeze_datetime):
        # now check the schedule at 1:59 AM, where the schedule is not to fire until 2:00 AM
        evaluate_schedules(workspace_one, executor, get_current_datetime())
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(origin_one.get_id(), schedule_one.selector_id)
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime + relativedelta(minutes=1)
    with freeze_time(freeze_datetime):
        # Now change the schedule to be at 1:00 AM.  It should not generate a tick because we last
        # evaluated at 1:59AM and it is now 2:00 AM. We expect the new schedule to wait until
        # tomorrow to create a new tick.
        evaluate_schedules(workspace_two, executor, get_current_datetime())
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(origin_two.get_id(), schedule_two.selector_id)
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime + relativedelta(hours=23)
    with freeze_time(freeze_datetime):
        evaluate_schedules(workspace_two, executor, get_current_datetime())
        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(origin_two.get_id(), schedule_two.selector_id)
        assert len(ticks) == 1


class TestSchedulerRun:
    @pytest.fixture
    def scheduler_instance(self, instance):
        return instance

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_simple_schedule(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        freeze_datetime = feb_27_2019_one_second_to_midnight()
        with freeze_time(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("simple_schedule")

            schedule_origin = external_schedule.get_external_origin()

            scheduler_instance.start_schedule(external_schedule)

            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 0

            # launch_scheduled_runs does nothing before the first tick
            iteration_times = evaluate_schedules(
                workspace_context, executor, get_current_datetime()
            )

            assert len(iteration_times) == 1
            assert (
                iteration_times[external_schedule.selector_id].cron_schedule
                == external_schedule.cron_schedule
            )
            assert (
                iteration_times[external_schedule.selector_id].next_iteration_timestamp
                == freeze_datetime.timestamp() + 1
            )

            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 0

        freeze_datetime = freeze_datetime + relativedelta(seconds=2)
        with freeze_time(freeze_datetime):
            new_iteration_times = evaluate_schedules(
                workspace_context,
                executor,
                get_current_datetime(),
                iteration_times=iteration_times,
            )

            assert len(new_iteration_times) == 1
            assert (
                new_iteration_times[external_schedule.selector_id].cron_schedule
                == external_schedule.cron_schedule
            )

            # Next iteration is planned for between 1 and 2 hours from now due to random jitter

            assert (
                new_iteration_times[external_schedule.selector_id].next_iteration_timestamp
                > freeze_datetime.timestamp()
            )
            assert (
                new_iteration_times[external_schedule.selector_id].next_iteration_timestamp
                < freeze_datetime.timestamp() + 3600 * 2
            )

            assert scheduler_instance.get_runs_count() == 1
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1

            expected_datetime = create_datetime(year=2019, month=2, day=28)

            validate_tick(
                ticks[0],
                external_schedule,
                expected_datetime,
                TickStatus.SUCCESS,
                [run.run_id for run in scheduler_instance.get_runs()],
            )

            wait_for_all_runs_to_start(scheduler_instance)
            validate_run_started(
                scheduler_instance,
                next(iter(scheduler_instance.get_runs())),
                execution_time=create_datetime(2019, 2, 28),
            )

            # Verify idempotence

            assert new_iteration_times == evaluate_schedules(
                workspace_context,
                executor,
                get_current_datetime(),
                iteration_times=new_iteration_times,
            )

            assert scheduler_instance.get_runs_count() == 1
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS

        # Verify advancing in time but not going past a tick doesn't add any new runs
        freeze_datetime = freeze_datetime + relativedelta(seconds=2)
        with freeze_time(freeze_datetime):
            assert new_iteration_times == evaluate_schedules(
                workspace_context,
                executor,
                get_current_datetime(),
                iteration_times=new_iteration_times,
            )

            assert scheduler_instance.get_runs_count() == 1
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS

        freeze_datetime = freeze_datetime + relativedelta(days=2)
        with freeze_time(freeze_datetime):
            # Traveling two more days in the future passes two ticks times, but only the most recent
            # will be created as a tick with a corresponding run.
            new_iteration_times = evaluate_schedules(
                workspace_context,
                executor,
                get_current_datetime(),
                iteration_times=new_iteration_times,
            )
            assert new_iteration_times

            assert len(new_iteration_times) == 1
            assert (
                new_iteration_times[external_schedule.selector_id].cron_schedule
                == external_schedule.cron_schedule
            )
            assert (
                new_iteration_times[external_schedule.selector_id].next_iteration_timestamp
                >= freeze_datetime.timestamp() + 3600
            )

            assert scheduler_instance.get_runs_count() == 2
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 2
            assert len([tick for tick in ticks if tick.status == TickStatus.SUCCESS]) == 2

            # Check idempotence again
            assert new_iteration_times == evaluate_schedules(
                workspace_context,
                executor,
                get_current_datetime(),
                iteration_times=new_iteration_times,
            )
            assert scheduler_instance.get_runs_count() == 2
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 2

    # Verify that the scheduler uses selector and not origin to dedupe schedules
    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_schedule_with_different_origin(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        existing_origin = external_schedule.get_external_origin()

        code_location_origin = existing_origin.repository_origin.code_location_origin
        assert isinstance(code_location_origin, ManagedGrpcPythonEnvCodeLocationOrigin)
        modified_loadable_target_origin = code_location_origin.loadable_target_origin._replace(
            executable_path="/different/executable_path"
        )

        # Change metadata on the origin that shouldn't matter for execution
        modified_origin = existing_origin._replace(
            repository_origin=existing_origin.repository_origin._replace(
                code_location_origin=code_location_origin._replace(
                    loadable_target_origin=modified_loadable_target_origin
                )
            )
        )

        freeze_datetime = feb_27_2019_one_second_to_midnight()
        with freeze_time(freeze_datetime):
            schedule_state = InstigatorState(
                modified_origin,
                InstigatorType.SCHEDULE,
                InstigatorStatus.RUNNING,
                ScheduleInstigatorData(external_schedule.cron_schedule, get_current_timestamp()),
            )
            scheduler_instance.add_instigator_state(schedule_state)

            freeze_datetime = freeze_datetime + relativedelta(seconds=2)

        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 1
            ticks = scheduler_instance.get_ticks(
                existing_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_old_tick_schedule(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        freeze_datetime = feb_27_2019_one_second_to_midnight()
        with freeze_time(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("simple_schedule")

            # Create an old tick from several days ago
            scheduler_instance.create_tick(
                TickData(
                    instigator_origin_id=external_schedule.get_external_origin_id(),
                    instigator_name="simple_schedule",
                    instigator_type=InstigatorType.SCHEDULE,
                    status=TickStatus.STARTED,
                    timestamp=(get_current_datetime() - relativedelta(days=3)).timestamp(),
                    selector_id=external_schedule.selector_id,
                )
            )

            schedule_origin = external_schedule.get_external_origin()
            scheduler_instance.start_schedule(external_schedule)

        freeze_datetime = freeze_datetime + relativedelta(seconds=2)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 1
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 2

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_no_started_schedules(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        schedule_origin = external_schedule.get_external_origin()

        evaluate_schedules(workspace_context, executor, get_current_datetime())
        assert scheduler_instance.get_runs_count() == 0

        ticks = scheduler_instance.get_ticks(
            schedule_origin.get_id(), external_schedule.selector_id
        )
        assert len(ticks) == 0

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_schedule_without_timezone(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        executor: ThreadPoolExecutor,
    ):
        code_location = next(
            iter(workspace_context.create_request_context().get_workspace_snapshot().values())
        ).code_location
        assert code_location is not None
        external_repo = code_location.get_repository("the_repo")
        external_schedule = external_repo.get_external_schedule("simple_schedule_no_timezone")
        schedule_origin = external_schedule.get_external_origin()
        initial_datetime = create_datetime(year=2019, month=2, day=27, hour=0, minute=0, second=0)

        with freeze_time(initial_datetime):
            scheduler_instance.start_schedule(external_schedule)

            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 1

            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )

            assert len(ticks) == 1

            expected_datetime = create_datetime(year=2019, month=2, day=27)

            validate_tick(
                ticks[0],
                external_schedule,
                expected_datetime,
                TickStatus.SUCCESS,
                [run.run_id for run in scheduler_instance.get_runs()],
            )

            wait_for_all_runs_to_start(scheduler_instance)
            validate_run_started(
                scheduler_instance,
                next(iter(scheduler_instance.get_runs())),
                execution_time=expected_datetime,
            )

            # Verify idempotence
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert scheduler_instance.get_runs_count() == 1
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_bad_eval_fn_no_retries(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        external_schedule = external_repo.get_external_schedule("wrong_config_schedule")
        schedule_origin = external_schedule.get_external_origin()
        freeze_datetime = create_datetime(year=2019, month=2, day=27, hour=0, minute=0, second=0)
        with freeze_time(freeze_datetime):
            scheduler_instance.start_schedule(external_schedule)

            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1

            validate_tick(
                ticks[0],
                external_schedule,
                freeze_datetime,
                TickStatus.FAILURE,
                [run.run_id for run in scheduler_instance.get_runs()],
                "DagsterInvalidConfigError",
                expected_failure_count=1,
            )

            # Idempotency (tick does not retry)
            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
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

        freeze_datetime = freeze_datetime + relativedelta(days=1)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
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
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        external_schedule = external_repo.get_external_schedule("wrong_config_schedule")
        schedule_origin = external_schedule.get_external_origin()
        freeze_datetime = create_datetime(year=2019, month=2, day=27, hour=0, minute=0, second=0)
        with freeze_time(freeze_datetime):
            scheduler_instance.start_schedule(external_schedule)

            evaluate_schedules(
                workspace_context, executor, get_current_datetime(), max_tick_retries=2
            )

            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
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

            evaluate_schedules(
                workspace_context, executor, get_current_datetime(), max_tick_retries=2
            )
            evaluate_schedules(
                workspace_context, executor, get_current_datetime(), max_tick_retries=2
            )

            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
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

            evaluate_schedules(
                workspace_context, executor, get_current_datetime(), max_tick_retries=2
            )
            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
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

        freeze_datetime = freeze_datetime + relativedelta(days=1)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
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
        self,
        scheduler_instance: DagsterInstance,
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
        freeze_datetime = create_datetime(year=2019, month=2, day=27, hour=0, minute=0, second=0)
        with freeze_time(freeze_datetime):
            scheduler_instance.start_schedule(external_schedule)

        expected_schedule_time = freeze_datetime
        freeze_datetime = freeze_datetime + relativedelta(seconds=2)

        with freeze_time(freeze_datetime):
            iteration_times = evaluate_schedules(
                workspace_context, executor, get_current_datetime(), max_tick_retries=1
            )

            assert len(iteration_times) == 1
            assert (
                iteration_times[external_schedule.selector_id].next_iteration_timestamp
                == expected_schedule_time.timestamp()
            )
            assert (
                iteration_times[external_schedule.selector_id].last_iteration_timestamp
                == expected_schedule_time.timestamp()
            )

            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1

            validate_tick(
                ticks[0],
                external_schedule,
                expected_schedule_time,
                TickStatus.FAILURE,
                [],
                f"Error occurred during the evaluation of schedule {schedule_name}",
                expected_failure_count=1,
            )

            new_iteration_times = evaluate_schedules(
                workspace_context,
                executor,
                get_current_datetime(),
                max_tick_retries=1,
                iteration_times=iteration_times,
            )

            assert len(new_iteration_times) == 1
            assert (
                new_iteration_times[external_schedule.selector_id].next_iteration_timestamp
                > freeze_datetime.timestamp()
            )
            assert (
                new_iteration_times[external_schedule.selector_id].last_iteration_timestamp
                == freeze_datetime.timestamp()
            )

            assert scheduler_instance.get_runs_count() == 1
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1

            validate_tick(
                ticks[0],
                external_schedule,
                expected_schedule_time,
                TickStatus.SUCCESS,
                [run.run_id for run in scheduler_instance.get_runs()],
                expected_failure_count=1,
            )

        freeze_datetime = freeze_datetime + relativedelta(days=1)
        expected_schedule_time = expected_schedule_time + relativedelta(days=1)
        with freeze_time(freeze_datetime):
            evaluate_schedules(
                workspace_context, executor, get_current_datetime(), max_tick_retries=1
            )

            assert scheduler_instance.get_runs_count() == 2
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 2

            validate_tick(
                ticks[0],
                external_schedule,
                expected_schedule_time,
                TickStatus.SUCCESS,
                [next(iter(scheduler_instance.get_runs())).run_id],
                expected_failure_count=0,
            )

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_bad_should_execute(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        external_schedule = external_repo.get_external_schedule("bad_should_execute_schedule")
        schedule_origin = external_schedule.get_external_origin()
        initial_datetime = create_datetime(
            year=2019,
            month=2,
            day=27,
            hour=0,
            minute=0,
            second=0,
        )
        with freeze_time(initial_datetime):
            scheduler_instance.start_schedule(external_schedule)

            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1

            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                TickStatus.FAILURE,
                [run.run_id for run in scheduler_instance.get_runs()],
                "Error occurred during the execution of should_execute for schedule"
                " bad_should_execute_schedule",
                expected_failure_count=1,
            )

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_skip(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        external_schedule = external_repo.get_external_schedule("skip_schedule")
        schedule_origin = external_schedule.get_external_origin()
        freeze_datetime = feb_27_2019_start_of_day()
        with freeze_time(freeze_datetime):
            scheduler_instance.start_schedule(external_schedule)

            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_schedule,
                freeze_datetime,
                TickStatus.SKIPPED,
                [run.run_id for run in scheduler_instance.get_runs()],
                expected_skip_reason="should_execute function for skip_schedule returned false.",
            )

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_wrong_config_schedule(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        external_schedule = external_repo.get_external_schedule("wrong_config_schedule")
        schedule_origin = external_schedule.get_external_origin()
        freeze_datetime = create_datetime(year=2019, month=2, day=27, hour=0, minute=0, second=0)
        with freeze_time(freeze_datetime):
            scheduler_instance.start_schedule(external_schedule)

            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 0

            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
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
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        external_schedule = external_repo.get_external_schedule("default_config_schedule")
        schedule_origin = external_schedule.get_external_origin()
        initial_datetime = create_datetime(year=2019, month=2, day=27, hour=0, minute=0, second=0)
        with freeze_time(initial_datetime):
            scheduler_instance.start_schedule(external_schedule)

            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 1

            wait_for_all_runs_to_start(scheduler_instance)

            run = next(iter(scheduler_instance.get_runs()))

            validate_run_started(
                scheduler_instance,
                run,
                execution_time=initial_datetime,
                expected_success=True,
            )

            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                TickStatus.SUCCESS,
                [run.run_id for run in scheduler_instance.get_runs()],
            )

            assert scheduler_instance.run_launcher.did_run_launch(run.run_id)  # type: ignore  # (unspecified scheduler_instance subclass)

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_static_partitioned_asset_schedule_run(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        external_schedule = external_repo.get_external_schedule(
            "static_partitioned_asset1_schedule"
        )
        initial_datetime = create_datetime(year=2019, month=2, day=27, hour=0, minute=0, second=0)
        with freeze_time(initial_datetime):
            scheduler_instance.start_schedule(external_schedule)

            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 3

            wait_for_all_runs_to_start(scheduler_instance)

            runs = scheduler_instance.get_runs()
            assert len(runs) == 3

            for key in static_partition_def.get_partition_keys():
                assert any(r.tags[PARTITION_NAME_TAG] == key for r in runs)

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_bad_schedules_mixed_with_good_schedule(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        good_schedule = external_repo.get_external_schedule("simple_schedule")
        bad_schedule = external_repo.get_external_schedule(
            "bad_should_execute_on_odd_days_schedule"
        )

        good_origin = good_schedule.get_external_origin()
        bad_origin = bad_schedule.get_external_origin()
        unloadable_origin = _get_unloadable_schedule_origin()
        freeze_datetime = feb_27_2019_start_of_day()
        with freeze_time(freeze_datetime):
            scheduler_instance.start_schedule(good_schedule)
            scheduler_instance.start_schedule(bad_schedule)

            unloadable_schedule_state = InstigatorState(
                unloadable_origin,
                InstigatorType.SCHEDULE,
                InstigatorStatus.RUNNING,
                ScheduleInstigatorData("0 0 * * *", get_current_timestamp()),
            )
            scheduler_instance.add_instigator_state(unloadable_schedule_state)

            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 1
            wait_for_all_runs_to_start(scheduler_instance)
            validate_run_started(
                scheduler_instance,
                next(iter(scheduler_instance.get_runs())),
                execution_time=freeze_datetime,
            )

            good_ticks = scheduler_instance.get_ticks(
                good_origin.get_id(), good_schedule.selector_id
            )
            assert len(good_ticks) == 1
            validate_tick(
                good_ticks[0],
                good_schedule,
                freeze_datetime,
                TickStatus.SUCCESS,
                [run.run_id for run in scheduler_instance.get_runs()],
            )

            bad_ticks = scheduler_instance.get_ticks(bad_origin.get_id(), bad_schedule.selector_id)
            assert len(bad_ticks) == 1

            assert bad_ticks[0].status == TickStatus.FAILURE

            assert (
                "Error occurred during the execution of should_execute for schedule bad_should_execute_on_odd_days_schedule"
                in bad_ticks[0].error.message  # type: ignore  # (possible none)
            )

            unloadable_ticks = scheduler_instance.get_ticks(
                unloadable_origin.get_id(), "fake_selector"
            )
            assert len(unloadable_ticks) == 0

        freeze_datetime = freeze_datetime + relativedelta(days=1)
        with freeze_time(freeze_datetime):
            new_now = get_current_datetime()
            evaluate_schedules(workspace_context, executor, new_now)

            assert scheduler_instance.get_runs_count() == 3
            wait_for_all_runs_to_start(scheduler_instance)

            good_schedule_runs = scheduler_instance.get_runs(
                filters=RunsFilter.for_schedule(good_schedule)
            )
            assert len(good_schedule_runs) == 2
            validate_run_started(
                scheduler_instance,
                good_schedule_runs[0],
                execution_time=new_now,
            )

            good_ticks = scheduler_instance.get_ticks(
                good_origin.get_id(), good_schedule.selector_id
            )
            assert len(good_ticks) == 2
            validate_tick(
                good_ticks[0],
                good_schedule,
                new_now,
                TickStatus.SUCCESS,
                [good_schedule_runs[0].run_id],
            )

            bad_schedule_runs = scheduler_instance.get_runs(
                filters=RunsFilter.for_schedule(bad_schedule)
            )
            assert len(bad_schedule_runs) == 1
            validate_run_started(
                scheduler_instance,
                bad_schedule_runs[0],
                execution_time=new_now,
            )

            bad_ticks = scheduler_instance.get_ticks(bad_origin.get_id(), bad_schedule.selector_id)
            assert len(bad_ticks) == 2
            validate_tick(
                bad_ticks[0],
                bad_schedule,
                new_now,
                TickStatus.SUCCESS,
                [bad_schedule_runs[0].run_id],
            )

            unloadable_ticks = scheduler_instance.get_ticks(
                unloadable_origin.get_id(), "fake_selector"
            )
            assert len(unloadable_ticks) == 0

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_run_scheduled_on_time_boundary(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        external_schedule = external_repo.get_external_schedule("simple_schedule")

        schedule_origin = external_schedule.get_external_origin()
        freeze_datetime = feb_27_2019_start_of_day()  # 00:00:00
        with freeze_time(freeze_datetime):
            # Start schedule exactly at midnight
            scheduler_instance.start_schedule(external_schedule)

            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 1
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_bad_load_repository(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        freeze_datetime = feb_27_2019_one_second_to_midnight()
        with freeze_time(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("simple_schedule")
            valid_schedule_origin = external_schedule.get_external_origin()

            # Swap out a new repository name
            invalid_repo_origin = RemoteInstigatorOrigin(
                RemoteRepositoryOrigin(
                    valid_schedule_origin.repository_origin.code_location_origin,
                    "invalid_repo_name",
                ),
                valid_schedule_origin.instigator_name,
            )

            schedule_state = InstigatorState(
                invalid_repo_origin,
                InstigatorType.SCHEDULE,
                InstigatorStatus.RUNNING,
                ScheduleInstigatorData("0 0 * * *", get_current_timestamp()),
            )
            scheduler_instance.add_instigator_state(schedule_state)

        initial_datetime = freeze_datetime + relativedelta(seconds=1)
        with freeze_time(initial_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 0

            ticks = scheduler_instance.get_ticks(
                invalid_repo_origin.get_id(), external_schedule.selector_id
            )

            assert len(ticks) == 0

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_bad_load_schedule(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        freeze_datetime = feb_27_2019_one_second_to_midnight()
        with freeze_time(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("simple_schedule")
            valid_schedule_origin = external_schedule.get_external_origin()

            # Swap out a new schedule name
            invalid_repo_origin = RemoteInstigatorOrigin(
                valid_schedule_origin.repository_origin,
                "invalid_schedule",
            )

            schedule_state = InstigatorState(
                invalid_repo_origin,
                InstigatorType.SCHEDULE,
                InstigatorStatus.RUNNING,
                ScheduleInstigatorData("0 0 * * *", get_current_timestamp()),
            )
            scheduler_instance.add_instigator_state(schedule_state)

        initial_datetime = freeze_datetime + relativedelta(seconds=1)
        with freeze_time(initial_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 0

            ticks = scheduler_instance.get_ticks(
                invalid_repo_origin.get_id(), schedule_state.selector_id
            )

            assert len(ticks) == 0

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_load_code_location_not_in_workspace(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        freeze_datetime = create_datetime(
            year=2019, month=2, day=27, hour=23, minute=59, second=59
        ).astimezone(get_timezone("US/Central"))

        with freeze_time(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("simple_schedule")
            valid_schedule_origin = external_schedule.get_external_origin()

            code_location_origin = valid_schedule_origin.repository_origin.code_location_origin
            assert isinstance(code_location_origin, ManagedGrpcPythonEnvCodeLocationOrigin)

            # Swap out a new location name
            invalid_repo_origin = RemoteInstigatorOrigin(
                RemoteRepositoryOrigin(
                    code_location_origin._replace(location_name="missing_location"),
                    valid_schedule_origin.repository_origin.repository_name,
                ),
                valid_schedule_origin.instigator_name,
            )

            schedule_state = InstigatorState(
                invalid_repo_origin,
                InstigatorType.SCHEDULE,
                InstigatorStatus.RUNNING,
                ScheduleInstigatorData("0 0 * * *", get_current_timestamp()),
            )
            scheduler_instance.add_instigator_state(schedule_state)

        initial_datetime = freeze_datetime + relativedelta(seconds=1)
        with freeze_time(initial_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 0

            ticks = scheduler_instance.get_ticks(
                invalid_repo_origin.get_id(), schedule_state.selector_id
            )

            assert len(ticks) == 0

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_multiple_schedules_on_different_time_ranges(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        external_hourly_schedule = external_repo.get_external_schedule("simple_hourly_schedule")
        freeze_datetime = feb_27_2019_one_second_to_midnight()
        with freeze_time(freeze_datetime):
            scheduler_instance.start_schedule(external_schedule)
            scheduler_instance.start_schedule(external_hourly_schedule)

        freeze_datetime = freeze_datetime + relativedelta(seconds=2)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 2
            ticks = scheduler_instance.get_ticks(
                external_schedule.get_external_origin_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS

            hourly_ticks = scheduler_instance.get_ticks(
                external_hourly_schedule.get_external_origin_id(),
                external_hourly_schedule.selector_id,
            )
            assert len(hourly_ticks) == 1
            assert hourly_ticks[0].status == TickStatus.SUCCESS

        freeze_datetime = freeze_datetime + relativedelta(hours=1)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 3

            ticks = scheduler_instance.get_ticks(
                external_schedule.get_external_origin_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS

            hourly_ticks = scheduler_instance.get_ticks(
                external_hourly_schedule.get_external_origin_id(),
                external_hourly_schedule.selector_id,
            )
            assert len(hourly_ticks) == 2
            assert len([tick for tick in hourly_ticks if tick.status == TickStatus.SUCCESS]) == 2

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_union_schedule(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        # This is a Wednesday.
        freeze_datetime = feb_27_2019_start_of_day()
        with freeze_time(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("union_schedule")
            schedule_origin = external_schedule.get_external_origin()
            scheduler_instance.start_schedule(external_schedule)

        # No new runs should be launched
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert scheduler_instance.get_runs_count() == 0

            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 0

        freeze_datetime = freeze_datetime + relativedelta(days=1)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert scheduler_instance.get_runs_count() == 1

            wait_for_all_runs_to_start(scheduler_instance)

            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1

            validate_tick(
                ticks[0],
                external_schedule,
                create_datetime(year=2019, month=2, day=28),
                TickStatus.SUCCESS,
                [next(iter(scheduler_instance.get_runs())).run_id],
            )

            validate_run_started(
                scheduler_instance,
                next(iter(scheduler_instance.get_runs())),
                execution_time=create_datetime(year=2019, month=2, day=28),
                partition_time=None,
            )

        freeze_datetime = freeze_datetime + relativedelta(days=1)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert scheduler_instance.get_runs_count() == 2

            wait_for_all_runs_to_start(scheduler_instance)

            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 2

            validate_tick(
                ticks[0],
                external_schedule,
                create_datetime(year=2019, month=3, day=1),
                TickStatus.SUCCESS,
                [next(iter(scheduler_instance.get_runs())).run_id],
            )

            validate_run_started(
                scheduler_instance,
                next(iter(scheduler_instance.get_runs())),
                execution_time=create_datetime(year=2019, month=3, day=1),
            )

        freeze_datetime = freeze_datetime + relativedelta(days=1)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert scheduler_instance.get_runs_count() == 3

            wait_for_all_runs_to_start(scheduler_instance)

            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 3

            validate_tick(
                ticks[0],
                external_schedule,
                create_datetime(year=2019, month=3, day=1, hour=12),
                TickStatus.SUCCESS,
                [next(iter(scheduler_instance.get_runs())).run_id],
            )

            validate_run_started(
                scheduler_instance,
                next(iter(scheduler_instance.get_runs())),
                execution_time=create_datetime(year=2019, month=3, day=1, hour=12),
                partition_time=None,
            )

        # No new runs should be launched
        freeze_datetime = freeze_datetime + relativedelta(days=1)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert scheduler_instance.get_runs_count() == 3

            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 3

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_multi_runs(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        freeze_datetime = feb_27_2019_one_second_to_midnight()
        with freeze_time(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("multi_run_schedule")
            schedule_origin = external_schedule.get_external_origin()
            scheduler_instance.start_schedule(external_schedule)

            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 0

            # launch_scheduled_runs does nothing before the first tick
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 0

        freeze_datetime = freeze_datetime + relativedelta(seconds=2)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert scheduler_instance.get_runs_count() == 2
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1

            expected_datetime = create_datetime(year=2019, month=2, day=28)

            runs = scheduler_instance.get_runs()
            validate_tick(
                ticks[0],
                external_schedule,
                expected_datetime,
                TickStatus.SUCCESS,
                [run.run_id for run in runs],
            )

            wait_for_all_runs_to_start(scheduler_instance)
            runs = scheduler_instance.get_runs()
            validate_run_started(
                scheduler_instance, runs[0], execution_time=create_datetime(2019, 2, 28)
            )
            validate_run_started(
                scheduler_instance, runs[1], execution_time=create_datetime(2019, 2, 28)
            )

            # Verify idempotence
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert scheduler_instance.get_runs_count() == 2
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS

        freeze_datetime = freeze_datetime + relativedelta(days=1)
        with freeze_time(freeze_datetime):
            # Traveling one more day in the future before running results in a tick
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert scheduler_instance.get_runs_count() == 4
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 2
            assert len([tick for tick in ticks if tick.status == TickStatus.SUCCESS]) == 2
            runs = scheduler_instance.get_runs()

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_multi_run_list(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        freeze_datetime = feb_27_2019_one_second_to_midnight()
        with freeze_time(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("multi_run_list_schedule")
            schedule_origin = external_schedule.get_external_origin()
            scheduler_instance.start_schedule(external_schedule)

            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 0

            # launch_scheduled_runs does nothing before the first tick
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 0

        freeze_datetime = freeze_datetime + relativedelta(seconds=2)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert scheduler_instance.get_runs_count() == 2
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1

            expected_datetime = create_datetime(year=2019, month=2, day=28)

            runs = scheduler_instance.get_runs()
            validate_tick(
                ticks[0],
                external_schedule,
                expected_datetime,
                TickStatus.SUCCESS,
                [run.run_id for run in runs],
            )

            wait_for_all_runs_to_start(scheduler_instance)
            runs = scheduler_instance.get_runs()
            validate_run_started(
                scheduler_instance, runs[0], execution_time=create_datetime(2019, 2, 28)
            )
            validate_run_started(
                scheduler_instance, runs[1], execution_time=create_datetime(2019, 2, 28)
            )

            # Verify idempotence
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert scheduler_instance.get_runs_count() == 2
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS

        freeze_datetime = freeze_datetime + relativedelta(days=1)
        with freeze_time(freeze_datetime):
            # Traveling one more day in the future before running results in a tick
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert scheduler_instance.get_runs_count() == 4
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 2
            assert len([tick for tick in ticks if tick.status == TickStatus.SUCCESS]) == 2
            runs = scheduler_instance.get_runs()

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_multi_runs_missing_run_key(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        freeze_datetime = feb_27_2019_start_of_day()
        with freeze_time(freeze_datetime):
            external_schedule = external_repo.get_external_schedule(
                "multi_run_schedule_with_missing_run_key"
            )
            schedule_origin = external_schedule.get_external_origin()
            scheduler_instance.start_schedule(external_schedule)

            evaluate_schedules(workspace_context, executor, get_current_datetime())
            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1

            validate_tick(
                ticks[0],
                external_schedule,
                freeze_datetime,
                TickStatus.FAILURE,
                [],
                "Error occurred during the execution function for schedule "
                "multi_run_schedule_with_missing_run_key",
                expected_failure_count=1,
            )

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_large_schedule(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        freeze_datetime = feb_27_2019_one_second_to_midnight()
        with freeze_time(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("large_schedule")
            schedule_origin = external_schedule.get_external_origin()
            scheduler_instance.start_schedule(external_schedule)

            freeze_datetime = freeze_datetime + relativedelta(seconds=2)

        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 1
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_skip_reason_schedule(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        freeze_datetime = feb_27_2019_start_of_day()
        with freeze_time(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("empty_schedule")

            schedule_origin = external_schedule.get_external_origin()

            scheduler_instance.start_schedule(external_schedule)

            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 0
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
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
    def test_many_requests_schedule(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
        submit_executor: Optional[ThreadPoolExecutor],
    ):
        freeze_datetime = feb_27_2019_start_of_day()
        with freeze_time(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("many_requests_schedule")

            schedule_origin = external_schedule.get_external_origin()

            scheduler_instance.start_schedule(external_schedule)

            evaluate_schedules(
                workspace_context,
                executor,
                get_current_datetime(),
                submit_executor=submit_executor,
            )

            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1

            runs = scheduler_instance.get_runs()
            assert len(runs) == 15
            validate_tick(
                ticks[0],
                external_schedule,
                freeze_datetime,
                TickStatus.SUCCESS,
                [run.run_id for run in runs],
            )

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_asset_selection(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        freeze_datetime = feb_27_2019_one_second_to_midnight()
        external_schedule = external_repo.get_external_schedule("asset_selection_schedule")
        schedule_origin = external_schedule.get_external_origin()

        with freeze_time(freeze_datetime):
            scheduler_instance.start_schedule(external_schedule)

            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )

            # launch_scheduled_runs does nothing before the first tick
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            scheduler_instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)

        freeze_datetime = freeze_datetime + relativedelta(seconds=2)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 1
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1

            expected_datetime = create_datetime(year=2019, month=2, day=28)

            validate_tick(
                ticks[0],
                external_schedule,
                expected_datetime,
                TickStatus.SUCCESS,
                [run.run_id for run in scheduler_instance.get_runs()],
            )

            wait_for_all_runs_to_start(scheduler_instance)
            run = next(iter(scheduler_instance.get_runs()))
            assert run.asset_selection == {AssetKey("asset1")}

            validate_run_started(
                scheduler_instance, run, execution_time=create_datetime(2019, 2, 28)
            )

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_stale_asset_selection_never_materialized(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        freeze_datetime = feb_27_2019_one_second_to_midnight()
        external_schedule = external_repo.get_external_schedule("stale_asset_selection_schedule")

        with freeze_time(freeze_datetime):
            scheduler_instance.start_schedule(external_schedule)

        # never materialized so all assets stale
        freeze_datetime = freeze_datetime + relativedelta(seconds=2)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            wait_for_all_runs_to_start(scheduler_instance)
            schedule_run = next(
                (r for r in scheduler_instance.get_runs() if r.job_name == "asset_job"), None
            )
            assert schedule_run is not None
            assert schedule_run.asset_selection == {AssetKey("asset1"), AssetKey("asset2")}
            validate_run_started(
                scheduler_instance, schedule_run, execution_time=create_datetime(2019, 2, 28)
            )

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_stale_asset_selection_empty(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        freeze_datetime = feb_27_2019_one_second_to_midnight()
        external_schedule = external_repo.get_external_schedule("stale_asset_selection_schedule")

        with freeze_time(freeze_datetime):
            scheduler_instance.start_schedule(external_schedule)

        materialize([asset1, asset2], instance=scheduler_instance)

        # assets previously materialized so we expect empy set
        freeze_datetime = freeze_datetime + relativedelta(seconds=2)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            wait_for_all_runs_to_start(scheduler_instance)
            schedule_run = next(
                (r for r in scheduler_instance.get_runs() if r.job_name == "asset_job"), None
            )
            assert schedule_run is None

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_stale_asset_selection_subset(
        self,
        scheduler_instance: DagsterInstance,
        workspace_context: WorkspaceProcessContext,
        external_repo: ExternalRepository,
        executor: ThreadPoolExecutor,
    ):
        freeze_datetime = feb_27_2019_one_second_to_midnight()
        external_schedule = external_repo.get_external_schedule("stale_asset_selection_schedule")

        with freeze_time(freeze_datetime):
            scheduler_instance.start_schedule(external_schedule)

        materialize([asset1], instance=scheduler_instance)

        # assets previously materialized so we expect empy set
        freeze_datetime = freeze_datetime + relativedelta(seconds=2)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            wait_for_all_runs_to_start(scheduler_instance)
            schedule_run = next(
                (r for r in scheduler_instance.get_runs() if r.job_name == "asset_job"), None
            )
            assert schedule_run is not None
            assert schedule_run.asset_selection == {AssetKey("asset2")}
            validate_run_started(
                scheduler_instance, schedule_run, execution_time=create_datetime(2019, 2, 28)
            )

    @pytest.mark.parametrize("executor", get_schedule_executors())
    def test_source_asset_observation(
        self, scheduler_instance: DagsterInstance, workspace_context, external_repo, executor
    ):
        freeze_datetime = feb_27_2019_one_second_to_midnight()
        external_schedule = external_repo.get_external_schedule("source_asset_observation_schedule")
        schedule_origin = external_schedule.get_external_origin()

        with freeze_time(freeze_datetime):
            scheduler_instance.start_schedule(external_schedule)

            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )

            # launch_scheduled_runs does nothing before the first tick
            evaluate_schedules(workspace_context, executor, get_current_datetime())
            scheduler_instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)

        freeze_datetime = freeze_datetime + relativedelta(seconds=2)
        with freeze_time(freeze_datetime):
            evaluate_schedules(workspace_context, executor, get_current_datetime())

            assert scheduler_instance.get_runs_count() == 1
            ticks = scheduler_instance.get_ticks(
                schedule_origin.get_id(), external_schedule.selector_id
            )
            assert len(ticks) == 1

            expected_datetime = create_datetime(year=2019, month=2, day=28)

            validate_tick(
                ticks[0],
                external_schedule,
                expected_datetime,
                TickStatus.SUCCESS,
                [run.run_id for run in scheduler_instance.get_runs()],
            )

            wait_for_all_runs_to_start(scheduler_instance)
            run = next(iter(scheduler_instance.get_runs()))
            assert run.asset_selection == {AssetKey("source_asset")}

            validate_run_started(
                scheduler_instance, run, execution_time=create_datetime(2019, 2, 28)
            )
