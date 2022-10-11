import datetime
import random
import string
import time
from contextlib import ExitStack, contextmanager

import pendulum
import pytest

from dagster import (
    Any,
    DefaultScheduleStatus,
    Field,
    ScheduleDefinition,
    job,
    op,
    repository,
    schedule,
)
from dagster._core.definitions.run_request import RunRequest
from dagster._core.host_representation import (
    ExternalInstigatorOrigin,
    ExternalRepositoryOrigin,
    GrpcServerRepositoryLocation,
    GrpcServerRepositoryLocationOrigin,
)
from dagster._core.instance import DagsterInstance
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    InstigatorType,
    ScheduleInstigatorData,
    TickData,
    TickStatus,
)
from dagster._core.scheduler.scheduler import DEFAULT_MAX_CATCHUP_RUNS
from dagster._core.storage.pipeline_run import PipelineRunStatus, RunsFilter
from dagster._core.storage.tags import PARTITION_NAME_TAG, SCHEDULED_EXECUTION_TIME_TAG
from dagster._core.test_utils import (
    SingleThreadPoolExecutor,
    create_test_daemon_workspace_context,
    instance_for_test,
    mock_system_timezone,
    wait_for_futures,
)
from dagster._core.workspace.load_target import EmptyWorkspaceTarget, GrpcServerTarget, ModuleTarget
from dagster._daemon import get_default_daemon_logger
from dagster._grpc.client import EphemeralDagsterGrpcClient
from dagster._grpc.server import open_server_process
from dagster._legacy import daily_schedule, hourly_schedule, pipeline, solid
from dagster._scheduler.scheduler import launch_scheduled_runs
from dagster._seven import wait_for_process
from dagster._seven.compat.pendulum import create_pendulum_time, to_timezone
from dagster._utils import find_free_port
from dagster._utils.error import SerializableErrorInfo
from dagster._utils.partitions import DEFAULT_DATE_FORMAT

from .conftest import loadable_target_origin, workspace_load_target

_COUPLE_DAYS_AGO = datetime.datetime(year=2019, month=2, day=25)


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
    workspace_context,
    executor,
    end_datetime_utc,
    max_tick_retries=0,
    max_catchup_runs=DEFAULT_MAX_CATCHUP_RUNS,
    debug_crash_flags=None,
    timeout=75,
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


@solid(config_schema={"partition_time": str})
def the_solid(context):
    return "Ran at this partition date: {}".format(context.solid_config["partition_time"])


@pipeline
def the_pipeline():
    the_solid()


def _solid_config(date):
    return {
        "solids": {"the_solid": {"config": {"partition_time": date.isoformat()}}},
    }


@daily_schedule(pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO, execution_timezone="UTC")
def simple_schedule(date):
    return _solid_config(date)


@daily_schedule(pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO)
def daily_schedule_without_timezone(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_timezone="US/Central",
)
def daily_central_time_schedule(date):
    return _solid_config(date)


@schedule(
    job_name="the_pipeline",
    cron_schedule="*/5 * * * *",
    execution_timezone="US/Central",
)
def partitionless_schedule(context):
    return _solid_config(context.scheduled_execution_time)


@schedule(
    job_name="the_pipeline",
    cron_schedule=["0 0 * * 4", "0 0 * * 5", "0 0,12 * * 5"],
    execution_timezone="UTC",
)
def union_schedule(context):
    return _solid_config(context.scheduled_execution_time)


# Schedule that runs on a different day in Central Time vs UTC
@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_time=datetime.time(hour=23, minute=0),
    execution_timezone="US/Central",
)
def daily_late_schedule(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_time=datetime.time(hour=2, minute=30),
    execution_timezone="US/Central",
)
def daily_dst_transition_schedule_skipped_time(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_time=datetime.time(hour=1, minute=30),
    execution_timezone="US/Central",
)
def daily_dst_transition_schedule_doubled_time(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_timezone="US/Eastern",
)
def daily_eastern_time_schedule(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    end_date=datetime.datetime(year=2019, month=3, day=1),
    execution_timezone="UTC",
)
def simple_temporary_schedule(date):
    return _solid_config(date)


# forgot date arg
@daily_schedule(  # type: ignore
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_timezone="UTC",
)
def bad_env_fn_schedule():
    return {}


NUM_CALLS = {"sync": 0, "async": 0}


