import os
import random
import string
import sys
import tempfile
import time
from contextlib import ExitStack, contextmanager
from unittest import mock

import pendulum
import pytest
from dagster import (
    Any,
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    AssetSelection,
    CodeLocationSelector,
    DagsterRunStatus,
    Field,
    HourlyPartitionsDefinition,
    JobSelector,
    Output,
    RepositorySelector,
    SourceAsset,
    WeeklyPartitionsDefinition,
    asset,
    build_asset_reconciliation_sensor,
    define_asset_job,
    graph,
    load_assets_from_current_module,
    materialize,
    multi_asset_sensor,
    repository,
    run_failure_sensor,
)
from dagster._core.definitions.decorators import op
from dagster._core.definitions.decorators.sensor_decorator import asset_sensor, sensor
from dagster._core.definitions.instigation_logger import get_instigation_log_records
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.definitions.run_status_sensor_definition import run_status_sensor
from dagster._core.definitions.sensor_definition import DefaultSensorStatus, RunRequest, SkipReason
from dagster._core.events import DagsterEventType
from dagster._core.execution.api import execute_pipeline
from dagster._core.host_representation import ExternalInstigatorOrigin, ExternalRepositoryOrigin
from dagster._core.instance import DagsterInstance
from dagster._core.log_manager import DAGSTER_META_KEY
from dagster._core.scheduler.instigation import InstigatorState, InstigatorStatus, TickStatus
from dagster._core.storage.event_log.base import EventRecordsFilter
from dagster._core.test_utils import (
    SingleThreadPoolExecutor,
    create_test_daemon_workspace_context,
    instance_for_test,
    wait_for_futures,
)
from dagster._daemon import get_default_daemon_logger
from dagster._daemon.sensor import execute_sensor_iteration, execute_sensor_iteration_loop
from dagster._legacy import pipeline
from dagster._seven.compat.pendulum import create_pendulum_time, to_timezone

from .conftest import create_workspace_load_target


@asset
def a():
    return 1


@asset
def b(a):
    return a + 1


@asset
def c(a):
    return a + 2


asset_job = define_asset_job("abc", selection=AssetSelection.keys("c", "b").upstream())


@op
def the_solid(_):
    return 1


@pipeline
def the_pipeline():
    the_solid()


@graph()
def the_graph():
    the_solid()


the_job = the_graph.to_job()


@op(config_schema=Field(Any))
def config_solid(_):
    return 1


@pipeline
def config_pipeline():
    config_solid()


@graph()
def config_graph():
    config_solid()


@op
def foo_solid():
    yield AssetMaterialization(asset_key=AssetKey("foo"))
    yield Output(1)


@pipeline
def foo_pipeline():
    foo_solid()


@op
def foo_observation_solid():
    yield AssetObservation(asset_key=AssetKey("foo"), metadata={"text": "FOO"})
    yield Output(5)


@pipeline
def foo_observation_pipeline():
    foo_observation_solid()


@op
def hanging_solid():
    start_time = time.time()
    while True:
        if time.time() - start_time > 10:
            return
        time.sleep(0.5)


@pipeline
def hanging_pipeline():
    hanging_solid()


@op
def failure_solid():
    raise Exception("womp womp")


@pipeline
def failure_pipeline():
    failure_solid()


@graph()
def failure_graph():
    failure_solid()


failure_job = failure_graph.to_job()


@sensor(job_name="the_pipeline")
def simple_sensor(context):
    if not context.last_completion_time or not int(context.last_completion_time) % 2:
        return SkipReason()

    return RunRequest(run_key=None, run_config={}, tags={})


@sensor(job_name="the_pipeline")
def always_on_sensor(_context):
    return RunRequest(run_key=None, run_config={}, tags={})


@sensor(job_name="the_pipeline")
def run_key_sensor(_context):
    return RunRequest(run_key="only_once", run_config={}, tags={})


@sensor(job_name="the_pipeline")
def error_sensor(context):
    context.update_cursor("the exception below should keep this from being persisted")
    raise Exception("womp womp")


@sensor(job_name="the_pipeline")
def wrong_config_sensor(_context):
    return RunRequest(run_key="bad_config_key", run_config={"bad_key": "bad_val"}, tags={})


@sensor(job_name="the_pipeline", minimum_interval_seconds=60)
def custom_interval_sensor(_context):
    return SkipReason()


@sensor(job_name="the_pipeline")
def skip_cursor_sensor(context):
    if not context.cursor:
        cursor = 1
    else:
        cursor = int(context.cursor) + 1

    context.update_cursor(str(cursor))
    return SkipReason()


@sensor(job_name="the_pipeline")
def run_cursor_sensor(context):
    if not context.cursor:
        cursor = 1
    else:
        cursor = int(context.cursor) + 1

    context.update_cursor(str(cursor))
    return RunRequest(run_key=None, run_config={}, tags={})


@asset
def asset_a():
    return 1


@asset
def asset_b():
    return 2


@asset
def asset_c(asset_b):  # pylint: disable=unused-argument
    return 3


@multi_asset_sensor(monitored_assets=[AssetKey("asset_a"), AssetKey("asset_b")], job=the_job)
def asset_a_and_b_sensor(context):
    asset_events = context.latest_materialization_records_by_key()
    if all(asset_events.values()):
        context.advance_all_cursors()
        return RunRequest(run_key=f"{context.cursor}", run_config={})


@multi_asset_sensor(monitored_assets=[AssetKey("asset_a"), AssetKey("asset_b")], job=the_job)
def doesnt_update_cursor_sensor(context):
    asset_events = context.latest_materialization_records_by_key()
    if any(asset_events.values()):
        # doesn't update cursor, should raise exception
        return RunRequest(run_key=f"{context.cursor}", run_config={})


@multi_asset_sensor(monitored_assets=[AssetKey("asset_a")], job=the_job)
def backlog_sensor(context):
    asset_events = context.materialization_records_for_key(asset_key=AssetKey("asset_a"), limit=2)
    if len(asset_events) == 2:
        context.advance_cursor({AssetKey("asset_a"): asset_events[-1]})
        return RunRequest(run_key=f"{context.cursor}", run_config={})


@multi_asset_sensor(monitored_assets=AssetSelection.keys("asset_c").upstream(include_self=False))
def asset_selection_sensor(context):
    assert context.asset_keys == [AssetKey("asset_b")]
    assert context.latest_materialization_records_by_key().keys() == {AssetKey("asset_b")}


@sensor(asset_selection=AssetSelection.keys("asset_a", "asset_b"))
def targets_asset_selection_sensor():
    return [RunRequest(), RunRequest(asset_selection=[AssetKey("asset_b")])]


@multi_asset_sensor(
    monitored_assets=AssetSelection.keys("asset_b"), request_assets=AssetSelection.keys("asset_c")
)
def multi_asset_sensor_targets_asset_selection(context):
    asset_events = context.latest_materialization_records_by_key()
    if all(asset_events.values()):
        context.advance_all_cursors()
        return RunRequest()


hourly_partitions_def_2022 = HourlyPartitionsDefinition(start_date="2022-08-01-00:00")


@asset(partitions_def=hourly_partitions_def_2022)
def hourly_asset():
    return 1


@asset(partitions_def=hourly_partitions_def_2022)
def hourly_asset_2():
    return 1


@asset(partitions_def=hourly_partitions_def_2022)
def hourly_asset_3():
    return 1


hourly_asset_job = define_asset_job(
    "hourly_asset_job",
    AssetSelection.keys("hourly_asset_3"),
    partitions_def=hourly_partitions_def_2022,
)


