import datetime
import random
import string
import time
from contextlib import contextmanager

import pendulum

from dagster import (
    Any,
    DefaultScheduleStatus,
    Field,
    Partition,
    PartitionSetDefinition,
    ScheduleDefinition,
    daily_schedule,
    hourly_schedule,
    job,
    op,
    pipeline,
    repository,
    schedule,
    solid,
)
from dagster.core.definitions.run_request import RunRequest
from dagster.core.host_representation import (
    ExternalInstigatorOrigin,
    ExternalRepositoryOrigin,
    GrpcServerRepositoryLocation,
    GrpcServerRepositoryLocationOrigin,
)
from dagster.core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    InstigatorType,
    ScheduleInstigatorData,
    TickData,
    TickStatus,
)
from dagster.core.storage.pipeline_run import PipelineRunStatus, RunsFilter
from dagster.core.storage.tags import PARTITION_NAME_TAG, SCHEDULED_EXECUTION_TIME_TAG
from dagster.core.test_utils import (
    create_test_daemon_workspace,
    instance_for_test,
    mock_system_timezone,
)
from dagster.core.workspace.load_target import EmptyWorkspaceTarget, GrpcServerTarget, ModuleTarget
from dagster.daemon import get_default_daemon_logger
from dagster.grpc.client import EphemeralDagsterGrpcClient
from dagster.grpc.server import open_server_process
from dagster.scheduler.scheduler import launch_scheduled_runs
from dagster.seven import wait_for_process
from dagster.seven.compat.pendulum import create_pendulum_time, to_timezone
from dagster.utils import find_free_port
from dagster.utils.partitions import DEFAULT_DATE_FORMAT

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
    pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO, execution_timezone="US/Central"
)
def daily_central_time_schedule(date):
    return _solid_config(date)


@schedule(
    pipeline_name="the_pipeline", cron_schedule="*/5 * * * *", execution_timezone="US/Central"
)
def partitionless_schedule(context):
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


NUM_CALLS = {"calls": 0}


@daily_schedule(  # type: ignore
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_timezone="UTC",
)
def passes_on_retry_schedule(date):
    NUM_CALLS["calls"] = NUM_CALLS["calls"] + 1
    if NUM_CALLS["calls"] > 1:
        return _solid_config(date)
    raise Exception("better luck next time")


@hourly_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_timezone="UTC",
)
def simple_hourly_schedule(date):
    return _solid_config(date)


@hourly_schedule(
    pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO, execution_timezone="US/Central"
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
    pipeline_name="the_pipeline",
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
        pipeline_name="the_pipeline",
        execution_timezone="UTC",
        execution_fn=gen_runs,
    )


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
        pipeline_name="the_pipeline",
        execution_timezone="UTC",
        execution_fn=gen_runs,
    )


@pipeline
def the_other_pipeline():
    the_solid()


@repository
def the_other_repo():
    return [
        the_other_pipeline,
    ]


@solid(config_schema=Field(Any))
def config_solid(_):
    return 1


@pipeline
def config_pipeline():
    config_solid()