def get_passes_on_retry_schedule(key):
    @daily_schedule(  # type: ignore
        pipeline_name="the_pipeline",
        start_date=_COUPLE_DAYS_AGO,
        execution_timezone="UTC",
        name=f"passes_on_retry_schedule_{key}",
    )
    def passes_on_retry_schedule(date):
        NUM_CALLS[key] = NUM_CALLS[key] + 1
        if NUM_CALLS[key] > 1:
            return _solid_config(date)
        raise Exception("better luck next time")

    return passes_on_retry_schedule


@hourly_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_timezone="UTC",
)
def simple_hourly_schedule(date):
    return _solid_config(date)


@hourly_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_timezone="US/Central",
)
def hourly_central_time_schedule(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    should_execute=_throw,
    execution_timezone="UTC",
)
def bad_should_execute_schedule(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    should_execute=_throw_on_odd_day,
    execution_timezone="UTC",
)
def bad_should_execute_schedule_on_odd_days(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    should_execute=_never,
    execution_timezone="UTC",
)
def skip_schedule(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_timezone="UTC",
)
def wrong_config_schedule(_date):
    return {}


@schedule(
    job_name="the_pipeline",
    cron_schedule="0 0 * * *",
    execution_timezone="UTC",
)
def empty_schedule(_date):
    pass  # No RunRequests


def define_multi_run_schedule():
    def gen_runs(context):
        if not context.scheduled_execution_time:
            date = pendulum.now().subtract(days=1)
        else:
            date = pendulum.instance(context.scheduled_execution_time).subtract(days=1)

        yield RunRequest(run_key="A", run_config=_solid_config(date), tags={"label": "A"})
        yield RunRequest(run_key="B", run_config=_solid_config(date), tags={"label": "B"})

    return ScheduleDefinition(
        name="multi_run_schedule",
        cron_schedule="0 0 * * *",
        job_name="the_pipeline",
        execution_timezone="UTC",
        execution_fn=gen_runs,
    )


@schedule(
    job_name="the_pipeline",
    cron_schedule="0 0 * * *",
    execution_timezone="UTC",
)
def multi_run_list_schedule(context):
    if not context.scheduled_execution_time:
        date = pendulum.now().subtract(days=1)
    else:
        date = pendulum.instance(context.scheduled_execution_time).subtract(days=1)

    return [
        RunRequest(run_key="A", run_config=_solid_config(date), tags={"label": "A"}),
        RunRequest(run_key="B", run_config=_solid_config(date), tags={"label": "B"}),
    ]


def define_multi_run_schedule_with_missing_run_key():
    def gen_runs(context):
        if not context.scheduled_execution_time:
            date = pendulum.now().subtract(days=1)
        else:
            date = pendulum.instance(context.scheduled_execution_time).subtract(days=1)

        yield RunRequest(run_key="A", run_config=_solid_config(date), tags={"label": "A"})
        yield RunRequest(run_key=None, run_config=_solid_config(date), tags={"label": "B"})

    return ScheduleDefinition(
        name="multi_run_schedule_with_missing_run_key",
        cron_schedule="0 0 * * *",
        job_name="the_pipeline",
        execution_timezone="UTC",
        execution_fn=gen_runs,
    )


@repository
def the_other_repo():
    return [
        the_pipeline,
        multi_run_list_schedule,
    ]


@solid(config_schema=Field(Any))
def config_solid(_):
    return 1


@pipeline
def config_pipeline():
    config_solid()


@daily_schedule(
    pipeline_name="config_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_timezone="UTC",
)
def large_schedule(_):
    REQUEST_CONFIG_COUNT = 120000

    def _random_string(length):
        return "".join(random.choice(string.ascii_lowercase) for x in range(length))

    return {
        "solids": {
            "config_solid": {
                "config": {
                    "foo": {
                        _random_string(10): _random_string(20) for i in range(REQUEST_CONFIG_COUNT)
                    }
                }
            }
        }
    }


@solid
def start(_, x):
    return x


@solid
def end(_, x=1):
    return x


@pipeline
def two_step_pipeline():
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