weekly_partitions_def = WeeklyPartitionsDefinition(start_date="2020-01-01")


@asset(partitions_def=weekly_partitions_def)
def weekly_asset():
    return 1


weekly_asset_job = define_asset_job(
    "weekly_asset_job", AssetSelection.keys("weekly_asset"), partitions_def=weekly_partitions_def
)


@multi_asset_sensor(monitored_assets=[hourly_asset.key], job=weekly_asset_job)
def multi_asset_sensor_hourly_to_weekly(context):
    for partition, materialization in context.latest_materialization_records_by_partition(
        hourly_asset.key
    ).items():
        mapped_partitions = context.get_downstream_partition_keys(
            partition, to_asset_key=weekly_asset.key, from_asset_key=hourly_asset.key
        )
        for mapped_partition in mapped_partitions:
            yield weekly_asset_job.run_request_for_partition(
                partition_key=mapped_partition, run_key=None
            )

        context.advance_cursor({hourly_asset.key: materialization})


@multi_asset_sensor(monitored_assets=[hourly_asset.key], job=hourly_asset_job)
def multi_asset_sensor_hourly_to_hourly(context):
    materialization_by_partition = context.latest_materialization_records_by_partition(
        hourly_asset.key
    )

    latest_partition = None
    for partition, materialization in materialization_by_partition.items():
        if materialization:
            mapped_partitions = context.get_downstream_partition_keys(
                partition, to_asset_key=hourly_asset_3.key, from_asset_key=hourly_asset.key
            )
            for mapped_partition in mapped_partitions:
                yield hourly_asset_job.run_request_for_partition(
                    partition_key=mapped_partition, run_key=None
                )

            latest_partition = (
                partition if latest_partition is None else max(latest_partition, partition)
            )

    if latest_partition:
        context.advance_cursor({hourly_asset.key: materialization_by_partition[latest_partition]})


def _random_string(length):
    return "".join(random.choice(string.ascii_lowercase) for x in range(length))


@sensor(job_name="config_pipeline")
def large_sensor(_context):
    # create a gRPC response payload larger than the limit (4194304)
    REQUEST_COUNT = 25
    REQUEST_TAG_COUNT = 5000
    REQUEST_CONFIG_COUNT = 100

    for _ in range(REQUEST_COUNT):
        tags_garbage = {_random_string(10): _random_string(20) for i in range(REQUEST_TAG_COUNT)}
        config_garbage = {
            _random_string(10): _random_string(20) for i in range(REQUEST_CONFIG_COUNT)
        }
        config = {"solids": {"config_solid": {"config": {"foo": config_garbage}}}}
        yield RunRequest(run_key=None, run_config=config, tags=tags_garbage)


@sensor(job=asset_job)
def run_request_asset_selection_sensor(_context):
    yield RunRequest(run_key=None, asset_selection=[AssetKey("a"), AssetKey("b")])


@sensor(job=asset_job)
def run_request_stale_asset_sensor(_context):
    yield RunRequest(run_key=None, stale_assets_only=True)


@sensor(job=hourly_asset_job)
def partitioned_asset_selection_sensor(_context):
    return hourly_asset_job.run_request_for_partition(
        partition_key="2022-08-01-00:00", run_key=None, asset_selection=[AssetKey("hourly_asset_3")]
    )


@asset_sensor(job_name="the_pipeline", asset_key=AssetKey("foo"))
def asset_foo_sensor(context, _event):
    return RunRequest(run_key=context.cursor, run_config={})


@asset_sensor(asset_key=AssetKey("foo"), job=the_job)
def asset_job_sensor(context, _event):
    return RunRequest(run_key=context.cursor, run_config={})


@run_failure_sensor
def my_run_failure_sensor(context):
    assert isinstance(context.instance, DagsterInstance)


@run_failure_sensor(monitored_jobs=[failure_job])
def my_run_failure_sensor_filtered(context):
    assert isinstance(context.instance, DagsterInstance)


@run_failure_sensor()
def my_run_failure_sensor_that_itself_fails(context):
    raise Exception("How meta")


@run_status_sensor(run_status=DagsterRunStatus.SUCCESS)
def my_pipeline_success_sensor(context):
    assert isinstance(context.instance, DagsterInstance)


@run_status_sensor(run_status=DagsterRunStatus.STARTED)
def my_pipeline_started_sensor(context):
    assert isinstance(context.instance, DagsterInstance)


config_job = config_graph.to_job()


@sensor(jobs=[the_job, config_job])
def two_job_sensor(context):
    counter = int(context.cursor) if context.cursor else 0
    if counter % 2 == 0:
        yield RunRequest(run_key=str(counter), job_name=the_job.name)
    else:
        yield RunRequest(
            run_key=str(counter),
            job_name=config_job.name,
            run_config={"solids": {"config_solid": {"config": {"foo": "blah"}}}},
        )
    context.update_cursor(str(counter + 1))


@sensor()
def bad_request_untargeted(_ctx):
    yield RunRequest(run_key=None, job_name="should_fail")


@sensor(job=the_job)
def bad_request_mismatch(_ctx):
    yield RunRequest(run_key=None, job_name="config_pipeline")


@sensor(jobs=[the_job, config_job])
def bad_request_unspecified(_ctx):
    yield RunRequest(run_key=None)


@sensor(job=the_job)
def request_list_sensor(_ctx):
    return [RunRequest(run_key="1"), RunRequest(run_key="2")]


@run_status_sensor(
    monitored_jobs=[
        JobSelector(
            location_name="test_location",
            repository_name="the_other_repo",
            job_name="the_pipeline",
        )
    ],
    run_status=DagsterRunStatus.SUCCESS,
    request_job=the_job,
)
def cross_repo_job_sensor(_ctx):
    from time import time

    return RunRequest(run_key=str(time()))


@run_status_sensor(
    monitored_jobs=[
        RepositorySelector(
            location_name="test_location",
            repository_name="the_other_repo",
        )
    ],
    run_status=DagsterRunStatus.SUCCESS,
)
def cross_repo_sensor(context):
    assert isinstance(context.instance, DagsterInstance)


@run_status_sensor(
    monitor_all_repositories=True,
    run_status=DagsterRunStatus.SUCCESS,
)
def instance_sensor(context):
    assert isinstance(context.instance, DagsterInstance)


@sensor(job=the_job)
def logging_sensor(context):
    context.log.info("hello hello")
    return SkipReason()


@run_status_sensor(
    monitor_all_repositories=True,
    run_status=DagsterRunStatus.SUCCESS,
)
def logging_status_sensor(context):
    context.log.info(f"run succeeded: {context.dagster_run.run_id}")


@repository
def the_repo():
    return [
        the_pipeline,
        the_job,
        config_pipeline,
        config_job,
        foo_pipeline,
        large_sensor,
        simple_sensor,
        error_sensor,
        wrong_config_sensor,
        always_on_sensor,
        run_key_sensor,
        custom_interval_sensor,
        skip_cursor_sensor,
        run_cursor_sensor,
        asset_foo_sensor,
        asset_job_sensor,
        my_run_failure_sensor,
        my_run_failure_sensor_filtered,
        my_run_failure_sensor_that_itself_fails,
        my_pipeline_success_sensor,
        my_pipeline_started_sensor,
        failure_pipeline,
        failure_job,
        hanging_pipeline,
        two_job_sensor,
        bad_request_untargeted,
        bad_request_mismatch,
        bad_request_unspecified,
        request_list_sensor,
        asset_a_and_b_sensor,
        doesnt_update_cursor_sensor,
        backlog_sensor,
        cross_repo_sensor,
        cross_repo_job_sensor,
        instance_sensor,
        load_assets_from_current_module(),
        run_request_asset_selection_sensor,
        run_request_stale_asset_sensor,
        weekly_asset_job,
        multi_asset_sensor_hourly_to_weekly,
        multi_asset_sensor_hourly_to_hourly,
        partitioned_asset_selection_sensor,
        asset_selection_sensor,
        targets_asset_selection_sensor,
        multi_asset_sensor_targets_asset_selection,
        logging_sensor,
        logging_status_sensor,
    ]