@daily_schedule(
    pipeline_name="config_pipeline", start_date=_COUPLE_DAYS_AGO, execution_timezone="UTC"
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


manual_partition = PartitionSetDefinition(
    name="manual_partition",
    pipeline_name="two_step_pipeline",
    # selects only second step
    solid_selection=["end"],
    partition_fn=lambda: [Partition("one")],
    # includes config for first step - test that it is ignored
    run_config_fn_for_partition=lambda _: {"solids": {"start": {"inputs": {"x": {"value": 4}}}}},
)

manual_partition_schedule = manual_partition.create_schedule_definition(
    "manual_partition_schedule", "0 0 * * *", lambda _x, _y: Partition("one")
)


def define_default_config_job():
    @op(config_schema=str)
    def my_op(context):
        assert context.op_config == "foo"

    @job(config={"ops": {"my_op": {"config": "foo"}}})
    def default_config_job():
        my_op()

    return default_config_job


default_config_schedule = ScheduleDefinition(
    name="default_config_schedule", cron_schedule="* * * * *", job=define_default_config_job()
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
        passes_on_retry_schedule,
        bad_should_execute_schedule,
        bad_should_execute_schedule_on_odd_days,
        skip_schedule,
        wrong_config_schedule,
        define_multi_run_schedule(),
        define_multi_run_schedule_with_missing_run_key(),
        partitionless_schedule,
        large_schedule,
        two_step_pipeline,
        manual_partition_schedule,
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
    assert set(tick_data.run_ids) == set(expected_run_ids)
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


def test_simple_schedule(instance, workspace, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("simple_schedule")

        schedule_origin = external_schedule.get_external_origin()

        instance.start_schedule(external_schedule)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

        # launch_scheduled_runs does nothing before the first tick
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id())
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
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )
        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS

    # Verify advancing in time but not going past a tick doesn't add any new runs
    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )
        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS

    freeze_datetime = freeze_datetime.add(days=2)
    with pendulum.test(freeze_datetime):

        # Traveling two more days in the future before running results in two new ticks
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )
        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 3
        assert len([tick for tick in ticks if tick.status == TickStatus.SUCCESS]) == 3

        runs_by_partition = {run.tags[PARTITION_NAME_TAG]: run for run in instance.get_runs()}

        assert "2019-02-28" in runs_by_partition
        assert "2019-03-01" in runs_by_partition

        # Check idempotence again
        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))
        assert instance.get_runs_count() == 3
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 3


def test_old_tick_schedule(instance, workspace, external_repo):
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
            )
        )

        schedule_origin = external_schedule.get_external_origin()

        # the start time is what determines the number of runs, not the last tick
        instance.start_schedule(external_schedule)

    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 2


def test_no_started_schedules(instance, workspace, external_repo):
    external_schedule = external_repo.get_external_schedule("simple_schedule")
    schedule_origin = external_schedule.get_external_origin()

    list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))
    assert instance.get_runs_count() == 0

    ticks = instance.get_ticks(schedule_origin.get_id())
    assert len(ticks) == 0


def test_schedule_without_timezone(instance):
    with mock_system_timezone("US/Eastern"):
        with create_test_daemon_workspace(
            workspace_load_target=workspace_load_target()
        ) as workspace:
            external_repo = next(
                iter(workspace.get_workspace_snapshot().values())
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

                list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

                assert instance.get_runs_count() == 1

                ticks = instance.get_ticks(schedule_origin.get_id())

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
                list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))
                assert instance.get_runs_count() == 1
                ticks = instance.get_ticks(schedule_origin.get_id())
                assert len(ticks) == 1


def test_bad_env_fn_no_retries(instance, workspace, external_repo):
    external_schedule = external_repo.get_external_schedule("bad_env_fn_schedule")
    schedule_origin = external_schedule.get_external_origin()
    initial_datetime = create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0)
    with pendulum.test(initial_datetime):
        instance.start_schedule(external_schedule)

        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
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
        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
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
        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
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


def test_bad_env_fn_with_retries(instance, workspace, external_repo):
    external_schedule = external_repo.get_external_schedule("bad_env_fn_schedule")
    schedule_origin = external_schedule.get_external_origin()
    initial_datetime = create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0)
    with pendulum.test(initial_datetime):
        instance.start_schedule(external_schedule)

        list(
            launch_scheduled_runs(
                instance, workspace, logger(), pendulum.now("UTC"), max_tick_retries=2
            )
        )

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
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

        list(
            launch_scheduled_runs(
                instance, workspace, logger(), pendulum.now("UTC"), max_tick_retries=2
            )
        )
        list(
            launch_scheduled_runs(
                instance, workspace, logger(), pendulum.now("UTC"), max_tick_retries=2
            )
        )

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
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

        list(
            launch_scheduled_runs(
                instance, workspace, logger(), pendulum.now("UTC"), max_tick_retries=2
            )
        )
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
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
        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
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