@repository
def the_repo():
    return [
        the_pipeline,
        config_pipeline,
        simple_schedule,
        simple_temporary_schedule,
        simple_hourly_schedule,
        daily_schedule_without_timezone,
        daily_late_schedule,
        daily_dst_transition_schedule_skipped_time,
        daily_dst_transition_schedule_doubled_time,
        daily_central_time_schedule,
        daily_eastern_time_schedule,
        hourly_central_time_schedule,
        bad_env_fn_schedule,
        get_passes_on_retry_schedule("sync"),
        get_passes_on_retry_schedule("async"),
        bad_should_execute_schedule,
        bad_should_execute_schedule_on_odd_days,
        skip_schedule,
        wrong_config_schedule,
        define_multi_run_schedule(),
        multi_run_list_schedule,
        define_multi_run_schedule_with_missing_run_key(),
        partitionless_schedule,
        union_schedule,
        large_schedule,
        two_step_pipeline,
        default_config_schedule,
        empty_schedule,
    ]


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_timezone="UTC",
    default_status=DefaultScheduleStatus.RUNNING,
)
def always_running_schedule(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_timezone="UTC",
    default_status=DefaultScheduleStatus.STOPPED,
)
def never_running_schedule(date):
    return _solid_config(date)


@repository
def the_status_in_code_repo():
    return [
        the_pipeline,
        always_running_schedule,
        never_running_schedule,
    ]


def logger():
    return get_default_daemon_logger("SchedulerDaemon")


def validate_tick(
    tick,
    external_schedule,
    expected_datetime,
    expected_status,
    expected_run_ids,
    expected_error=None,
    expected_failure_count=0,
    expected_skip_reason=None,
):
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
            assert run.run_config == _solid_config(partition_time)
    else:
        assert run.status == PipelineRunStatus.FAILURE


def wait_for_all_runs_to_start(instance, timeout=10):
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            raise Exception("Timed out waiting for runs to start")
        time.sleep(0.5)

        not_started_runs = [
            run for run in instance.get_runs() if run.status == PipelineRunStatus.NOT_STARTED
        ]

        if len(not_started_runs) == 0:
            break


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_simple_schedule(instance, workspace_context, external_repo, executor):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
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
            instance.get_runs()[0],
            execution_time=create_pendulum_time(2019, 2, 28),
            partition_time=create_pendulum_time(2019, 2, 27),
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

        # Traveling two more days in the future before running results in two new ticks
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 3
        assert len([tick for tick in ticks if tick.status == TickStatus.SUCCESS]) == 3

        runs_by_partition = {run.tags[PARTITION_NAME_TAG]: run for run in instance.get_runs()}

        assert "2019-02-28" in runs_by_partition
        assert "2019-03-01" in runs_by_partition

        # Check idempotence again
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 3