@repository
def the_other_repo():
    return [
        the_pipeline,
        run_key_sensor,
    ]


@sensor(job_name="the_pipeline", default_status=DefaultSensorStatus.RUNNING)
def always_running_sensor(context):
    if not context.last_completion_time or not int(context.last_completion_time) % 2:
        return SkipReason()

    return RunRequest(run_key=None, run_config={}, tags={})


@sensor(job_name="the_pipeline", default_status=DefaultSensorStatus.STOPPED)
def never_running_sensor(context):
    if not context.last_completion_time or not int(context.last_completion_time) % 2:
        return SkipReason()

    return RunRequest(run_key=None, run_config={}, tags={})


@repository
def the_status_in_code_repo():
    return [
        the_pipeline,
        always_running_sensor,
        never_running_sensor,
    ]


@asset
def x():
    return 1


@asset
def y(x):
    return x + 1


@asset
def z():
    return 2


@asset
def d(x, z):
    return x + z


@asset
def e():
    return 3


@asset
def f(z, e):
    return z + e


@asset
def g(d, f):
    return d + f


@asset
def h():
    return 1


@asset
def i(h):
    return h + 1


@asset
def sleeper():
    from time import sleep

    sleep(30)
    return 1


@asset
def waits_on_sleep(sleeper, x):
    return sleeper + x


@asset
def a_source_asset():
    return 1


source_asset_source = SourceAsset(key=AssetKey("a_source_asset"))


@asset
def depends_on_source(a_source_asset):
    return a_source_asset + 1


@repository
def with_source_asset_repo():
    return [a_source_asset]


@multi_asset_sensor(monitored_assets=[AssetKey("a_source_asset")], job=the_job)
def monitor_source_asset_sensor(context):
    asset_events = context.latest_materialization_records_by_key()
    if all(asset_events.values()):
        context.advance_all_cursors()
        return RunRequest(run_key=f"{context.cursor}", run_config={})


@repository
def asset_sensor_repo():
    return [
        x,
        y,
        z,
        d,
        e,
        f,
        g,
        h,
        i,
        sleeper,
        waits_on_sleep,
        source_asset_source,
        depends_on_source,
        the_job,
        monitor_source_asset_sensor,
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(y),
            name="just_y_OR",
        ),
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(d),
            name="just_d_OR",
        ),
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(d, f),
            name="d_and_f_OR",
        ),
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(d, f, g),
            name="d_and_f_and_g_OR",
        ),
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(y, d),
            name="y_and_d_OR",
        ),
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(y, i),
            name="y_and_i_OR",
        ),
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(g),
            name="just_g_OR",
        ),
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(y),
            name="just_y_AND",
            run_tags={"hello": "world"},
        ),
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(d),
            name="just_d_AND",
        ),
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(d, f),
            name="d_and_f_AND",
        ),
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(d, f, g),
            name="d_and_f_and_g_AND",
        ),
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(y, d),
            name="y_and_d_AND",
        ),
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(y, i),
            name="y_and_i_AND",
        ),
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(g),
            name="just_g_AND",
        ),
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(waits_on_sleep),
            name="in_progress_condition_sensor",
        ),
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.assets(depends_on_source),
            name="source_asset_sensor",
        ),
    ]


def get_sensor_executors():
    is_buildkite = os.getenv("BUILDKITE") is not None
    return [
        pytest.param(
            None,
            marks=pytest.mark.skipif(
                is_buildkite and sys.version_info.minor != 9, reason="timeouts"
            ),
            id="synchronous",
        ),
        pytest.param(
            SingleThreadPoolExecutor(),
            marks=pytest.mark.skipif(
                is_buildkite and sys.version_info.minor != 9, reason="timeouts"
            ),
            id="threadpool",
        ),
    ]


def evaluate_sensors(workspace_context, executor, timeout=75):
    logger = get_default_daemon_logger("SensorDaemon")
    futures = {}
    list(
        execute_sensor_iteration(
            workspace_context,
            logger,
            threadpool_executor=executor,
            sensor_tick_futures=futures,
        )
    )

    wait_for_futures(futures, timeout=timeout)


def validate_tick(
    tick,
    external_sensor,
    expected_datetime,
    expected_status,
    expected_run_ids=None,
    expected_error=None,
):
    tick_data = tick.tick_data
    assert tick_data.instigator_origin_id == external_sensor.get_external_origin_id()
    assert tick_data.instigator_name == external_sensor.name
    assert tick_data.instigator_type == InstigatorType.SENSOR
    assert tick_data.status == expected_status
    assert tick_data.timestamp == expected_datetime.timestamp()
    if expected_run_ids is not None:
        assert set(tick_data.run_ids) == set(expected_run_ids)
    if expected_error:
        assert expected_error in str(tick_data.error)


def validate_run_started(run, expected_success=True):
    if expected_success:
        assert (
            run.status == DagsterRunStatus.STARTED
            or run.status == DagsterRunStatus.SUCCESS
            or run.status == DagsterRunStatus.STARTING
        )
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