def test_passes_on_retry(instance, workspace, external_repo):
    external_schedule = external_repo.get_external_schedule("passes_on_retry_schedule")
    schedule_origin = external_schedule.get_external_origin()
    initial_datetime = create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0)
    with pendulum.test(initial_datetime):
        instance.start_schedule(external_schedule)

        list(
            launch_scheduled_runs(
                instance, workspace, logger(), pendulum.now("UTC"), max_tick_retries=1
            )
        )

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_schedule,
            initial_datetime,
            TickStatus.FAILURE,
            [],
            "Error occurred during the execution of run_config_fn for schedule passes_on_retry_schedule",
            expected_failure_count=1,
        )

        list(
            launch_scheduled_runs(
                instance, workspace, logger(), pendulum.now("UTC"), max_tick_retries=1
            )
        )

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id())
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
        list(
            launch_scheduled_runs(
                instance, workspace, logger(), pendulum.now("UTC"), max_tick_retries=1
            )
        )

        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 2

        validate_tick(
            ticks[0],
            external_schedule,
            initial_datetime,
            TickStatus.SUCCESS,
            [instance.get_runs()[0].run_id],
            expected_failure_count=0,
        )


def test_bad_should_execute(instance, workspace, external_repo):
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

        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
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


def test_skip(instance, workspace, external_repo):
    external_schedule = external_repo.get_external_schedule("skip_schedule")
    schedule_origin = external_schedule.get_external_origin()
    initial_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(initial_datetime):
        instance.start_schedule(external_schedule)

        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            external_schedule,
            initial_datetime,
            TickStatus.SKIPPED,
            [run.run_id for run in instance.get_runs()],
            expected_skip_reason="should_execute function for skip_schedule returned false.",
        )


def test_wrong_config_schedule(instance, workspace, external_repo):
    external_schedule = external_repo.get_external_schedule("wrong_config_schedule")
    schedule_origin = external_schedule.get_external_origin()
    initial_datetime = create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0)
    with pendulum.test(initial_datetime):
        instance.start_schedule(external_schedule)

        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

        assert instance.get_runs_count() == 0

        ticks = instance.get_ticks(schedule_origin.get_id())
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


def test_schedule_run_default_config(instance, workspace, external_repo):
    external_schedule = external_repo.get_external_schedule("default_config_schedule")
    schedule_origin = external_schedule.get_external_origin()
    initial_datetime = create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0)
    with pendulum.test(initial_datetime):
        instance.start_schedule(external_schedule)

        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

        assert instance.get_runs_count() == 1

        wait_for_all_runs_to_start(instance)

        run = instance.get_runs()[0]

        validate_run_started(
            instance,
            run,
            execution_time=initial_datetime,
            expected_success=True,
        )

        ticks = instance.get_ticks(schedule_origin.get_id())
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


def test_bad_schedules_mixed_with_good_schedule(instance, workspace, external_repo):
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

        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

        assert instance.get_runs_count() == 1
        wait_for_all_runs_to_start(instance)
        validate_run_started(
            instance,
            instance.get_runs()[0],
            execution_time=initial_datetime,
            partition_time=create_pendulum_time(2019, 2, 26),
        )

        good_ticks = instance.get_ticks(good_origin.get_id())
        assert len(good_ticks) == 1
        validate_tick(
            good_ticks[0],
            good_schedule,
            initial_datetime,
            TickStatus.SUCCESS,
            [run.run_id for run in instance.get_runs()],
        )

        bad_ticks = instance.get_ticks(bad_origin.get_id())
        assert len(bad_ticks) == 1

        assert bad_ticks[0].status == TickStatus.FAILURE

        assert (
            "Error occurred during the execution of should_execute for schedule bad_should_execute_schedule"
            in bad_ticks[0].error.message
        )

        unloadable_ticks = instance.get_ticks(unloadable_origin.get_id())
        assert len(unloadable_ticks) == 0

    initial_datetime = initial_datetime.add(days=1)
    with pendulum.test(initial_datetime):
        new_now = pendulum.now("UTC")
        list(launch_scheduled_runs(instance, workspace, logger(), new_now))

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

        good_ticks = instance.get_ticks(good_origin.get_id())
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

        bad_ticks = instance.get_ticks(bad_origin.get_id())
        assert len(bad_ticks) == 2
        validate_tick(
            bad_ticks[0],
            bad_schedule,
            new_now,
            TickStatus.SUCCESS,
            [bad_schedule_runs[0].run_id],
        )

        unloadable_ticks = instance.get_ticks(unloadable_origin.get_id())
        assert len(unloadable_ticks) == 0