# Verify that the scheduler uses selector and not origin to dedupe schedules
@pytest.mark.parametrize("executor", get_schedule_executors())
def test_schedule_with_different_origin(instance, workspace_context, external_repo, executor):
    external_schedule = external_repo.get_external_schedule("simple_schedule")
    existing_origin = external_schedule.get_external_origin()

    repo_location_origin = existing_origin.external_repository_origin.repository_location_origin
    modified_loadable_target_origin = repo_location_origin.loadable_target_origin._replace(
        executable_path="/different/executable_path"
    )

    # Change metadata on the origin that shouldn't matter for execution
    modified_origin = existing_origin._replace(
        external_repository_origin=existing_origin.external_repository_origin._replace(
            repository_location_origin=repo_location_origin._replace(
                loadable_target_origin=modified_loadable_target_origin
            )
        )
    )

    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
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
def test_old_tick_schedule(instance, workspace_context, external_repo, executor):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
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

        # the start time is what determines the number of runs, not the last tick
        instance.start_schedule(external_schedule)

    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 2


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_no_started_schedules(instance, workspace_context, external_repo, executor):
    external_schedule = external_repo.get_external_schedule("simple_schedule")
    schedule_origin = external_schedule.get_external_origin()

    evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
    assert instance.get_runs_count() == 0

    ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
    assert len(ticks) == 0


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_schedule_without_timezone(instance, executor):
    with mock_system_timezone("US/Eastern"):
        with create_test_daemon_workspace_context(
            workspace_load_target=workspace_load_target(),
            instance=instance,
        ) as workspace_context:
            external_repo = next(
                iter(workspace_context.create_request_context().get_workspace_snapshot().values())
            ).repository_location.get_repository("the_repo")
            external_schedule = external_repo.get_external_schedule(
                "daily_schedule_without_timezone"
            )
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
                    instance.get_runs()[0],
                    execution_time=expected_datetime,
                    partition_time=create_pendulum_time(2019, 2, 26, tz="UTC"),
                )

                # Verify idempotence
                evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
                assert instance.get_runs_count() == 1
                ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
                assert len(ticks) == 1


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_bad_env_fn_no_retries(instance, workspace_context, external_repo, executor):
    external_schedule = external_repo.get_external_schedule("bad_env_fn_schedule")
    schedule_origin = external_schedule.get_external_origin()
    initial_datetime = create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0)
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
            "Error occurred during the execution of run_config_fn for schedule bad_env_fn_schedule",
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
            initial_datetime,
            TickStatus.FAILURE,
            [],
            "Error occurred during the execution of run_config_fn for schedule bad_env_fn_schedule",
            expected_failure_count=1,
        )

    initial_datetime = initial_datetime.add(days=1)
    with pendulum.test(initial_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 2

        validate_tick(
            ticks[0],
            external_schedule,
            initial_datetime,
            TickStatus.FAILURE,
            [],
            "Error occurred during the execution of run_config_fn for schedule bad_env_fn_schedule",
            expected_failure_count=1,
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_bad_env_fn_with_retries(instance, workspace_context, external_repo, executor):
    external_schedule = external_repo.get_external_schedule("bad_env_fn_schedule")
    schedule_origin = external_schedule.get_external_origin()
    initial_datetime = create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0)
    with pendulum.test(initial_datetime):
        instance.start_schedule(external_schedule)

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"), max_tick_retries=2)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            initial_datetime,
            TickStatus.FAILURE,
            [],
            "Error occurred during the execution of run_config_fn for schedule bad_env_fn_schedule",
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
            initial_datetime,
            TickStatus.FAILURE,
            [],
            "Error occurred during the execution of run_config_fn for schedule bad_env_fn_schedule",
            expected_failure_count=3,
        )

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"), max_tick_retries=2)
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            initial_datetime,
            TickStatus.FAILURE,
            [],
            "Error occurred during the execution of run_config_fn for schedule bad_env_fn_schedule",
            expected_failure_count=3,
        )

    initial_datetime = initial_datetime.add(days=1)
    with pendulum.test(initial_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 2

        validate_tick(
            ticks[0],
            external_schedule,
            initial_datetime,
            TickStatus.FAILURE,
            [],
            "Error occurred during the execution of run_config_fn for schedule bad_env_fn_schedule",
            expected_failure_count=1,
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_passes_on_retry(instance, workspace_context, external_repo, executor):
    # We need to use different keys across sync and async executors, as the dictionary is persisted across processes.
    if isinstance(executor, SingleThreadPoolExecutor):
        schedule_name = "passes_on_retry_schedule_sync"
    else:
        schedule_name = "passes_on_retry_schedule_async"
    external_schedule = external_repo.get_external_schedule(schedule_name)
    schedule_origin = external_schedule.get_external_origin()
    initial_datetime = create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0)
    with pendulum.test(initial_datetime):
        instance.start_schedule(external_schedule)

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"), max_tick_retries=1)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            initial_datetime,
            TickStatus.FAILURE,
            [],
            f"Error occurred during the execution of run_config_fn for schedule {schedule_name}",
            expected_failure_count=1,
        )

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"), max_tick_retries=1)

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            initial_datetime,
            TickStatus.SUCCESS,
            [run.run_id for run in instance.get_runs()],
            expected_failure_count=1,
        )

    initial_datetime = initial_datetime.add(days=1)
    with pendulum.test(initial_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"), max_tick_retries=1)

        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 2

        validate_tick(
            ticks[0],
            external_schedule,
            initial_datetime,
            TickStatus.SUCCESS,
            [instance.get_runs()[0].run_id],
            expected_failure_count=0,
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_bad_should_execute(instance, workspace_context, external_repo, executor):
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
            "Error occurred during the execution of should_execute for schedule bad_should_execute_schedule",
            expected_failure_count=1,
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_skip(instance, workspace_context, external_repo, executor):
    external_schedule = external_repo.get_external_schedule("skip_schedule")
    schedule_origin = external_schedule.get_external_origin()
    initial_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0, tz="UTC"),
        "US/Central",
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
            TickStatus.SKIPPED,
            [run.run_id for run in instance.get_runs()],
            expected_skip_reason="should_execute function for skip_schedule returned false.",
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_wrong_config_schedule(instance, workspace_context, external_repo, executor):
    external_schedule = external_repo.get_external_schedule("wrong_config_schedule")
    schedule_origin = external_schedule.get_external_origin()
    initial_datetime = create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0)
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
            [],
            "DagsterInvalidConfigError",
            expected_failure_count=1,
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_schedule_run_default_config(instance, workspace_context, external_repo, executor):
    external_schedule = external_repo.get_external_schedule("default_config_schedule")
    schedule_origin = external_schedule.get_external_origin()
    initial_datetime = create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0)
    with pendulum.test(initial_datetime):
        instance.start_schedule(external_schedule)

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1

        wait_for_all_runs_to_start(instance)

        run = instance.get_runs()[0]

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

        assert instance.run_launcher.did_run_launch(run.run_id)


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
    instance, workspace_context, external_repo, executor
):
    good_schedule = external_repo.get_external_schedule("simple_schedule")
    bad_schedule = external_repo.get_external_schedule("bad_should_execute_schedule_on_odd_days")

    good_origin = good_schedule.get_external_origin()
    bad_origin = bad_schedule.get_external_origin()
    unloadable_origin = _get_unloadable_schedule_origin()
    initial_datetime = create_pendulum_time(
        year=2019,
        month=2,
        day=27,
        hour=0,
        minute=0,
        second=0,
    )
    with pendulum.test(initial_datetime):
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
            instance.get_runs()[0],
            execution_time=initial_datetime,
            partition_time=create_pendulum_time(2019, 2, 26),
        )

        good_ticks = instance.get_ticks(good_origin.get_id(), good_schedule.selector_id)
        assert len(good_ticks) == 1
        validate_tick(
            good_ticks[0],
            good_schedule,
            initial_datetime,
            TickStatus.SUCCESS,
            [run.run_id for run in instance.get_runs()],
        )

        bad_ticks = instance.get_ticks(bad_origin.get_id(), bad_schedule.selector_id)
        assert len(bad_ticks) == 1

        assert bad_ticks[0].status == TickStatus.FAILURE

        assert (
            "Error occurred during the execution of should_execute for schedule bad_should_execute_schedule"
            in bad_ticks[0].error.message
        )

        unloadable_ticks = instance.get_ticks(unloadable_origin.get_id(), "fake_selector")
        assert len(unloadable_ticks) == 0

    initial_datetime = initial_datetime.add(days=1)
    with pendulum.test(initial_datetime):
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
            partition_time=create_pendulum_time(2019, 2, 27),
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
            partition_time=create_pendulum_time(2019, 2, 27),
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
def test_run_scheduled_on_time_boundary(instance, workspace_context, external_repo, executor):
    external_schedule = external_repo.get_external_schedule("simple_schedule")

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
        # Start schedule exactly at midnight
        instance.start_schedule(external_schedule)

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_bad_load_repository(instance, workspace_context, external_repo, caplog, executor):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        valid_schedule_origin = external_schedule.get_external_origin()

        # Swap out a new repository name
        invalid_repo_origin = ExternalInstigatorOrigin(
            ExternalRepositoryOrigin(
                valid_schedule_origin.external_repository_origin.repository_location_origin,
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
            "Could not find repository invalid_repo_name in location test_location to run schedule simple_schedule"
            in caplog.text
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_bad_load_schedule(instance, workspace_context, external_repo, caplog, executor):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
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
def test_error_load_repository_location(instance, executor):
    with create_test_daemon_workspace_context(
        _get_unloadable_workspace_load_target(), instance
    ) as workspace_context:
        fake_origin = _get_unloadable_schedule_origin()
        initial_datetime = create_pendulum_time(
            year=2019,
            month=2,
            day=27,
            hour=23,
            minute=59,
            second=59,
        )
        with pendulum.test(initial_datetime):
            schedule_state = InstigatorState(
                fake_origin,
                InstigatorType.SCHEDULE,
                InstigatorStatus.RUNNING,
                ScheduleInstigatorData("0 0 * * *", pendulum.now("UTC").timestamp()),
            )
            instance.add_instigator_state(schedule_state)

        initial_datetime = initial_datetime.add(seconds=1)
        with pendulum.test(initial_datetime):
            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

            assert instance.get_runs_count() == 0

            ticks = instance.get_ticks(fake_origin.get_id(), schedule_state.selector_id)

            assert len(ticks) == 0

        initial_datetime = initial_datetime.add(days=1)
        with pendulum.test(initial_datetime):
            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
            assert instance.get_runs_count() == 0
            ticks = instance.get_ticks(fake_origin.get_id(), schedule_state.selector_id)
            assert len(ticks) == 0


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_load_repository_location_not_in_workspace(
    instance, workspace_context, external_repo, caplog, executor
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )

    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        valid_schedule_origin = external_schedule.get_external_origin()

        # Swap out a new location name
        invalid_repo_origin = ExternalInstigatorOrigin(
            ExternalRepositoryOrigin(
                valid_schedule_origin.external_repository_origin.repository_location_origin._replace(
                    location_name="missing_location"
                ),
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
            "Schedule simple_schedule was started from a location missing_location that can no longer be found in the workspace"
            in caplog.text
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_multiple_schedules_on_different_time_ranges(
    instance, workspace_context, external_repo, executor
):
    external_schedule = external_repo.get_external_schedule("simple_schedule")
    external_hourly_schedule = external_repo.get_external_schedule("simple_hourly_schedule")
    initial_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(initial_datetime):
        instance.start_schedule(external_schedule)
        instance.start_schedule(external_hourly_schedule)

    initial_datetime = initial_datetime.add(seconds=2)
    with pendulum.test(initial_datetime):
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

    initial_datetime = initial_datetime.add(hours=1)
    with pendulum.test(initial_datetime):
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
def test_launch_failure(workspace_context, external_repo, executor):
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
        initial_datetime = to_timezone(
            create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0, tz="UTC"),
            "US/Central",
        )

        with pendulum.test(initial_datetime):
            exploding_ctx = workspace_context.copy_for_test_instance(instance)
            instance.start_schedule(external_schedule)

            evaluate_schedules(exploding_ctx, executor, pendulum.now("UTC"))

            assert instance.get_runs_count() == 1

            run = instance.get_runs()[0]

            validate_run_started(
                instance,
                run,
                execution_time=initial_datetime,
                partition_time=create_pendulum_time(2019, 2, 26),
                expected_success=False,
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


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_partitionless_schedule(instance, workspace_context, external_repo, executor):
    initial_datetime = create_pendulum_time(year=2019, month=2, day=27, tz="US/Central")
    with pendulum.test(initial_datetime):
        external_schedule = external_repo.get_external_schedule("partitionless_schedule")
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

    # Travel enough in the future that many ticks have passed, but only one run executes
    initial_datetime = initial_datetime.add(days=5)
    with pendulum.test(initial_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 1

        wait_for_all_runs_to_start(instance)

        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            create_pendulum_time(year=2019, month=3, day=4, tz="US/Central"),
            TickStatus.SUCCESS,
            [run.run_id for run in instance.get_runs()],
        )

        validate_run_started(
            instance,
            instance.get_runs()[0],
            execution_time=create_pendulum_time(year=2019, month=3, day=4, tz="US/Central"),
            partition_time=None,
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_union_schedule(instance, workspace_context, external_repo, executor):
    # This is a Wednesday.
    initial_datetime = create_pendulum_time(year=2019, month=2, day=27, tz="UTC")
    with pendulum.test(initial_datetime):
        external_schedule = external_repo.get_external_schedule("union_schedule")
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

    # No new runs should be launched
    with pendulum.test(initial_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 0

        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 0

    initial_datetime = initial_datetime.add(days=1)
    with pendulum.test(initial_datetime):
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
            [instance.get_runs()[0].run_id],
        )

        validate_run_started(
            instance,
            instance.get_runs()[0],
            execution_time=create_pendulum_time(year=2019, month=2, day=28, tz="UTC"),
            partition_time=None,
        )

    initial_datetime = initial_datetime.add(days=1)
    with pendulum.test(initial_datetime):
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
            [instance.get_runs()[0].run_id],
        )

        validate_run_started(
            instance,
            instance.get_runs()[0],
            execution_time=create_pendulum_time(year=2019, month=3, day=1, tz="UTC"),
            partition_time=None,
        )

    initial_datetime = initial_datetime.add(days=1)
    with pendulum.test(initial_datetime):
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
            [instance.get_runs()[0].run_id],
        )

        validate_run_started(
            instance,
            instance.get_runs()[0],
            execution_time=create_pendulum_time(year=2019, month=3, day=1, hour=12, tz="UTC"),
            partition_time=None,
        )

    # No new runs should be launched
    initial_datetime = initial_datetime.add(days=1)
    with pendulum.test(initial_datetime):
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
        assert instance.get_runs_count() == 3

        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 3


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_max_catchup_runs(instance, workspace_context, external_repo, executor):
    initial_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(initial_datetime):
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

    initial_datetime = initial_datetime.add(days=5)
    with pendulum.test(initial_datetime):
        # Day is now March 4 at 11:59PM
        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"), max_catchup_runs=2)

        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 2

        first_datetime = create_pendulum_time(year=2019, month=3, day=4)

        wait_for_all_runs_to_start(instance)

        validate_tick(
            ticks[0],
            external_schedule,
            first_datetime,
            TickStatus.SUCCESS,
            [instance.get_runs()[0].run_id],
        )
        validate_run_started(
            instance,
            instance.get_runs()[0],
            execution_time=first_datetime,
            partition_time=create_pendulum_time(2019, 3, 3),
        )

        second_datetime = create_pendulum_time(year=2019, month=3, day=3)

        validate_tick(
            ticks[1],
            external_schedule,
            second_datetime,
            TickStatus.SUCCESS,
            [instance.get_runs()[1].run_id],
        )

        validate_run_started(
            instance,
            instance.get_runs()[1],
            execution_time=second_datetime,
            partition_time=create_pendulum_time(2019, 3, 2),
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_multi_runs(instance, workspace_context, external_repo, executor):
    freeze_datetime = to_timezone(
        create_pendulum_time(
            year=2019,
            month=2,
            day=27,
            hour=23,
            minute=59,
            second=59,
            tz="UTC",
        ),
        "US/Central",
    )
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
def test_multi_run_list(instance, workspace_context, external_repo, executor):
    freeze_datetime = to_timezone(
        create_pendulum_time(
            year=2019,
            month=2,
            day=27,
            hour=23,
            minute=59,
            second=59,
            tz="UTC",
        ),
        "US/Central",
    )
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
def test_multi_runs_missing_run_key(instance, workspace_context, external_repo, executor):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"), "US/Central"
    )
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
            "Error occurred during the execution function for schedule "
            "multi_run_schedule_with_missing_run_key",
            expected_failure_count=1,
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_large_schedule(instance, workspace_context, external_repo, executor):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
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
def _grpc_server_external_repo(port):
    server_process = open_server_process(
        port=port,
        socket=None,
        loadable_target_origin=loadable_target_origin(),
    )
    try:
        # shuts down server when it leaves this contextmanager
        with EphemeralDagsterGrpcClient(port=port, socket=None, server_process=server_process):
            location_origin = GrpcServerRepositoryLocationOrigin(
                host="localhost", port=port, location_name="test_location"
            )
            with GrpcServerRepositoryLocation(origin=location_origin) as location:
                yield location.get_repository("the_repo")

    finally:
        if server_process.poll() is None:
            wait_for_process(server_process, timeout=30)


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_skip_reason_schedule(instance, workspace_context, external_repo, executor):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=28, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("empty_schedule")

        schedule_origin = external_schedule.get_external_origin()

        instance.start_schedule(external_schedule)

        evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
        assert len(ticks) == 1

        expected_datetime = create_pendulum_time(year=2019, month=2, day=28, tz="UTC")

        validate_tick(
            ticks[0],
            external_schedule,
            expected_datetime,
            TickStatus.SKIPPED,
            [],
            expected_skip_reason="Schedule function returned an empty result",
        )


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_grpc_server_down(instance, executor):
    port = find_free_port()
    location_origin = GrpcServerRepositoryLocationOrigin(
        host="localhost", port=port, location_name="test_location"
    )
    schedule_origin = ExternalInstigatorOrigin(
        external_repository_origin=ExternalRepositoryOrigin(
            repository_location_origin=location_origin,
            repository_name="the_repo",
        ),
        instigator_name="simple_schedule",
    )

    initial_datetime = create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0)
    stack = ExitStack()
    external_repo = stack.enter_context(_grpc_server_external_repo(port))
    workspace_context = stack.enter_context(
        create_test_daemon_workspace_context(
            GrpcServerTarget(
                host="localhost", port=port, socket=None, location_name="test_location"
            ),
            instance,
        )
    )
    with pendulum.test(initial_datetime):
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        instance.start_schedule(external_schedule)
        # freeze the working workspace snapshot
        server_up_ctx = workspace_context.copy_for_test_instance(instance)

        # shut down the server
        stack.pop_all()

        # Server is no longer running, ticks fail but indicate it will resume once it is reachable
        for _trial in range(3):
            evaluate_schedules(server_up_ctx, executor, pendulum.now("UTC"))
            assert instance.get_runs_count() == 0
            ticks = instance.get_ticks(schedule_origin.get_id(), external_schedule.selector_id)
            assert len(ticks) == 1

            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                TickStatus.FAILURE,
                [],
                "Unable to reach the user code server for schedule simple_schedule. Schedule will resume execution once the server is available.",
                expected_failure_count=0,
            )

        # Server starts back up, tick now succeeds
        with _grpc_server_external_repo(port) as external_repo:
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
def test_status_in_code_schedule(instance, executor):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with create_test_daemon_workspace_context(
        workspace_load_target(attribute="the_status_in_code_repo"),
        instance,
    ) as workspace_context:
        external_repo = next(
            iter(workspace_context.create_request_context().get_workspace_snapshot().values())
        ).repository_location.get_repository("the_status_in_code_repo")

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
                instance.get_runs()[0],
                execution_time=create_pendulum_time(2019, 2, 28),
                partition_time=create_pendulum_time(2019, 2, 27),
            )

            # Verify idempotence
            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
            assert instance.get_runs_count() == 1
            ticks = instance.get_ticks(always_running_origin.get_id(), running_schedule.selector_id)
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS

        freeze_datetime = freeze_datetime.add(days=2)
        with pendulum.test(freeze_datetime):
            # Traveling two more days in the future before running results in two new ticks
            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
            assert instance.get_runs_count() == 3
            ticks = instance.get_ticks(always_running_origin.get_id(), running_schedule.selector_id)
            assert len(ticks) == 3
            assert len([tick for tick in ticks if tick.status == TickStatus.SUCCESS]) == 3

            runs_by_partition = {run.tags[PARTITION_NAME_TAG]: run for run in instance.get_runs()}

            assert "2019-02-28" in runs_by_partition
            assert "2019-03-01" in runs_by_partition

        # Now try with an error workspace - the job state should not be deleted
        # since its associated with an errored out location
        with pendulum.test(freeze_datetime):
            # pylint: disable=protected-access
            workspace_context._location_entry_dict[
                "test_location"
            ] = workspace_context._location_entry_dict["test_location"]._replace(
                repository_location=None,
                load_error=SerializableErrorInfo("error", [], "error"),
            )

            evaluate_schedules(workspace_context, executor, pendulum.now("UTC"))
            ticks = instance.get_ticks(always_running_origin.get_id(), running_schedule.selector_id)
            assert len(ticks) == 3
            assert len(instance.all_instigator_state()) == 1

    # Now try with an empty workspace - ticks are still there, but the job state is deleted
    # once it's no longer present in the workspace
    with create_test_daemon_workspace_context(
        EmptyWorkspaceTarget(), instance
    ) as empty_workspace_ctx:
        with pendulum.test(freeze_datetime):
            evaluate_schedules(empty_workspace_ctx, executor, pendulum.now("UTC"))
            ticks = instance.get_ticks(always_running_origin.get_id(), running_schedule.selector_id)
            assert len(ticks) == 3
            assert len(instance.all_instigator_state()) == 0