def wait_for_all_runs_to_finish(instance, timeout=10):
    start_time = time.time()
    FINISHED_STATES = [
        DagsterRunStatus.SUCCESS,
        DagsterRunStatus.FAILURE,
        DagsterRunStatus.CANCELED,
    ]
    while True:
        if time.time() - start_time > timeout:
            raise Exception("Timed out waiting for runs to finish")
        time.sleep(0.5)

        not_finished_runs = [
            run for run in instance.get_runs() if run.status not in FINISHED_STATES
        ]

        if len(not_finished_runs) == 0:
            break


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_simple_sensor(instance, workspace_context, external_repo, executor):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )

    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("simple_sensor")
        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 0

        evaluate_sensors(workspace_context, executor)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            external_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime.add(seconds=30)

    with pendulum.test(freeze_datetime):
        evaluate_sensors(workspace_context, executor)
        wait_for_all_runs_to_start(instance)
        assert instance.get_runs_count() == 1
        run = instance.get_runs()[0]
        validate_run_started(run)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 2

        expected_datetime = create_pendulum_time(
            year=2019, month=2, day=28, hour=0, minute=0, second=29
        )
        validate_tick(
            ticks[0],
            external_sensor,
            expected_datetime,
            TickStatus.SUCCESS,
            [run.run_id],
        )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_sensors_keyed_on_selector_not_origin(instance, workspace_context, external_repo, executor):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )

    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("simple_sensor")

        existing_origin = external_sensor.get_external_origin()

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

        instance.add_instigator_state(
            InstigatorState(
                modified_origin,
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )

        evaluate_sensors(workspace_context, executor)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 1


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_bad_load_sensor_repository(caplog, executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )

    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("simple_sensor")

        valid_origin = external_sensor.get_external_origin()

        # Swap out a new repository name
        invalid_repo_origin = ExternalInstigatorOrigin(
            ExternalRepositoryOrigin(
                valid_origin.external_repository_origin.repository_location_origin,
                "invalid_repo_name",
            ),
            valid_origin.instigator_name,
        )

        invalid_state = instance.add_instigator_state(
            InstigatorState(invalid_repo_origin, InstigatorType.SENSOR, InstigatorStatus.RUNNING)
        )

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(invalid_state.instigator_origin_id, invalid_state.selector_id)
        assert len(ticks) == 0

        evaluate_sensors(workspace_context, executor)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(invalid_state.instigator_origin_id, invalid_state.selector_id)
        assert len(ticks) == 0

        assert (
            "Could not find repository invalid_repo_name in location test_location to run sensor"
            " simple_sensor"
            in caplog.text
        )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_bad_load_sensor(caplog, executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )

    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("simple_sensor")

        valid_origin = external_sensor.get_external_origin()

        # Swap out a new repository name
        invalid_repo_origin = ExternalInstigatorOrigin(
            valid_origin.external_repository_origin,
            "invalid_sensor",
        )

        invalid_state = instance.add_instigator_state(
            InstigatorState(invalid_repo_origin, InstigatorType.SENSOR, InstigatorStatus.RUNNING)
        )

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(invalid_state.instigator_origin_id, invalid_state.selector_id)
        assert len(ticks) == 0

        evaluate_sensors(workspace_context, executor)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(invalid_state.instigator_origin_id, invalid_state.selector_id)
        assert len(ticks) == 0

        assert "Could not find sensor invalid_sensor in repository the_repo." in caplog.text


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_error_sensor(caplog, executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("error_sensor")
        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )

        state = instance.get_instigator_state(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert state.instigator_data is None

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 0

        evaluate_sensors(workspace_context, executor)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            external_sensor,
            freeze_datetime,
            TickStatus.FAILURE,
            [],
            "Error occurred during the execution of evaluation_fn for sensor error_sensor",
        )

        assert (
            "Error occurred during the execution of evaluation_fn for sensor error_sensor"
            in caplog.text
        )

        # Tick updated the sensor's last tick time, but not its cursor (due to the failure)
        state = instance.get_instigator_state(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert state.instigator_data.cursor is None
        assert state.instigator_data.last_tick_timestamp == freeze_datetime.timestamp()


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_wrong_config_sensor(caplog, executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(
            year=2019,
            month=2,
            day=27,
            hour=23,
            minute=59,
            second=59,
        ),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("wrong_config_sensor")
        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 0

        evaluate_sensors(workspace_context, executor)
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 1

        validate_tick(
            ticks[0],
            external_sensor,
            freeze_datetime,
            TickStatus.FAILURE,
            [],
            "Error in config for pipeline",
        )

        assert "Error in config for pipeline" in caplog.text

    freeze_datetime = freeze_datetime.add(seconds=60)
    caplog.clear()
    with pendulum.test(freeze_datetime):
        # Error repeats on subsequent ticks

        evaluate_sensors(workspace_context, executor)
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 2

        validate_tick(
            ticks[0],
            external_sensor,
            freeze_datetime,
            TickStatus.FAILURE,
            [],
            "Error in config for pipeline",
        )

        assert "Error in config for pipeline" in caplog.text


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_launch_failure(caplog, executor, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster._core.test_utils",
                "class": "ExplodingRunLauncher",
            },
        },
    ) as instance:
        with pendulum.test(freeze_datetime):
            exploding_workspace_context = workspace_context.copy_for_test_instance(instance)
            external_sensor = external_repo.get_external_sensor("always_on_sensor")
            instance.add_instigator_state(
                InstigatorState(
                    external_sensor.get_external_origin(),
                    InstigatorType.SENSOR,
                    InstigatorStatus.RUNNING,
                )
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_ticks(
                external_sensor.get_external_origin_id(), external_sensor.selector_id
            )
            assert len(ticks) == 0

            evaluate_sensors(exploding_workspace_context, executor)

            assert instance.get_runs_count() == 1
            run = instance.get_runs()[0]
            ticks = instance.get_ticks(
                external_sensor.get_external_origin_id(), external_sensor.selector_id
            )
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
                [run.run_id],
            )

            assert (
                "Run {run_id} created successfully but failed to launch:".format(run_id=run.run_id)
                in caplog.text
            )

            assert "The entire purpose of this is to throw on launch" in caplog.text


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_launch_once(caplog, executor, instance, workspace_context, external_repo):
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
        external_sensor = external_repo.get_external_sensor("run_key_sensor")
        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 0

        evaluate_sensors(workspace_context, executor)
        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 1
        run = instance.get_runs()[0]
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            external_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
            expected_run_ids=[run.run_id],
        )

    # run again (after 30 seconds), to ensure that the run key maintains idempotence
    freeze_datetime = freeze_datetime.add(seconds=30)
    with pendulum.test(freeze_datetime):
        evaluate_sensors(workspace_context, executor)
        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            external_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )
        assert ticks[0].run_keys
        assert len(ticks[0].run_keys) == 1
        assert not ticks[0].run_ids

        assert (
            "Skipping 1 run for sensor run_key_sensor already completed with run keys:"
            ' ["only_once"]'
            in caplog.text
        )

        launched_run = instance.get_runs()[0]

        # Manually create a new run with the same tags
        execute_pipeline(
            the_pipeline,
            run_config=launched_run.run_config,
            tags=launched_run.tags,
            instance=instance,
        )

        # Sensor loop still executes
    freeze_datetime = freeze_datetime.add(seconds=30)
    with pendulum.test(freeze_datetime):
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )

        assert len(ticks) == 3
        validate_tick(
            ticks[0],
            external_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )


@contextmanager
def instance_with_sensors_no_run_bucketing():
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(
            overrides={
                "run_storage": {
                    "module": "dagster_tests.storage_tests.test_run_storage",
                    "class": "NonBucketQuerySqliteRunStorage",
                    "config": {"base_dir": temp_dir},
                },
                "run_launcher": {
                    "module": "dagster._core.test_utils",
                    "class": "MockedRunLauncher",
                },
            }
        ) as instance:
            yield instance


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_launch_once_unbatched(caplog, executor, workspace_context, external_repo):
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
    with instance_with_sensors_no_run_bucketing() as instance:
        no_bucket_workspace_context = workspace_context.copy_for_test_instance(instance)

        with pendulum.test(freeze_datetime):
            external_sensor = external_repo.get_external_sensor("run_key_sensor")
            instance.add_instigator_state(
                InstigatorState(
                    external_sensor.get_external_origin(),
                    InstigatorType.SENSOR,
                    InstigatorStatus.RUNNING,
                )
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_ticks(
                external_sensor.get_external_origin_id(), external_sensor.selector_id
            )
            assert len(ticks) == 0

            evaluate_sensors(no_bucket_workspace_context, executor)
            wait_for_all_runs_to_start(instance)

            assert instance.get_runs_count() == 1
            run = instance.get_runs()[0]
            ticks = instance.get_ticks(
                external_sensor.get_external_origin_id(), external_sensor.selector_id
            )
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
                expected_run_ids=[run.run_id],
            )

        # run again (after 30 seconds), to ensure that the run key maintains idempotence
        freeze_datetime = freeze_datetime.add(seconds=30)
        with pendulum.test(freeze_datetime):
            evaluate_sensors(no_bucket_workspace_context, executor)
            assert instance.get_runs_count() == 1
            ticks = instance.get_ticks(
                external_sensor.get_external_origin_id(), external_sensor.selector_id
            )
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                external_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )
            assert (
                "Skipping 1 run for sensor run_key_sensor already completed with run keys:"
                ' ["only_once"]'
                in caplog.text
            )

            launched_run = instance.get_runs()[0]

            # Manually create a new run with the same tags
            execute_pipeline(
                the_pipeline,
                run_config=launched_run.run_config,
                tags=launched_run.tags,
                instance=instance,
            )

            # Sensor loop still executes
        freeze_datetime = freeze_datetime.add(seconds=30)
        with pendulum.test(freeze_datetime):
            evaluate_sensors(no_bucket_workspace_context, executor)
            ticks = instance.get_ticks(
                external_sensor.get_external_origin_id(), external_sensor.selector_id
            )

            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                external_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_custom_interval_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=28, tz="UTC"), "US/Central"
    )
    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("custom_interval_sensor")
        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 0

        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(ticks[0], external_sensor, freeze_datetime, TickStatus.SKIPPED)

        freeze_datetime = freeze_datetime.add(seconds=30)

    with pendulum.test(freeze_datetime):
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        # no additional tick created after 30 seconds
        assert len(ticks) == 1

        freeze_datetime = freeze_datetime.add(seconds=30)

    with pendulum.test(freeze_datetime):
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 2

        expected_datetime = create_pendulum_time(year=2019, month=2, day=28, hour=0, minute=1)
        validate_tick(ticks[0], external_sensor, expected_datetime, TickStatus.SKIPPED)


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_custom_interval_sensor_with_offset(
    monkeypatch, executor, instance, workspace_context, external_repo
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=28, tz="UTC"), "US/Central"
    )

    sleeps = []

    def fake_sleep(s):
        sleeps.append(s)
        pendulum.set_test_now(pendulum.now().add(seconds=s))

    monkeypatch.setattr(time, "sleep", fake_sleep)

    shutdown_event = mock.MagicMock()
    shutdown_event.wait.side_effect = fake_sleep

    with pendulum.test(freeze_datetime):
        # 60 second custom interval
        external_sensor = external_repo.get_external_sensor("custom_interval_sensor")

        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )

        # create a tick
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 1

        # calling for another iteration should not generate another tick because time has not
        # advanced
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 1

        # call the sensor_iteration_loop, which should loop, and call the monkeypatched sleep
        # to advance 30 seconds
        list(
            execute_sensor_iteration_loop(
                workspace_context,
                get_default_daemon_logger("dagster.daemon.SensorDaemon"),
                shutdown_event=shutdown_event,
                until=freeze_datetime.add(seconds=65).timestamp(),
            )
        )

        assert pendulum.now() == freeze_datetime.add(seconds=65)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 2
        assert sum(sleeps) == 65


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_sensor_start_stop(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("always_on_sensor")
        external_origin_id = external_sensor.get_external_origin_id()
        instance.start_sensor(external_sensor)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(external_origin_id, external_sensor.selector_id)
        assert len(ticks) == 0

        evaluate_sensors(workspace_context, executor)

        assert instance.get_runs_count() == 1
        run = instance.get_runs()[0]
        ticks = instance.get_ticks(external_origin_id, external_sensor.selector_id)
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            external_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
            [run.run_id],
        )

        freeze_datetime = freeze_datetime.add(seconds=15)

    with pendulum.test(freeze_datetime):
        evaluate_sensors(workspace_context, executor)
        # no new ticks, no new runs, we are below the 30 second min interval
        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(external_origin_id, external_sensor.selector_id)
        assert len(ticks) == 1

        # stop / start
        instance.stop_sensor(external_origin_id, external_sensor.selector_id, external_sensor)
        instance.start_sensor(external_sensor)

        evaluate_sensors(workspace_context, executor)
        # no new ticks, no new runs, we are below the 30 second min interval
        assert instance.get_runs_count() == 1
        ticks = instance.get_ticks(external_origin_id, external_sensor.selector_id)
        assert len(ticks) == 1

        freeze_datetime = freeze_datetime.add(seconds=16)

    with pendulum.test(freeze_datetime):
        evaluate_sensors(workspace_context, executor)
        # should have new tick, new run, we are after the 30 second min interval
        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(external_origin_id, external_sensor.selector_id)
        assert len(ticks) == 2


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_large_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("large_sensor")
        instance.start_sensor(external_sensor)
        evaluate_sensors(workspace_context, executor, timeout=300)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            external_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_cursor_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        skip_sensor = external_repo.get_external_sensor("skip_cursor_sensor")
        run_sensor = external_repo.get_external_sensor("run_cursor_sensor")
        instance.start_sensor(skip_sensor)
        instance.start_sensor(run_sensor)
        evaluate_sensors(workspace_context, executor)

        skip_ticks = instance.get_ticks(
            skip_sensor.get_external_origin_id(), skip_sensor.selector_id
        )
        assert len(skip_ticks) == 1
        validate_tick(
            skip_ticks[0],
            skip_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )
        assert skip_ticks[0].cursor == "1"

        run_ticks = instance.get_ticks(run_sensor.get_external_origin_id(), run_sensor.selector_id)
        assert len(run_ticks) == 1
        validate_tick(
            run_ticks[0],
            run_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )
        assert run_ticks[0].cursor == "1"

    freeze_datetime = freeze_datetime.add(seconds=60)
    with pendulum.test(freeze_datetime):
        evaluate_sensors(workspace_context, executor)

        skip_ticks = instance.get_ticks(
            skip_sensor.get_external_origin_id(), skip_sensor.selector_id
        )
        assert len(skip_ticks) == 2
        validate_tick(
            skip_ticks[0],
            skip_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )
        assert skip_ticks[0].cursor == "2"

        run_ticks = instance.get_ticks(run_sensor.get_external_origin_id(), run_sensor.selector_id)
        assert len(run_ticks) == 2
        validate_tick(
            run_ticks[0],
            run_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )
        assert run_ticks[0].cursor == "2"


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_run_request_asset_selection_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("run_request_asset_selection_sensor")
        external_origin_id = external_sensor.get_external_origin_id()
        instance.start_sensor(external_sensor)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(external_origin_id, external_sensor.selector_id)
        assert len(ticks) == 0

        evaluate_sensors(workspace_context, executor)

        assert instance.get_runs_count() == 1
        run = instance.get_runs()[0]
        assert run.asset_selection == {AssetKey("a"), AssetKey("b")}
        ticks = instance.get_ticks(external_origin_id, external_sensor.selector_id)
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            external_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
            [run.run_id],
        )
        planned_asset_keys = {
            record.event_log_entry.dagster_event.event_specific_data.asset_key
            for record in instance.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION_PLANNED)
            )
        }
        assert planned_asset_keys == {AssetKey("a"), AssetKey("b")}


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_run_request_stale_asset_selection_sensor_never_materialized(
    executor, instance, workspace_context, external_repo
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )

    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("run_request_stale_asset_sensor")
        instance.start_sensor(external_sensor)
        evaluate_sensors(workspace_context, executor)
        sensor_run = next((r for r in instance.get_runs() if r.pipeline_name == "abc"), None)
        assert sensor_run is not None
        assert sensor_run.asset_selection == {AssetKey("a"), AssetKey("b"), AssetKey("c")}


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_run_request_stale_asset_selection_sensor_empty(
    executor, instance, workspace_context, external_repo
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )

    materialize([a, b, c], instance=instance)

    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("run_request_stale_asset_sensor")
        instance.start_sensor(external_sensor)
        evaluate_sensors(workspace_context, executor)
        sensor_run = next((r for r in instance.get_runs() if r.pipeline_name == "abc"), None)
        assert sensor_run is None


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_run_request_stale_asset_selection_sensor_subset(
    executor, instance, workspace_context, external_repo
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )

    materialize([a], instance=instance)

    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("run_request_stale_asset_sensor")
        instance.start_sensor(external_sensor)
        evaluate_sensors(workspace_context, executor)
        sensor_run = next((r for r in instance.get_runs() if r.pipeline_name == "abc"), None)
        assert sensor_run is not None
        assert sensor_run.asset_selection == {AssetKey("b"), AssetKey("c")}


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_targets_asset_selection_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("targets_asset_selection_sensor")
        external_origin_id = external_sensor.get_external_origin_id()
        instance.start_sensor(external_sensor)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(external_origin_id, external_sensor.selector_id)
        assert len(ticks) == 0

        evaluate_sensors(workspace_context, executor)

        assert instance.get_runs_count() == 2
        runs = instance.get_runs()
        assert (
            len(
                [
                    run
                    for run in runs
                    if run.asset_selection == {AssetKey("asset_a"), AssetKey("asset_b")}
                ]
            )
            == 1
        )
        assert len([run for run in runs if run.asset_selection == {AssetKey("asset_b")}]) == 1
        ticks = instance.get_ticks(external_origin_id, external_sensor.selector_id)
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            external_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
            [run.run_id for run in runs],
        )
        planned_asset_keys = [
            record.event_log_entry.dagster_event.event_specific_data.asset_key
            for record in instance.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION_PLANNED)
            )
        ]
        assert len(planned_asset_keys) == 3
        assert set(planned_asset_keys) == {AssetKey("asset_a"), AssetKey("asset_b")}


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_partitioned_asset_selection_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("partitioned_asset_selection_sensor")
        external_origin_id = external_sensor.get_external_origin_id()
        instance.start_sensor(external_sensor)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(external_origin_id, external_sensor.selector_id)
        assert len(ticks) == 0

        evaluate_sensors(workspace_context, executor)

        assert instance.get_runs_count() == 1
        run = instance.get_runs()[0]
        assert run.asset_selection == {AssetKey("hourly_asset_3")}
        assert run.tags["dagster/partition"] == "2022-08-01-00:00"
        ticks = instance.get_ticks(external_origin_id, external_sensor.selector_id)
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            external_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
            [run.run_id],
        )

        planned_asset_keys = {
            record.event_log_entry.dagster_event.event_specific_data.asset_key
            for record in instance.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION_PLANNED)
            )
        }
        assert planned_asset_keys == {AssetKey("hourly_asset_3")}


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_asset_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        foo_sensor = external_repo.get_external_sensor("asset_foo_sensor")
        instance.start_sensor(foo_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(foo_sensor.get_external_origin_id(), foo_sensor.selector_id)
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            foo_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime.add(seconds=60)
    with pendulum.test(freeze_datetime):
        # should generate the foo asset
        execute_pipeline(foo_pipeline, instance=instance)

        # should fire the asset sensor
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(foo_sensor.get_external_origin_id(), foo_sensor.selector_id)
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            foo_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )
        run = instance.get_runs()[0]
        assert run.run_config == {}
        assert run.tags
        assert run.tags.get("dagster/sensor_name") == "asset_foo_sensor"


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_asset_job_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        job_sensor = external_repo.get_external_sensor("asset_job_sensor")
        instance.start_sensor(job_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(job_sensor.get_external_origin_id(), job_sensor.selector_id)
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            job_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )
        assert "No new materialization events" in ticks[0].tick_data.skip_reason

        freeze_datetime = freeze_datetime.add(seconds=60)
    with pendulum.test(freeze_datetime):
        # should generate the foo asset
        execute_pipeline(foo_pipeline, instance=instance)

        # should fire the asset sensor
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(job_sensor.get_external_origin_id(), job_sensor.selector_id)
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            job_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )
        run = instance.get_runs()[0]
        assert run.run_config == {}
        assert run.tags
        assert run.tags.get("dagster/sensor_name") == "asset_job_sensor"


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_asset_sensor_not_triggered_on_observation(
    executor, instance, workspace_context, external_repo
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        foo_sensor = external_repo.get_external_sensor("asset_foo_sensor")
        instance.start_sensor(foo_sensor)

        # generates the foo asset observation
        execute_pipeline(foo_observation_pipeline, instance=instance)

        # observation should not fire the asset sensor
        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(foo_sensor.get_external_origin_id(), foo_sensor.selector_id)
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            foo_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime.add(seconds=60)
    with pendulum.test(freeze_datetime):
        # should generate the foo asset
        execute_pipeline(foo_pipeline, instance=instance)

        # materialization should fire the asset sensor
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(foo_sensor.get_external_origin_id(), foo_sensor.selector_id)
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            foo_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )
        run = instance.get_runs()[0]
        assert run.run_config == {}
        assert run.tags
        assert run.tags.get("dagster/sensor_name") == "asset_foo_sensor"


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_multi_asset_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        a_and_b_sensor = external_repo.get_external_sensor("asset_a_and_b_sensor")
        instance.start_sensor(a_and_b_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            a_and_b_sensor.get_external_origin_id(), a_and_b_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            a_and_b_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime.add(seconds=60)
    with pendulum.test(freeze_datetime):
        # should generate asset_a
        materialize([asset_a], instance=instance)

        evaluate_sensors(workspace_context, executor)

        # sensor should not fire
        ticks = instance.get_ticks(
            a_and_b_sensor.get_external_origin_id(), a_and_b_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            a_and_b_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime.add(seconds=60)

    with pendulum.test(freeze_datetime):
        # should generate asset_b
        materialize([asset_b], instance=instance)

        # should fire the asset sensor
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            a_and_b_sensor.get_external_origin_id(), a_and_b_sensor.selector_id
        )
        assert len(ticks) == 3
        validate_tick(
            ticks[0],
            a_and_b_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )
        run = instance.get_runs()[0]
        assert run.run_config == {}
        assert run.tags
        assert run.tags.get("dagster/sensor_name") == "asset_a_and_b_sensor"


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_asset_selection_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        asset_selection_sensor = external_repo.get_external_sensor("asset_selection_sensor")
        instance.start_sensor(asset_selection_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            asset_selection_sensor.get_external_origin_id(), asset_selection_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            asset_selection_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_multi_asset_sensor_targets_asset_selection(
    executor, instance, workspace_context, external_repo
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        multi_asset_sensor_targets_asset_selection = external_repo.get_external_sensor(
            "multi_asset_sensor_targets_asset_selection"
        )
        instance.start_sensor(multi_asset_sensor_targets_asset_selection)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            multi_asset_sensor_targets_asset_selection.get_external_origin_id(),
            multi_asset_sensor_targets_asset_selection.selector_id,
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            multi_asset_sensor_targets_asset_selection,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime.add(seconds=60)
    with pendulum.test(freeze_datetime):
        # should generate asset_a
        materialize([asset_a], instance=instance)

        evaluate_sensors(workspace_context, executor)

        # sensor should not fire
        ticks = instance.get_ticks(
            multi_asset_sensor_targets_asset_selection.get_external_origin_id(),
            multi_asset_sensor_targets_asset_selection.selector_id,
        )
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            multi_asset_sensor_targets_asset_selection,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime.add(seconds=60)

    with pendulum.test(freeze_datetime):
        # should generate asset_b
        materialize([asset_b], instance=instance)

        # should fire the asset sensor
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            multi_asset_sensor_targets_asset_selection.get_external_origin_id(),
            multi_asset_sensor_targets_asset_selection.selector_id,
        )
        assert len(ticks) == 3
        validate_tick(
            ticks[0],
            multi_asset_sensor_targets_asset_selection,
            freeze_datetime,
            TickStatus.SUCCESS,
        )
        run = instance.get_runs()[0]
        assert run.run_config == {}
        assert run.tags
        assert run.tags.get("dagster/sensor_name") == "multi_asset_sensor_targets_asset_selection"
        assert run.asset_selection == {AssetKey(["asset_c"])}


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_multi_asset_sensor_w_many_events(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        backlog_sensor = external_repo.get_external_sensor("backlog_sensor")
        instance.start_sensor(backlog_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            backlog_sensor.get_external_origin_id(), backlog_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            backlog_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime.add(seconds=60)
    with pendulum.test(freeze_datetime):
        # should generate asset_a
        materialize([asset_a], instance=instance)

        # sensor should not fire
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            backlog_sensor.get_external_origin_id(), backlog_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            backlog_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime.add(seconds=60)

    with pendulum.test(freeze_datetime):
        # should generate asset_a
        materialize([asset_a], instance=instance)

        # should fire the asset sensor
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            backlog_sensor.get_external_origin_id(), backlog_sensor.selector_id
        )
        assert len(ticks) == 3
        validate_tick(
            ticks[0],
            backlog_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )
        run = instance.get_runs()[0]
        assert run.run_config == {}
        assert run.tags
        assert run.tags.get("dagster/sensor_name") == "backlog_sensor"


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_multi_asset_sensor_w_no_cursor_update(
    executor, instance, workspace_context, external_repo
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        cursor_sensor = external_repo.get_external_sensor("doesnt_update_cursor_sensor")
        instance.start_sensor(cursor_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            cursor_sensor.get_external_origin_id(), cursor_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            cursor_sensor,
            freeze_datetime,
            TickStatus.SKIPPED,
        )

        freeze_datetime = freeze_datetime.add(seconds=60)
    with pendulum.test(freeze_datetime):
        # should generate asset_a
        materialize([asset_a], instance=instance)

        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            cursor_sensor.get_external_origin_id(), cursor_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            cursor_sensor,
            freeze_datetime,
            TickStatus.FAILURE,
        )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_multi_asset_sensor_hourly_to_weekly(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2022, month=8, day=2, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        materialize([hourly_asset], instance=instance, partition_key="2022-08-01-00:00")
        cursor_sensor = external_repo.get_external_sensor("multi_asset_sensor_hourly_to_weekly")
        instance.start_sensor(cursor_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            cursor_sensor.get_external_origin_id(), cursor_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            cursor_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )
        run = instance.get_runs()[0]
        assert run.run_config == {}
        assert run.tags
        assert run.tags.get("dagster/sensor_name") == "multi_asset_sensor_hourly_to_weekly"
        assert run.tags.get("dagster/partition") == "2022-07-31"


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_multi_asset_sensor_hourly_to_hourly(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2022, month=8, day=3, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        materialize([hourly_asset], instance=instance, partition_key="2022-08-02-00:00")
        cursor_sensor = external_repo.get_external_sensor("multi_asset_sensor_hourly_to_hourly")
        instance.start_sensor(cursor_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            cursor_sensor.get_external_origin_id(), cursor_sensor.selector_id
        )
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            cursor_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )
        run = instance.get_runs()[0]

        assert run.run_config == {}
        assert run.tags
        assert run.tags.get("dagster/sensor_name") == "multi_asset_sensor_hourly_to_hourly"
        assert run.tags.get("dagster/partition") == "2022-08-02-00:00"

        freeze_datetime = freeze_datetime.add(seconds=30)

    with pendulum.test(freeze_datetime):
        cursor_sensor = external_repo.get_external_sensor("multi_asset_sensor_hourly_to_hourly")
        instance.start_sensor(cursor_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            cursor_sensor.get_external_origin_id(), cursor_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(ticks[0], cursor_sensor, freeze_datetime, TickStatus.SKIPPED)


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_multi_job_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        job_sensor = external_repo.get_external_sensor("two_job_sensor")
        instance.start_sensor(job_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(job_sensor.get_external_origin_id(), job_sensor.selector_id)
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            job_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )

        run = instance.get_runs()[0]
        assert run.run_config == {}
        assert run.tags.get("dagster/sensor_name") == "two_job_sensor"
        assert run.pipeline_name == "the_graph"

        freeze_datetime = freeze_datetime.add(seconds=60)
    with pendulum.test(freeze_datetime):
        # should fire the asset sensor
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(job_sensor.get_external_origin_id(), job_sensor.selector_id)
        assert len(ticks) == 2
        validate_tick(
            ticks[0],
            job_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
        )
        run = instance.get_runs()[0]
        assert run.run_config == {"solids": {"config_solid": {"config": {"foo": "blah"}}}}
        assert run.tags
        assert run.tags.get("dagster/sensor_name") == "two_job_sensor"
        assert run.pipeline_name == "config_graph"


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_bad_run_request_untargeted(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        job_sensor = external_repo.get_external_sensor("bad_request_untargeted")
        instance.start_sensor(job_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(job_sensor.get_external_origin_id(), job_sensor.selector_id)
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            job_sensor,
            freeze_datetime,
            TickStatus.FAILURE,
            None,
            (
                "Error in sensor bad_request_untargeted: Sensor evaluation function returned a "
                "RunRequest for a sensor lacking a specified target (job_name, job, or "
                "jobs)."
            ),
        )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_bad_run_request_mismatch(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        job_sensor = external_repo.get_external_sensor("bad_request_mismatch")
        instance.start_sensor(job_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(job_sensor.get_external_origin_id(), job_sensor.selector_id)
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            job_sensor,
            freeze_datetime,
            TickStatus.FAILURE,
            None,
            (
                "Error in sensor bad_request_mismatch: Sensor returned a RunRequest with "
                "job_name config_pipeline. Expected one of: ['the_graph']"
            ),
        )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_bad_run_request_unspecified(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        job_sensor = external_repo.get_external_sensor("bad_request_unspecified")
        instance.start_sensor(job_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(job_sensor.get_external_origin_id(), job_sensor.selector_id)
        assert len(ticks) == 1
        validate_tick(
            ticks[0],
            job_sensor,
            freeze_datetime,
            TickStatus.FAILURE,
            None,
            (
                "Error in sensor bad_request_unspecified: Sensor returned a RunRequest that "
                "did not specify job_name for the requested run. Expected one of: "
                "['the_graph', 'config_graph']"
            ),
        )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_status_in_code_sensor(executor, instance):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with create_test_daemon_workspace_context(
        create_workspace_load_target(attribute="the_status_in_code_repo"),
        instance=instance,
    ) as workspace_context:
        external_repo = next(
            iter(workspace_context.create_request_context().get_workspace_snapshot().values())
        ).repository_location.get_repository("the_status_in_code_repo")

        with pendulum.test(freeze_datetime):
            running_sensor = external_repo.get_external_sensor("always_running_sensor")
            not_running_sensor = external_repo.get_external_sensor("never_running_sensor")

            always_running_origin = running_sensor.get_external_origin()
            never_running_origin = not_running_sensor.get_external_origin()

            assert instance.get_runs_count() == 0
            assert (
                len(instance.get_ticks(always_running_origin.get_id(), running_sensor.selector_id))
                == 0
            )
            assert (
                len(
                    instance.get_ticks(
                        never_running_origin.get_id(),
                        not_running_sensor.selector_id,
                    )
                )
                == 0
            )

            assert len(instance.all_instigator_state()) == 0

            evaluate_sensors(workspace_context, executor)

            assert instance.get_runs_count() == 0

            assert len(instance.all_instigator_state()) == 1
            instigator_state = instance.get_instigator_state(
                always_running_origin.get_id(), running_sensor.selector_id
            )
            assert instigator_state.status == InstigatorStatus.AUTOMATICALLY_RUNNING

            ticks = instance.get_ticks(
                running_sensor.get_external_origin_id(), running_sensor.selector_id
            )
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                running_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            assert (
                len(
                    instance.get_ticks(
                        never_running_origin.get_id(),
                        not_running_sensor.selector_id,
                    )
                )
                == 0
            )

        freeze_datetime = freeze_datetime.add(seconds=30)
        with pendulum.test(freeze_datetime):
            evaluate_sensors(workspace_context, executor)
            wait_for_all_runs_to_start(instance)
            assert instance.get_runs_count() == 1
            run = instance.get_runs()[0]
            validate_run_started(run)
            ticks = instance.get_ticks(
                running_sensor.get_external_origin_id(), running_sensor.selector_id
            )
            assert len(ticks) == 2

            expected_datetime = create_pendulum_time(
                year=2019, month=2, day=28, hour=0, minute=0, second=29
            )
            validate_tick(
                ticks[0],
                running_sensor,
                expected_datetime,
                TickStatus.SUCCESS,
                [run.run_id],
            )

            assert (
                len(
                    instance.get_ticks(
                        never_running_origin.get_id(),
                        not_running_sensor.selector_id,
                    )
                )
                == 0
            )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_run_request_list_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("request_list_sensor")
        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 0

        evaluate_sensors(workspace_context, executor)

        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 1


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_sensor_purge(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with pendulum.test(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("simple_sensor")
        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 0

        # create a tick
        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 1
        freeze_datetime = freeze_datetime.add(days=6)

    with pendulum.test(freeze_datetime):
        # create another tick
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 2

        freeze_datetime = freeze_datetime.add(days=2)

    with pendulum.test(freeze_datetime):
        # create another tick, but the first tick should be purged
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 2


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_sensor_custom_purge(executor, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with instance_for_test(
        overrides={
            "retention": {"sensor": {"purge_after_days": {"skipped": 14}}},
            "run_launcher": {"module": "dagster._core.test_utils", "class": "MockedRunLauncher"},
        },
    ) as instance:
        purge_ws_ctx = workspace_context.copy_for_test_instance(instance)
        with pendulum.test(freeze_datetime):
            external_sensor = external_repo.get_external_sensor("simple_sensor")
            instance.add_instigator_state(
                InstigatorState(
                    external_sensor.get_external_origin(),
                    InstigatorType.SENSOR,
                    InstigatorStatus.RUNNING,
                )
            )
            ticks = instance.get_ticks(
                external_sensor.get_external_origin_id(), external_sensor.selector_id
            )
            assert len(ticks) == 0

            # create a tick
            evaluate_sensors(purge_ws_ctx, executor)

            ticks = instance.get_ticks(
                external_sensor.get_external_origin_id(), external_sensor.selector_id
            )
            assert len(ticks) == 1
            freeze_datetime = freeze_datetime.add(days=8)

        with pendulum.test(freeze_datetime):
            # create another tick, and the first tick should not be purged despite the fact that the
            # default purge day offset is 7
            evaluate_sensors(purge_ws_ctx, executor)
            ticks = instance.get_ticks(
                external_sensor.get_external_origin_id(), external_sensor.selector_id
            )
            assert len(ticks) == 2

            freeze_datetime = freeze_datetime.add(days=7)

        with pendulum.test(freeze_datetime):
            # create another tick, but the first tick should be purged
            evaluate_sensors(purge_ws_ctx, executor)
            ticks = instance.get_ticks(
                external_sensor.get_external_origin_id(), external_sensor.selector_id
            )
            assert len(ticks) == 2


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_repository_namespacing(executor):
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
    with ExitStack() as exit_stack:
        instance = exit_stack.enter_context(instance_for_test())
        full_workspace_context = exit_stack.enter_context(
            create_test_daemon_workspace_context(
                create_workspace_load_target(attribute=None),  # load all repos
                instance=instance,
            )
        )

        full_location = next(
            iter(full_workspace_context.create_request_context().get_workspace_snapshot().values())
        ).repository_location
        external_repo = full_location.get_repository("the_repo")
        other_repo = full_location.get_repository("the_other_repo")

        # stop always on sensor
        status_in_code_repo = full_location.get_repository("the_status_in_code_repo")
        running_sensor = status_in_code_repo.get_external_sensor("always_running_sensor")
        instance.stop_sensor(
            running_sensor.get_external_origin_id(), running_sensor.selector_id, running_sensor
        )

        external_sensor = external_repo.get_external_sensor("run_key_sensor")
        other_sensor = other_repo.get_external_sensor("run_key_sensor")

        with pendulum.test(freeze_datetime):
            instance.start_sensor(external_sensor)
            assert instance.get_runs_count() == 0
            ticks = instance.get_ticks(
                external_sensor.get_external_origin_id(), external_sensor.selector_id
            )
            assert len(ticks) == 0

            instance.start_sensor(other_sensor)
            assert instance.get_runs_count() == 0
            ticks = instance.get_ticks(
                other_sensor.get_external_origin_id(), other_sensor.selector_id
            )
            assert len(ticks) == 0

            evaluate_sensors(full_workspace_context, executor)

            wait_for_all_runs_to_start(instance)

            assert instance.get_runs_count() == 2  # both copies of the sensor

            ticks = instance.get_ticks(
                external_sensor.get_external_origin_id(), external_sensor.selector_id
            )
            assert len(ticks) == 1
            assert ticks[0].status == TickStatus.SUCCESS

            ticks = instance.get_ticks(
                other_sensor.get_external_origin_id(), other_sensor.selector_id
            )
            assert len(ticks) == 1

        # run again (after 30 seconds), to ensure that the run key maintains idempotence
        freeze_datetime = freeze_datetime.add(seconds=30)
        with pendulum.test(freeze_datetime):
            evaluate_sensors(full_workspace_context, executor)
            assert instance.get_runs_count() == 2  # still 2
            ticks = instance.get_ticks(
                external_sensor.get_external_origin_id(), external_sensor.selector_id
            )
            assert len(ticks) == 2


def test_settings():
    settings = {"use_threads": True, "num_workers": 4}
    with instance_for_test(overrides={"sensors": settings}) as thread_inst:
        assert thread_inst.get_settings("sensors") == settings


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_sensor_logging(executor, instance, workspace_context, external_repo):
    external_sensor = external_repo.get_external_sensor("logging_sensor")
    instance.add_instigator_state(
        InstigatorState(
            external_sensor.get_external_origin(),
            InstigatorType.SENSOR,
            InstigatorStatus.RUNNING,
        )
    )
    assert instance.get_runs_count() == 0
    ticks = instance.get_ticks(
        external_sensor.get_external_origin_id(), external_sensor.selector_id
    )
    assert len(ticks) == 0

    evaluate_sensors(workspace_context, executor)

    ticks = instance.get_ticks(
        external_sensor.get_external_origin_id(), external_sensor.selector_id
    )
    assert len(ticks) == 1
    tick = ticks[0]
    assert tick.log_key
    records = get_instigation_log_records(instance, tick.log_key)
    assert len(records) == 1
    record = records[0]
    assert record[DAGSTER_META_KEY]["orig_message"] == "hello hello"
    instance.compute_log_manager.delete_logs(log_key=tick.log_key)


def test_code_location_construction():
    # this just gets code coverage in in the run status sensor definition constructor
    @run_status_sensor(
        monitored_jobs=[
            CodeLocationSelector(
                location_name="test_location",
            )
        ],
        run_status=DagsterRunStatus.SUCCESS,
    )
    def cross_code_location_sensor(context):
        raise Exception("never executed")

    assert cross_code_location_sensor