def test_run_scheduled_on_time_boundary(instance, workspace, external_repo):
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

        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS


def test_bad_load_repository(instance, workspace, external_repo, caplog):
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
        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

        assert instance.get_runs_count() == 0

        ticks = instance.get_ticks(invalid_repo_origin.get_id())

        assert len(ticks) == 0

        assert (
            "Could not find repository invalid_repo_name in location test_location to run schedule simple_schedule"
            in caplog.text
        )


def test_bad_load_schedule(instance, workspace, external_repo, caplog):
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
        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

        assert instance.get_runs_count() == 0

        ticks = instance.get_ticks(invalid_repo_origin.get_id())

        assert len(ticks) == 0

        assert "Could not find schedule invalid_schedule in repository the_repo." in caplog.text


def test_error_load_repository_location(instance):
    with create_test_daemon_workspace(_get_unloadable_workspace_load_target()) as workspace:
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
            list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

            assert instance.get_runs_count() == 0

            ticks = instance.get_ticks(fake_origin.get_id())

            assert len(ticks) == 0

        initial_datetime = initial_datetime.add(days=1)
        with pendulum.test(initial_datetime):
            list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))
            assert instance.get_runs_count() == 0
            ticks = instance.get_ticks(fake_origin.get_id())
            assert len(ticks) == 0


def test_load_repository_location_not_in_workspace(instance, workspace, external_repo, caplog):
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
        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

        assert instance.get_runs_count() == 0

        ticks = instance.get_ticks(invalid_repo_origin.get_id())

        assert len(ticks) == 0

        assert (
            "Schedule simple_schedule was started from a location missing_location that can no longer be found in the workspace"
            in caplog.text
        )


def test_multiple_schedules_on_different_time_ranges(instance, workspace, external_repo):
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
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )

        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(external_schedule.get_external_origin_id())
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS

        hourly_ticks = instance.get_ticks(external_hourly_schedule.get_external_origin_id())
        assert len(hourly_ticks) == 1
        assert hourly_ticks[0].status == TickStatus.SUCCESS

    initial_datetime = initial_datetime.add(hours=1)
    with pendulum.test(initial_datetime):
        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

        assert instance.get_runs_count() == 3

        ticks = instance.get_ticks(external_schedule.get_external_origin_id())
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS

        hourly_ticks = instance.get_ticks(external_hourly_schedule.get_external_origin_id())
        assert len(hourly_ticks) == 2
        assert len([tick for tick in hourly_ticks if tick.status == TickStatus.SUCCESS]) == 2


def test_launch_failure(workspace, external_repo):
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster.core.test_utils",
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
            instance.start_schedule(external_schedule)

            list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

            assert instance.get_runs_count() == 1

            run = instance.get_runs()[0]

            validate_run_started(
                instance,
                run,
                execution_time=initial_datetime,
                partition_time=create_pendulum_time(2019, 2, 26),
                expected_success=False,
            )

            ticks = instance.get_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                TickStatus.SUCCESS,
                [run.run_id for run in instance.get_runs()],
            )