@pytest.mark.parametrize("executor", get_schedule_executors())
def test_change_default_status(instance, executor):
    # Simulate the case where a schedule previously had a default running status set, but is now changed back to default status stopped
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with create_test_daemon_workspace_context(
        workspace_load_target(attribute="the_status_in_code_repo"),
        instance,
    ) as workspace_context:
        external_repo = next(
            iter(workspace_context.create_request_context().get_workspace_snapshot().values())
        ).repository_location.get_repository("the_status_in_code_repo")

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

    freeze_datetime = to_timezone(
        create_pendulum_time(
            year=2019,
            month=2,
            day=27,
            hour=23,
            minute=59,
            second=59,
            tz="UTC",
        ),
        "US/Central",
    )
    with create_test_daemon_workspace_context(
        workspace_load_target=workspace_load_target(attribute=None),  # load all repos
        instance=instance,
    ) as full_workspace_context:

        with pendulum.test(freeze_datetime):
            full_location = next(
                iter(
                    full_workspace_context.create_request_context()
                    .get_workspace_snapshot()
                    .values()
                )
            ).repository_location
            external_repo = full_location.get_repository("the_repo")
            other_repo = full_location.get_repository("the_other_repo")

            # stop always on schedule
            status_in_code_repo = full_location.get_repository("the_status_in_code_repo")
            running_sched = status_in_code_repo.get_external_schedule("always_running_schedule")
            instance.stop_schedule(
                running_sched.get_external_origin_id(), running_sched.selector_id, running_sched
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