def test_partitionless_schedule(instance, workspace, external_repo):
    initial_datetime = create_pendulum_time(year=2019, month=2, day=27, tz="US/Central")
    with pendulum.test(initial_datetime):
        external_schedule = external_repo.get_external_schedule("partitionless_schedule")
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

    # Travel enough in the future that many ticks have passed, but only one run executes
    initial_datetime = initial_datetime.add(days=5)
    with pendulum.test(initial_datetime):
        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))
        assert instance.get_runs_count() == 1

        wait_for_all_runs_to_start(instance)

        ticks = instance.get_ticks(schedule_origin.get_id())
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


def test_max_catchup_runs(instance, workspace, external_repo):
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
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
                max_catchup_runs=2,
            )
        )

        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(schedule_origin.get_id())
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


def test_multi_runs(instance, workspace, external_repo):
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
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

        # launch_scheduled_runs does nothing before the first tick
        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

    freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum.test(freeze_datetime):
        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))
        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(schedule_origin.get_id())
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
        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))
        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.SUCCESS

    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):

        # Traveling one more day in the future before running results in a tick
        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))
        assert instance.get_runs_count() == 4
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 2
        assert len([tick for tick in ticks if tick.status == TickStatus.SUCCESS]) == 2
        runs = instance.get_runs()


def test_multi_runs_missing_run_key(instance, workspace, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"), "US/Central"
    )
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule(
            "multi_run_schedule_with_missing_run_key"
        )
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)

        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
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


def test_large_schedule(instance, workspace, external_repo):
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
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 1


def test_manual_partition_with_solid_selection(instance, workspace, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("manual_partition_schedule")
        schedule_origin = external_schedule.get_external_origin()
        instance.start_schedule(external_schedule)
        freeze_datetime = freeze_datetime.add(seconds=2)

    with pendulum.test(freeze_datetime):
        list(
            launch_scheduled_runs(
                instance,
                workspace,
                logger(),
                pendulum.now("UTC"),
            )
        )

        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(schedule_origin.get_id())
        assert len(ticks) == 1
        run_id = ticks[0].run_ids[0]

        assert instance.get_run_by_id(run_id).solid_selection == ["end"]  # matches solid_selection


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


def test_skip_reason_schedule(instance, workspace, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=28, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        external_schedule = external_repo.get_external_schedule("empty_schedule")

        schedule_origin = external_schedule.get_external_origin()

        instance.start_schedule(external_schedule)

        list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(schedule_origin.get_id())
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


def test_grpc_server_down(instance):
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
    with create_test_daemon_workspace(
        GrpcServerTarget(host="localhost", port=port, socket=None, location_name="test_location")
    ) as workspace:
        with pendulum.test(initial_datetime):
            with _grpc_server_external_repo(port) as external_repo:
                external_schedule = external_repo.get_external_schedule("simple_schedule")
                instance.start_schedule(external_schedule)
                workspace.get_location(location_origin.location_name)

            # Server is no longer running, ticks fail but indicate it will resume once it is reachable
            for _trial in range(3):
                list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))
                assert instance.get_runs_count() == 0
                ticks = instance.get_ticks(schedule_origin.get_id())
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
                list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))
                assert instance.get_runs_count() == 1
                ticks = instance.get_ticks(schedule_origin.get_id())
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
def test_status_in_code_schedule(instance):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with create_test_daemon_workspace(
        workspace_load_target(attribute="the_status_in_code_repo")
    ) as workspace:
        external_repo = next(
            iter(workspace.get_workspace_snapshot().values())
        ).repository_location.get_repository("the_status_in_code_repo")

        with pendulum.test(freeze_datetime):
            running_schedule = external_repo.get_external_schedule("always_running_schedule")
            not_running_schedule = external_repo.get_external_schedule("never_running_schedule")

            always_running_origin = running_schedule.get_external_origin()
            never_running_origin = not_running_schedule.get_external_origin()

            assert instance.get_runs_count() == 0
            assert len(instance.get_ticks(always_running_origin.get_id())) == 0
            assert len(instance.get_ticks(never_running_origin.get_id())) == 0

            assert len(instance.all_instigator_state()) == 0

            list(launch_scheduled_runs(instance, workspace, logger(), pendulum.now("UTC")))

            # No runs, but the job state is updated to set a checkpoing
            assert instance.get_runs_count() == 0

            assert len(instance.all_instigator_state()) == 1

            instigator_state = instance.get_instigator_state(always_running_origin.get_id())

            assert instigator_state.status == InstigatorStatus.AUTOMATICALLY_RUNNING
            assert (
                instigator_state.instigator_data.start_timestamp == pendulum.now("UTC").timestamp()
            )

            ticks = instance.get_ticks(always_running_origin.get_id())
            assert len(ticks) == 0

            assert len(instance.get_ticks(never_running_origin.get_id())) == 0

        freeze_datetime = freeze_datetime.add(seconds=2)
        with pendulum.test(freeze_datetime):
            list(
                launch_scheduled_runs(
                    instance,
                    workspace,
                    logger(),
                    pendulum.now("UTC"),
                )
            )

            assert instance.get_runs_count() == 1

            assert len(instance.get_ticks(never_running_origin.get_id())) == 0

            ticks = instance.get_ticks(always_running_origin.get_id())

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
            list(
                launch_scheduled_runs(
                    instance,
                    workspace,
                    logger(),
                    pendulum.now("UTC"),
                )
            )
            assert instance.get_runs_count() == 1
            ticks = instance.get_ticks(always_running_origin.get_id())
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS

        freeze_datetime = freeze_datetime.add(days=2)
        with pendulum.test(freeze_datetime):
            # Traveling two more days in the future before running results in two new ticks
            list(
                launch_scheduled_runs(
                    instance,
                    workspace,
                    logger(),
                    pendulum.now("UTC"),
                )
            )
            assert instance.get_runs_count() == 3
            ticks = instance.get_ticks(always_running_origin.get_id())
            assert len(ticks) == 3
            assert len([tick for tick in ticks if tick.status == TickStatus.SUCCESS]) == 3

            runs_by_partition = {run.tags[PARTITION_NAME_TAG]: run for run in instance.get_runs()}

            assert "2019-02-28" in runs_by_partition
            assert "2019-03-01" in runs_by_partition

    # Now try with an empty workspace - ticks are still there, but the job state is deleted
    # once it's no longer present in the workspace
    with create_test_daemon_workspace(EmptyWorkspaceTarget()) as empty_workspace:
        with pendulum.test(freeze_datetime):
            list(
                launch_scheduled_runs(
                    instance,
                    empty_workspace,
                    logger(),
                    pendulum.now("UTC"),
                )
            )
            ticks = instance.get_ticks(always_running_origin.get_id())
            assert len(ticks) == 3
            assert len(instance.all_instigator_state()) == 0


def test_change_default_status(instance):
    # Simulate the case where a schedule previously had a default running status set, but is now changed back to default status stopped
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with create_test_daemon_workspace(
        workspace_load_target(attribute="the_status_in_code_repo")
    ) as workspace:
        external_repo = next(
            iter(workspace.get_workspace_snapshot().values())
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
            list(
                launch_scheduled_runs(
                    instance,
                    workspace,
                    logger(),
                    pendulum.now("UTC"),
                )
            )

            ticks = instance.get_ticks(never_running_origin.get_id())
            assert len(ticks) == 0

            # AUTOMATICALLY_RUNNING row has been removed from the database
            instigator_state = instance.get_instigator_state(never_running_origin.get_id())
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

            list(
                launch_scheduled_runs(
                    instance,
                    workspace,
                    logger(),
                    pendulum.now("UTC"),
                )
            )

            ticks = instance.get_ticks(never_running_origin.get_id())
            assert len(ticks) == 1
            assert len(ticks[0].run_ids) == 1
            assert ticks[0].timestamp == freeze_datetime.timestamp()
            assert ticks[0].status == TickStatus.SUCCESS
