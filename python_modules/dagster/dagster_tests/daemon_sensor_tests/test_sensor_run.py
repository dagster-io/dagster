import logging
import random
import string
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from typing import Any
from unittest import mock

import pendulum
import pytest
from dagster import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    AssetSelection,
    AutoMaterializePolicy,
    CodeLocationSelector,
    DagsterInstance,
    DagsterRunStatus,
    DailyPartitionsDefinition,
    DynamicPartitionsDefinition,
    Field,
    HourlyPartitionsDefinition,
    JobSelector,
    MultiPartitionKey,
    MultiPartitionsDefinition,
    Output,
    RepositorySelector,
    SourceAsset,
    StaticPartitionsDefinition,
    WeeklyPartitionsDefinition,
    asset,
    asset_check,
    define_asset_job,
    load_asset_checks_from_current_module,
    load_assets_from_current_module,
    materialize,
    multi_asset_sensor,
    repository,
    run_failure_sensor,
)
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.auto_materialize_sensor_definition import (
    AutoMaterializeSensorDefinition,
)
from dagster._core.definitions.decorators import op
from dagster._core.definitions.decorators.job_decorator import job
from dagster._core.definitions.decorators.sensor_decorator import asset_sensor, sensor
from dagster._core.definitions.instigation_logger import get_instigation_log_records
from dagster._core.definitions.run_request import InstigatorType, SensorResult
from dagster._core.definitions.run_status_sensor_definition import run_status_sensor
from dagster._core.definitions.sensor_definition import (
    DefaultSensorStatus,
    RunRequest,
    SensorEvaluationContext,
    SensorType,
    SkipReason,
)
from dagster._core.events import DagsterEventType
from dagster._core.log_manager import LOG_RECORD_METADATA_ATTR
from dagster._core.remote_representation import (
    ExternalInstigatorOrigin,
    ExternalRepositoryOrigin,
    ExternalSensor,
)
from dagster._core.remote_representation.external import ExternalRepository
from dagster._core.remote_representation.origin import (
    ManagedGrpcPythonEnvCodeLocationOrigin,
)
from dagster._core.scheduler.instigation import (
    DynamicPartitionsRequestResult,
    InstigatorState,
    InstigatorStatus,
    SensorInstigatorData,
    TickStatus,
)
from dagster._core.storage.captured_log_manager import CapturedLogManager
from dagster._core.storage.event_log.base import EventRecordsFilter
from dagster._core.test_utils import (
    BlockingThreadPoolExecutor,
    create_test_daemon_workspace_context,
    instance_for_test,
    wait_for_futures,
)
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._daemon import get_default_daemon_logger
from dagster._daemon.daemon import SpanMarker
from dagster._daemon.sensor import execute_sensor_iteration, execute_sensor_iteration_loop
from dagster._seven.compat.pendulum import (
    _IS_PENDULUM_3,
    create_pendulum_time,
    pendulum_freeze_time,
    to_timezone,
)

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


@asset_check(asset="a")
def check_a():
    return AssetCheckResult(passed=True)


asset_job = define_asset_job("abc", selection=AssetSelection.keys("c", "b").upstream())

asset_and_check_job = define_asset_job(
    "asset_and_check_job",
    selection=AssetSelection.assets(a),
)


@op
def the_op(_):
    return 1


@job
def the_job():
    the_op()


@job
def the_other_job():
    the_op()


@op(config_schema=Field(Any))
def config_op(_):
    return 1


@job
def config_job():
    config_op()


@op
def foo_op():
    yield AssetMaterialization(asset_key=AssetKey("foo"))
    yield Output(1)


@job
def foo_job():
    foo_op()


@op
def foo_observation_op():
    yield AssetObservation(asset_key=AssetKey("foo"), metadata={"text": "FOO"})
    yield Output(5)


@job
def foo_observation_job():
    foo_observation_op()


@op
def hanging_op():
    start_time = time.time()
    while True:
        if time.time() - start_time > 10:
            return
        time.sleep(0.5)


@job
def hanging_job():
    hanging_op()


@op
def failure_op():
    raise Exception("womp womp")


@job
def failure_job():
    failure_op()


@job
def failure_job_2():
    failure_op()


@sensor(job_name="the_job")
def simple_sensor(context):
    if not context.last_tick_completion_time or not int(context.last_tick_completion_time) % 2:
        return SkipReason()

    return RunRequest(run_key=None, run_config={}, tags={})


@sensor(job_name="the_job")
def always_on_sensor(_context):
    return RunRequest(run_key=None, run_config={}, tags={})


@sensor(job_name="the_job")
def run_key_sensor(_context):
    return RunRequest(run_key="only_once", run_config={}, tags={})


@sensor(job_name="the_job")
def error_sensor(context):
    context.update_cursor("the exception below should keep this from being persisted")
    raise Exception("womp womp")


@sensor(job_name="the_job")
def wrong_config_sensor(_context):
    return RunRequest(run_key="bad_config_key", run_config={"bad_key": "bad_val"}, tags={})


@sensor(job_name="the_job", minimum_interval_seconds=60)
def custom_interval_sensor(_context):
    return SkipReason()


@sensor(job_name="the_job")
def skip_cursor_sensor(context):
    if not context.cursor:
        cursor = 1
    else:
        cursor = int(context.cursor) + 1

    context.update_cursor(str(cursor))
    return SkipReason()


@sensor(job_name="the_job")
def run_cursor_sensor(context):
    if not context.cursor:
        cursor = 1
    else:
        cursor = int(context.cursor) + 1

    context.update_cursor(str(cursor))
    return RunRequest(run_key=None, run_config={}, tags={})


@sensor(job_name="the_job")
def start_skip_sensor(context: SensorEvaluationContext):
    context.update_cursor(
        str(context.last_sensor_start_time) if context.last_sensor_start_time else None
    )
    # skips the first tick after a start
    if context.is_first_tick_since_sensor_start:
        return SkipReason()
    return RunRequest()


@asset
def asset_a():
    return 1


@asset
def asset_b():
    return 2


@asset
def asset_c(asset_b):
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


@multi_asset_sensor(monitored_assets=[AssetKey("asset_a"), AssetKey("asset_b")], job=the_job)
def sensor_result_multi_asset_sensor(context):
    context.advance_all_cursors()
    return SensorResult([RunRequest("foo")])


@multi_asset_sensor(monitored_assets=[AssetKey("asset_a"), AssetKey("asset_b")], job=the_job)
def cursor_sensor_result_multi_asset_sensor(context):
    return SensorResult([RunRequest("foo")], cursor="foo")


def _random_string(length):
    return "".join(random.choice(string.ascii_lowercase) for x in range(length))


@sensor(job_name="config_job")
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
        config = {"ops": {"config_op": {"config": {"foo": config_garbage}}}}
        yield RunRequest(run_key=None, run_config=config, tags=tags_garbage)


@sensor(job_name="config_job")
def many_request_sensor(_context):
    # create a gRPC response payload larger than the limit (4194304)
    REQUEST_COUNT = 15

    for _ in range(REQUEST_COUNT):
        config = {"ops": {"config_op": {"config": {"foo": "bar"}}}}
        yield RunRequest(run_key=None, run_config=config)


@sensor(job=asset_job)
def run_request_asset_selection_sensor(_context):
    yield RunRequest(run_key=None, asset_selection=[AssetKey("a"), AssetKey("b")])


@sensor(job=asset_and_check_job)
def run_request_check_only_sensor(_context):
    yield RunRequest(asset_check_keys=[AssetCheckKey(AssetKey("a"), "check_a")])


@sensor(job=asset_job)
def run_request_stale_asset_sensor(_context):
    yield RunRequest(run_key=None, stale_assets_only=True)


@sensor(job=hourly_asset_job)
def partitioned_asset_selection_sensor(_context):
    return hourly_asset_job.run_request_for_partition(
        partition_key="2022-08-01-00:00", run_key=None, asset_selection=[AssetKey("hourly_asset_3")]
    )


@asset_sensor(job_name="the_job", asset_key=AssetKey("foo"))
def asset_foo_sensor(context, _event):
    return RunRequest(run_key=context.cursor, run_config={})


@asset_sensor(asset_key=AssetKey("foo"), job=the_job)
def asset_job_sensor(context, _event):
    return RunRequest(run_key=context.cursor, run_config={})


@run_failure_sensor
def my_run_failure_sensor(context):
    assert isinstance(context.instance, DagsterInstance)
    if "failure_op" in context.failure_event.message:
        step_failure_events = context.get_step_failure_events()
        assert len(step_failure_events) == 1
        step_error_str = step_failure_events[0].event_specific_data.error.to_string()
        assert "womp womp" in step_error_str, step_error_str


@run_failure_sensor(job_selection=[failure_job])
def my_run_failure_sensor_filtered(context):
    assert isinstance(context.instance, DagsterInstance)


@run_failure_sensor()
def my_run_failure_sensor_that_itself_fails(context):
    raise Exception("How meta")


@run_status_sensor(run_status=DagsterRunStatus.SUCCESS)
def my_job_success_sensor(context):
    assert isinstance(context.instance, DagsterInstance)


@run_status_sensor(run_status=DagsterRunStatus.STARTED)
def my_job_started_sensor(context):
    assert isinstance(context.instance, DagsterInstance)


@sensor(jobs=[the_job, config_job])
def two_job_sensor(context):
    counter = int(context.cursor) if context.cursor else 0
    if counter % 2 == 0:
        yield RunRequest(run_key=str(counter), job_name=the_job.name)
    else:
        yield RunRequest(
            run_key=str(counter),
            job_name=config_job.name,
            run_config={"ops": {"config_op": {"config": {"foo": "blah"}}}},
        )
    context.update_cursor(str(counter + 1))


@sensor()
def bad_request_untargeted(_ctx):
    yield RunRequest(run_key=None, job_name="should_fail")


@sensor(job=the_job)
def bad_request_mismatch(_ctx):
    yield RunRequest(run_key=None, job_name="config_job")


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
            job_name="the_job",
        )
    ],
    run_status=DagsterRunStatus.SUCCESS,
    request_job=the_other_job,
)
def cross_repo_job_sensor():
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
def instance_sensor():
    pass


@run_status_sensor(
    monitor_all_repositories=True,
    run_status=DagsterRunStatus.SUCCESS,
)
def all_code_locations_run_status_sensor():
    pass


@sensor(job=the_job)
def logging_sensor(context):
    class Handler(logging.Handler):
        def handle(self, record):
            try:
                self.message = record.getMessage()
            except TypeError:
                self.message = "error"

    handler = Handler()
    context.log.addHandler(handler)
    context.log.info("hello %s", "hello")
    context.log.info(handler.message)

    try:
        raise Exception("hi hi")
    except Exception:
        context.log.exception("goodbye goodbye")

    context.log.removeHandler(handler)

    return SkipReason()


@sensor(job=the_job)
def logging_fail_tick_sensor(context: "SensorEvaluationContext"):
    context.log.info("hello hello")

    raise Exception("womp womp")


@run_status_sensor(
    monitor_all_repositories=True,
    run_status=DagsterRunStatus.SUCCESS,
)
def logging_status_sensor(context):
    context.log.info(f"run succeeded: {context.dagster_run.run_id}")


quux = DynamicPartitionsDefinition(name="quux")


@asset(partitions_def=quux)
def quux_asset(context):
    return 1


quux_asset_job = define_asset_job("quux_asset_job", [quux_asset], partitions_def=quux)


@sensor()
def add_dynamic_partitions_sensor(context):
    return SensorResult(
        dynamic_partitions_requests=[
            quux.build_add_request(["baz", "foo"]),
        ],
    )


@sensor(job=quux_asset_job)
def add_delete_dynamic_partitions_and_yield_run_requests_sensor(context):
    return SensorResult(
        dynamic_partitions_requests=[
            quux.build_add_request(["1"]),
            quux.build_delete_request(["2", "3"]),
        ],
        run_requests=[RunRequest(partition_key="1")],
    )


@sensor(job=quux_asset_job)
def error_on_deleted_dynamic_partitions_run_requests_sensor(context):
    return SensorResult(
        dynamic_partitions_requests=[
            quux.build_delete_request(["2"]),
        ],
        run_requests=[RunRequest(partition_key="2")],
    )


dynamic1 = DynamicPartitionsDefinition(name="dynamic1")
dynamic2 = DynamicPartitionsDefinition(name="dynamic2")


@asset(partitions_def=MultiPartitionsDefinition({"dynamic1": dynamic1, "dynamic2": dynamic2}))
def multipartitioned_with_two_dynamic_dims():
    pass


@sensor(asset_selection=AssetSelection.keys(multipartitioned_with_two_dynamic_dims.key))
def success_on_multipartition_run_request_with_two_dynamic_dimensions_sensor(context):
    return SensorResult(
        dynamic_partitions_requests=[
            dynamic1.build_add_request(["1"]),
            dynamic2.build_add_request(["2"]),
        ],
        run_requests=[
            RunRequest(partition_key=MultiPartitionKey({"dynamic1": "1", "dynamic2": "2"}))
        ],
    )


@sensor(asset_selection=AssetSelection.keys(multipartitioned_with_two_dynamic_dims.key))
def error_on_multipartition_run_request_with_two_dynamic_dimensions_sensor(context):
    return SensorResult(
        dynamic_partitions_requests=[
            dynamic1.build_add_request(["1"]),
            dynamic2.build_add_request(["2"]),
        ],
        run_requests=[
            RunRequest(partition_key=MultiPartitionKey({"dynamic1": "2", "dynamic2": "1"}))
        ],
    )


@asset(
    partitions_def=MultiPartitionsDefinition(
        {
            "static": StaticPartitionsDefinition(["a", "b", "c"]),
            "time": DailyPartitionsDefinition("2023-01-01"),
        }
    )
)
def multipartitioned_asset_with_static_time_dimensions():
    pass


@sensor(asset_selection=AssetSelection.keys(multipartitioned_asset_with_static_time_dimensions.key))
def multipartitions_with_static_time_dimensions_run_requests_sensor(context):
    return SensorResult(
        run_requests=[
            RunRequest(partition_key=MultiPartitionKey({"static": "b", "time": "2023-01-05"}))
        ],
    )


daily_partitions_def = DailyPartitionsDefinition(start_date="2022-08-01")


@asset(partitions_def=daily_partitions_def)
def partitioned_asset():
    return 1


daily_partitioned_job = define_asset_job(
    "daily_partitioned_job",
    partitions_def=daily_partitions_def,
).resolve(asset_graph=AssetGraph.from_assets([partitioned_asset]))


@run_status_sensor(run_status=DagsterRunStatus.SUCCESS, monitored_jobs=[daily_partitioned_job])
def partitioned_pipeline_success_sensor(_context):
    assert _context.partition_key == "2022-08-01"


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def auto_materialize_asset():
    pass


auto_materialize_sensor = AutoMaterializeSensorDefinition(
    "my_auto_materialize_sensor",
    asset_selection=[auto_materialize_asset],
)


@repository
def the_repo():
    return [
        the_job,
        the_other_job,
        config_job,
        foo_job,
        asset_and_check_job,
        large_sensor,
        many_request_sensor,
        simple_sensor,
        error_sensor,
        wrong_config_sensor,
        always_on_sensor,
        run_key_sensor,
        custom_interval_sensor,
        skip_cursor_sensor,
        run_cursor_sensor,
        start_skip_sensor,
        asset_foo_sensor,
        asset_job_sensor,
        my_run_failure_sensor,
        my_run_failure_sensor_filtered,
        my_run_failure_sensor_that_itself_fails,
        my_job_success_sensor,
        my_job_started_sensor,
        failure_job,
        failure_job_2,
        hanging_job,
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
        load_asset_checks_from_current_module(),
        run_request_asset_selection_sensor,
        run_request_stale_asset_sensor,
        weekly_asset_job,
        multi_asset_sensor_hourly_to_weekly,
        multi_asset_sensor_hourly_to_hourly,
        sensor_result_multi_asset_sensor,
        cursor_sensor_result_multi_asset_sensor,
        partitioned_asset_selection_sensor,
        asset_selection_sensor,
        targets_asset_selection_sensor,
        multi_asset_sensor_targets_asset_selection,
        logging_sensor,
        logging_fail_tick_sensor,
        logging_status_sensor,
        add_delete_dynamic_partitions_and_yield_run_requests_sensor,
        add_dynamic_partitions_sensor,
        quux_asset_job,
        error_on_deleted_dynamic_partitions_run_requests_sensor,
        partitioned_pipeline_success_sensor,
        daily_partitioned_job,
        success_on_multipartition_run_request_with_two_dynamic_dimensions_sensor,
        error_on_multipartition_run_request_with_two_dynamic_dimensions_sensor,
        multipartitions_with_static_time_dimensions_run_requests_sensor,
        auto_materialize_sensor,
        run_request_check_only_sensor,
    ]


@repository
def the_other_repo():
    return [
        the_job,
        run_key_sensor,
    ]


@sensor(job_name="the_job", default_status=DefaultSensorStatus.RUNNING)
def always_running_sensor(context):
    if not context.last_tick_completion_time or not int(context.last_tick_completion_time) % 2:
        return SkipReason()

    return RunRequest(run_key=None, run_config={}, tags={})


@sensor(job_name="the_job", default_status=DefaultSensorStatus.STOPPED)
def never_running_sensor(context):
    if not context.last_tick_completion_time or not int(context.last_tick_completion_time) % 2:
        return SkipReason()

    return RunRequest(run_key=None, run_config={}, tags={})


@repository
def the_status_in_code_repo():
    return [
        the_job,
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
    ]


FUTURES_TIMEOUT = 75


def evaluate_sensors(workspace_context, executor, submit_executor=None, timeout=FUTURES_TIMEOUT):
    logger = get_default_daemon_logger("SensorDaemon")
    futures = {}
    list(
        execute_sensor_iteration(
            workspace_context,
            logger,
            threadpool_executor=executor,
            sensor_tick_futures=futures,
            submit_threadpool_executor=submit_executor,
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
    assert tick_data.status == expected_status, tick_data.error
    if expected_datetime:
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


def test_ignore_auto_materialize_sensor(instance, workspace_context, external_repo, executor):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )

    with pendulum_freeze_time(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("my_auto_materialize_sensor")
        assert external_sensor
        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
                instigator_data=SensorInstigatorData(
                    sensor_type=SensorType.AUTO_MATERIALIZE,
                ),
            )
        )
        evaluate_sensors(workspace_context, executor)
        # No ticks because of the sensor type
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 0


def test_simple_sensor(instance, workspace_context, external_repo, executor):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )

    with pendulum_freeze_time(freeze_datetime):
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

    with pendulum_freeze_time(freeze_datetime):
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


def test_sensors_keyed_on_selector_not_origin(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
    executor: ThreadPoolExecutor,
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )

    with pendulum_freeze_time(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("simple_sensor")

        existing_origin = external_sensor.get_external_origin()

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


def test_bad_load_sensor_repository(
    executor: ThreadPoolExecutor,
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )

    with pendulum_freeze_time(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("simple_sensor")

        valid_origin = external_sensor.get_external_origin()

        # Swap out a new repository name
        invalid_repo_origin = ExternalInstigatorOrigin(
            ExternalRepositoryOrigin(
                valid_origin.external_repository_origin.code_location_origin,
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


def test_bad_load_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )

    with pendulum_freeze_time(freeze_datetime):
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


def test_error_sensor(caplog, executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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
        assert state.instigator_data.sensor_type == SensorType.STANDARD
        assert state.instigator_data.cursor is None
        assert state.instigator_data.last_tick_timestamp == freeze_datetime.timestamp()


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
    with pendulum_freeze_time(freeze_datetime):
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
            "Error in config for job",
        )

        assert "Error in config for job" in caplog.text

    freeze_datetime = freeze_datetime.add(seconds=60)
    caplog.clear()
    with pendulum_freeze_time(freeze_datetime):
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
            "Error in config for job",
        )

        assert "Error in config for job" in caplog.text


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
        with pendulum_freeze_time(freeze_datetime):
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

            assert f"Run {run.run_id} created successfully but failed to launch:" in caplog.text

            assert "The entire purpose of this is to throw on launch" in caplog.text


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

    with pendulum_freeze_time(freeze_datetime):
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
    with pendulum_freeze_time(freeze_datetime):
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
            ' ["only_once"]' in caplog.text
        )

        launched_run = instance.get_runs()[0]

        # Manually create a new run with the same tags
        the_job.execute_in_process(
            run_config=launched_run.run_config,
            tags=launched_run.tags,
            instance=instance,
        )

        # Sensor loop still executes
    freeze_datetime = freeze_datetime.add(seconds=30)
    with pendulum_freeze_time(freeze_datetime):
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


def test_custom_interval_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=28, tz="UTC"), "US/Central"
    )
    with pendulum_freeze_time(freeze_datetime):
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

    with pendulum_freeze_time(freeze_datetime):
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        # no additional tick created after 30 seconds
        assert len(ticks) == 1

        freeze_datetime = freeze_datetime.add(seconds=30)

    with pendulum_freeze_time(freeze_datetime):
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 2

        expected_datetime = create_pendulum_time(year=2019, month=2, day=28, hour=0, minute=1)
        validate_tick(ticks[0], external_sensor, expected_datetime, TickStatus.SKIPPED)


def test_sensor_spans(workspace_context):
    loop = execute_sensor_iteration_loop(
        workspace_context,
        get_default_daemon_logger("dagster.daemon.SensorDaemon"),
        shutdown_event=threading.Event(),
    )

    assert next(loop) == SpanMarker.START_SPAN

    for _i in range(10):
        next_span = next(loop)
        assert (
            next_span != SpanMarker.START_SPAN
        ), "Started another span before finishing the previous one"

        if next_span == SpanMarker.END_SPAN:
            break


@pytest.mark.skipif(_IS_PENDULUM_3, reason="pendulum.set_test_now not supported in pendulum 3")
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

    with pendulum_freeze_time(freeze_datetime):
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


def test_sensor_start_stop(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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

    with pendulum_freeze_time(freeze_datetime):
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

    with pendulum_freeze_time(freeze_datetime):
        evaluate_sensors(workspace_context, executor)
        # should have new tick, new run, we are after the 30 second min interval
        assert instance.get_runs_count() == 2
        ticks = instance.get_ticks(external_origin_id, external_sensor.selector_id)
        assert len(ticks) == 2


def test_large_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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


def test_many_request_sensor(executor, submit_executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("many_request_sensor")
        instance.start_sensor(external_sensor)
        evaluate_sensors(workspace_context, executor, submit_executor=submit_executor)
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


def test_cursor_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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
    with pendulum_freeze_time(freeze_datetime):
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


def test_run_request_asset_selection_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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


def test_run_request_check_selection_only_sensor(
    executor, instance: DagsterInstance, workspace_context, external_repo
) -> None:
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("run_request_check_only_sensor")
        external_origin_id = external_sensor.get_external_origin_id()
        instance.start_sensor(external_sensor)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(external_origin_id, external_sensor.selector_id)
        assert len(ticks) == 0

        evaluate_sensors(workspace_context, executor)

        assert instance.get_runs_count() == 1
        run = instance.get_runs()[0]
        assert run.asset_check_selection == {AssetCheckKey(AssetKey("a"), "check_a")}
        assert run.asset_selection is None
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
            record.event_log_entry.dagster_event.event_specific_data.asset_key  # type: ignore[attr-defined]
            for record in instance.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION_PLANNED)
            )
        }
        assert planned_asset_keys == set()
        planned_check_keys = {
            record.event_log_entry.dagster_event.event_specific_data.asset_check_key  # type: ignore[attr-defined]
            for record in instance.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED)
            )
        }
        assert planned_check_keys == {AssetCheckKey(AssetKey("a"), "check_a")}


def test_run_request_stale_asset_selection_sensor_never_materialized(
    executor, instance, workspace_context, external_repo
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )

    with pendulum_freeze_time(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("run_request_stale_asset_sensor")
        instance.start_sensor(external_sensor)
        evaluate_sensors(workspace_context, executor)
        sensor_run = next((r for r in instance.get_runs() if r.job_name == "abc"), None)
        assert sensor_run is not None
        assert sensor_run.asset_selection == {AssetKey("a"), AssetKey("b"), AssetKey("c")}


def test_run_request_stale_asset_selection_sensor_empty(
    executor, instance, workspace_context, external_repo
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )

    materialize([a, b, c], instance=instance)

    with pendulum_freeze_time(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("run_request_stale_asset_sensor")
        instance.start_sensor(external_sensor)
        evaluate_sensors(workspace_context, executor)
        sensor_run = next((r for r in instance.get_runs() if r.job_name == "abc"), None)
        assert sensor_run is None


def test_run_request_stale_asset_selection_sensor_subset(
    executor, instance, workspace_context, external_repo
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )

    materialize([a], instance=instance)

    with pendulum_freeze_time(freeze_datetime):
        external_sensor = external_repo.get_external_sensor("run_request_stale_asset_sensor")
        instance.start_sensor(external_sensor)
        evaluate_sensors(workspace_context, executor)
        sensor_run = next((r for r in instance.get_runs() if r.job_name == "abc"), None)
        assert sensor_run is not None
        assert sensor_run.asset_selection == {AssetKey("b"), AssetKey("c")}


def test_targets_asset_selection_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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


def test_partitioned_asset_selection_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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


def test_asset_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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
    with pendulum_freeze_time(freeze_datetime):
        # should generate the foo asset
        foo_job.execute_in_process(instance=instance)

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


def test_asset_job_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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
    with pendulum_freeze_time(freeze_datetime):
        # should generate the foo asset
        foo_job.execute_in_process(instance=instance)

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


def test_asset_sensor_not_triggered_on_observation(
    executor, instance, workspace_context, external_repo
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
        foo_sensor = external_repo.get_external_sensor("asset_foo_sensor")
        instance.start_sensor(foo_sensor)

        # generates the foo asset observation
        foo_observation_job.execute_in_process(instance=instance)

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
    with pendulum_freeze_time(freeze_datetime):
        # should generate the foo asset
        foo_job.execute_in_process(instance=instance)

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


def test_multi_asset_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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
    with pendulum_freeze_time(freeze_datetime):
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

    with pendulum_freeze_time(freeze_datetime):
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


def test_asset_selection_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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


def test_multi_asset_sensor_targets_asset_selection(
    executor, instance, workspace_context, external_repo
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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
    with pendulum_freeze_time(freeze_datetime):
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

    with pendulum_freeze_time(freeze_datetime):
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


def test_multi_asset_sensor_w_many_events(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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
    with pendulum_freeze_time(freeze_datetime):
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

    with pendulum_freeze_time(freeze_datetime):
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


def test_multi_asset_sensor_w_no_cursor_update(
    executor, instance, workspace_context, external_repo
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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
    with pendulum_freeze_time(freeze_datetime):
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


def test_multi_asset_sensor_hourly_to_weekly(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2022, month=8, day=2, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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


def test_multi_asset_sensor_hourly_to_hourly(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2022, month=8, day=3, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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

    with pendulum_freeze_time(freeze_datetime):
        cursor_sensor = external_repo.get_external_sensor("multi_asset_sensor_hourly_to_hourly")
        instance.start_sensor(cursor_sensor)

        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            cursor_sensor.get_external_origin_id(), cursor_sensor.selector_id
        )
        assert len(ticks) == 2
        validate_tick(ticks[0], cursor_sensor, freeze_datetime, TickStatus.SKIPPED)


def test_sensor_result_multi_asset_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2022, month=8, day=3, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
        cursor_sensor = external_repo.get_external_sensor("sensor_result_multi_asset_sensor")
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


def test_cursor_update_sensor_result_multi_asset_sensor(
    executor, instance, workspace_context, external_repo
):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2022, month=8, day=3, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
        cursor_sensor = external_repo.get_external_sensor("cursor_sensor_result_multi_asset_sensor")
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
            TickStatus.FAILURE,
        )
        assert "Cannot set cursor in a multi_asset_sensor" in ticks[0].error.message


def test_multi_job_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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
        assert run.job_name == "the_job"

        freeze_datetime = freeze_datetime.add(seconds=60)
    with pendulum_freeze_time(freeze_datetime):
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
        assert run.run_config == {"ops": {"config_op": {"config": {"foo": "blah"}}}}
        assert run.tags
        assert run.tags.get("dagster/sensor_name") == "two_job_sensor"
        assert run.job_name == "config_job"


def test_bad_run_request_untargeted(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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
            "Error in sensor bad_request_untargeted: Sensor evaluation function returned a "
            "RunRequest for a sensor lacking a specified target (job_name, job, or "
            "jobs).",
        )


def test_bad_run_request_mismatch(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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
            "Error in sensor bad_request_mismatch: Sensor returned a RunRequest with "
            "job_name config_job. Expected one of: ['the_job']",
        )


def test_bad_run_request_unspecified(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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
            "Error in sensor bad_request_unspecified: Sensor returned a RunRequest that "
            "did not specify job_name for the requested run. Expected one of: "
            "['the_job', 'config_job']",
        )


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
        ).code_location.get_repository("the_status_in_code_repo")

        with pendulum_freeze_time(freeze_datetime):
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
            assert instigator_state.status == InstigatorStatus.DECLARED_IN_CODE

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

            # The instigator state status can be manually updated, as well as reset.
            instance.stop_sensor(
                always_running_origin.get_id(), running_sensor.selector_id, running_sensor
            )
            stopped_instigator_state = instance.get_instigator_state(
                always_running_origin.get_id(), running_sensor.selector_id
            )

            assert stopped_instigator_state
            assert stopped_instigator_state.status == InstigatorStatus.STOPPED

            instance.reset_sensor(running_sensor)
            reset_instigator_state = instance.get_instigator_state(
                always_running_origin.get_id(), running_sensor.selector_id
            )

            assert reset_instigator_state
            assert reset_instigator_state.status == InstigatorStatus.DECLARED_IN_CODE

            running_to_not_running_sensor = ExternalSensor(
                external_sensor_data=running_sensor._external_sensor_data._replace(  # noqa: SLF001
                    default_status=DefaultSensorStatus.STOPPED
                ),
                handle=running_sensor.handle.repository_handle,
            )
            current_state = running_to_not_running_sensor.get_current_instigator_state(
                stored_state=reset_instigator_state
            )

            assert current_state.status == InstigatorStatus.STOPPED
            assert current_state.instigator_data == reset_instigator_state.instigator_data

            evaluate_sensors(workspace_context, executor)

        freeze_datetime = freeze_datetime.add(seconds=30)
        with pendulum_freeze_time(freeze_datetime):
            evaluate_sensors(workspace_context, executor)
            wait_for_all_runs_to_start(instance)
            assert instance.get_runs_count() == 1
            run = instance.get_runs()[0]
            validate_run_started(run)
            ticks = instance.get_ticks(
                running_sensor.get_external_origin_id(), running_sensor.selector_id
            )
            assert len(ticks) == 3

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


def test_run_request_list_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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


def test_sensor_purge(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
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

    with pendulum_freeze_time(freeze_datetime):
        # create another tick
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 2

        freeze_datetime = freeze_datetime.add(days=2)

    with pendulum_freeze_time(freeze_datetime):
        # create another tick, but the first tick should be purged
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 2


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
        with pendulum_freeze_time(freeze_datetime):
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

        with pendulum_freeze_time(freeze_datetime):
            # create another tick, and the first tick should not be purged despite the fact that the
            # default purge day offset is 7
            evaluate_sensors(purge_ws_ctx, executor)
            ticks = instance.get_ticks(
                external_sensor.get_external_origin_id(), external_sensor.selector_id
            )
            assert len(ticks) == 2

            freeze_datetime = freeze_datetime.add(days=7)

        with pendulum_freeze_time(freeze_datetime):
            # create another tick, but the first tick should be purged
            evaluate_sensors(purge_ws_ctx, executor)
            ticks = instance.get_ticks(
                external_sensor.get_external_origin_id(), external_sensor.selector_id
            )
            assert len(ticks) == 2


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
        ).code_location
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

        with pendulum_freeze_time(freeze_datetime):
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
        with pendulum_freeze_time(freeze_datetime):
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
    assert tick.log_key == [
        external_sensor.handle.repository_name,
        external_sensor.name,
        str(tick.tick_id),
    ]
    assert tick.status == TickStatus.SKIPPED
    records = get_instigation_log_records(instance, tick.log_key)
    assert len(records) == 3
    assert records[0][LOG_RECORD_METADATA_ATTR]["orig_message"] == "hello hello"
    assert records[1][LOG_RECORD_METADATA_ATTR]["orig_message"].endswith("hello hello")
    assert records[2][LOG_RECORD_METADATA_ATTR]["orig_message"] == ("goodbye goodbye")
    assert records[2]["exc_info"].startswith("Traceback")
    assert "Exception: hi hi" in records[2]["exc_info"]
    instance.compute_log_manager.delete_logs(log_key=tick.log_key)


def test_sensor_logging_on_tick_failure(
    executor: ThreadPoolExecutor,
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
) -> None:
    external_sensor = external_repo.get_external_sensor("logging_fail_tick_sensor")
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

    assert instance.get_runs_count() == 0
    assert len(ticks) == 0

    evaluate_sensors(workspace_context, executor)

    ticks = instance.get_ticks(
        external_sensor.get_external_origin_id(), external_sensor.selector_id
    )

    assert len(ticks) == 1

    tick = ticks[0]

    assert tick.status == TickStatus.FAILURE
    assert tick.log_key
    assert tick.log_key == [
        external_sensor.handle.repository_name,
        external_sensor.name,
        str(tick.tick_id),
    ]

    records = get_instigation_log_records(instance, tick.log_key)

    assert len(records) == 1
    assert records[0][LOG_RECORD_METADATA_ATTR]["orig_message"] == "hello hello"

    assert isinstance(instance.compute_log_manager, CapturedLogManager)
    instance.compute_log_manager.delete_logs(log_key=tick.log_key)


def test_add_dynamic_partitions_sensor(
    caplog, executor, instance, workspace_context, external_repo
):
    foo_job.execute_in_process(instance=instance)  # creates event log storage tables
    instance.add_dynamic_partitions("quux", ["foo"])
    assert set(instance.get_dynamic_partitions("quux")) == set(["foo"])

    external_sensor = external_repo.get_external_sensor("add_dynamic_partitions_sensor")
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

    assert set(instance.get_dynamic_partitions("quux")) == set(["baz", "foo"])
    ticks = instance.get_ticks(
        external_sensor.get_external_origin_id(), external_sensor.selector_id
    )

    assert "Added partition keys to dynamic partitions definition 'quux': ['baz']" in caplog.text
    assert (
        "Skipping addition of partition keys for dynamic partitions definition 'quux' that already"
        " exist: ['foo']" in caplog.text
    )
    assert ticks[0].tick_data.dynamic_partitions_request_results == [
        DynamicPartitionsRequestResult(
            "quux", added_partitions=["baz"], deleted_partitions=None, skipped_partitions=["foo"]
        ),
    ]


def test_add_delete_skip_dynamic_partitions(
    caplog, executor, instance, workspace_context, external_repo
):
    foo_job.execute_in_process(instance=instance)  # creates event log storage tables
    instance.add_dynamic_partitions("quux", ["2"])
    assert set(instance.get_dynamic_partitions("quux")) == set(["2"])
    external_sensor = external_repo.get_external_sensor(
        "add_delete_dynamic_partitions_and_yield_run_requests_sensor"
    )
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

    freeze_datetime = to_timezone(
        create_pendulum_time(
            year=2023,
            month=2,
            day=27,
            hour=23,
            minute=59,
            second=59,
            tz="UTC",
        ),
        "US/Central",
    )

    with pendulum_freeze_time(freeze_datetime):
        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 1
        assert set(instance.get_dynamic_partitions("quux")) == set(["1"])

        assert instance.get_runs_count() == 2

        assert "Added partition keys to dynamic partitions definition 'quux': ['1']" in caplog.text
        assert (
            "Deleted partition keys from dynamic partitions definition 'quux': ['2']" in caplog.text
        )
        assert (
            "Skipping deletion of partition keys for dynamic partitions definition 'quux' that do"
            " not exist: ['3']" in caplog.text
        )
        assert ticks[0].tick_data.dynamic_partitions_request_results == [
            DynamicPartitionsRequestResult(
                "quux", added_partitions=["1"], deleted_partitions=None, skipped_partitions=[]
            ),
            DynamicPartitionsRequestResult(
                "quux", added_partitions=None, deleted_partitions=["2"], skipped_partitions=["3"]
            ),
        ]

        run = instance.get_runs()[0]
        assert run.run_config == {}
        assert run.tags
        assert run.tags.get("dagster/partition") == "1"

    freeze_datetime = freeze_datetime.add(seconds=60)
    with pendulum_freeze_time(freeze_datetime):
        evaluate_sensors(workspace_context, executor)

        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 2

        assert ticks[0].tick_data.dynamic_partitions_request_results == [
            DynamicPartitionsRequestResult(
                "quux", added_partitions=[], deleted_partitions=None, skipped_partitions=["1"]
            ),
            DynamicPartitionsRequestResult(
                "quux", added_partitions=None, deleted_partitions=[], skipped_partitions=["2", "3"]
            ),
        ]

        assert (
            "Skipping addition of partition keys for dynamic partitions definition 'quux' that"
            " already exist: ['1']" in caplog.text
        )
        assert (
            "Skipping deletion of partition keys for dynamic partitions definition 'quux' that do"
            " not exist: ['2', '3']" in caplog.text
        )


def test_error_on_deleted_dynamic_partitions_run_request(
    executor, instance, workspace_context, external_repo
):
    foo_job.execute_in_process(instance=instance)  # creates event log storage tables
    instance.add_dynamic_partitions("quux", ["2"])
    assert set(instance.get_dynamic_partitions("quux")) == set(["2"])
    external_sensor = external_repo.get_external_sensor(
        "error_on_deleted_dynamic_partitions_run_requests_sensor"
    )
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
    validate_tick(
        ticks[0],
        external_sensor,
        expected_datetime=None,
        expected_status=TickStatus.FAILURE,
        expected_run_ids=None,
        expected_error="Dynamic partition key 2 for partitions def 'quux' is invalid",
    )
    assert set(instance.get_dynamic_partitions("quux")) == set(["2"])


@pytest.mark.parametrize(
    "sensor_name, is_expected_success",
    [
        ("success_on_multipartition_run_request_with_two_dynamic_dimensions_sensor", True),
        ("error_on_multipartition_run_request_with_two_dynamic_dimensions_sensor", False),
    ],
)
def test_multipartitions_with_dynamic_dims_run_request_sensor(
    sensor_name, is_expected_success, executor, instance, workspace_context, external_repo
):
    external_sensor = external_repo.get_external_sensor(sensor_name)
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

    if is_expected_success:
        validate_tick(
            ticks[0],
            external_sensor,
            expected_datetime=None,
            expected_status=TickStatus.SUCCESS,
            expected_run_ids=None,
        )
    else:
        validate_tick(
            ticks[0],
            external_sensor,
            expected_datetime=None,
            expected_status=TickStatus.FAILURE,
            expected_run_ids=None,
            expected_error="does not exist in the set of valid partition keys",
        )


def test_multipartition_asset_with_static_time_dimensions_run_requests_sensor(
    executor, instance, workspace_context, external_repo
):
    external_sensor = external_repo.get_external_sensor(
        "multipartitions_with_static_time_dimensions_run_requests_sensor"
    )
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

    validate_tick(
        ticks[0],
        external_sensor,
        expected_datetime=None,
        expected_status=TickStatus.SUCCESS,
        expected_run_ids=None,
    )


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


def test_stale_request_context(instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )

    executor = ThreadPoolExecutor()
    blocking_executor = BlockingThreadPoolExecutor()

    with pendulum_freeze_time(freeze_datetime):
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

        futures = {}
        list(
            execute_sensor_iteration(
                workspace_context,
                get_default_daemon_logger("SensorDaemon"),
                threadpool_executor=executor,
                submit_threadpool_executor=None,
                sensor_tick_futures=futures,
            )
        )
        blocking_executor.allow()
        wait_for_futures(futures, timeout=FUTURES_TIMEOUT)

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

    blocking_executor.block()
    freeze_datetime = freeze_datetime.add(seconds=30)

    with pendulum_freeze_time(freeze_datetime):
        futures = {}
        list(
            execute_sensor_iteration(
                workspace_context,
                get_default_daemon_logger("SensorDaemon"),
                threadpool_executor=executor,
                sensor_tick_futures=futures,
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

        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 2

        wait_for_all_runs_to_start(instance)
        assert instance.get_runs_count() == 1, ticks[0].error
        run = instance.get_runs()[0]
        validate_run_started(run)

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


def test_start_tick_sensor(executor, instance, workspace_context, external_repo):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with pendulum_freeze_time(freeze_datetime):
        start_skip_sensor = external_repo.get_external_sensor("start_skip_sensor")
        instance.start_sensor(start_skip_sensor)
        evaluate_sensors(workspace_context, executor)
        last_tick = _get_last_tick(instance, start_skip_sensor)
        validate_tick(last_tick, start_skip_sensor, freeze_datetime, TickStatus.SKIPPED)
        last_sensor_start_time = last_tick.tick_data.cursor
        assert last_sensor_start_time

    freeze_datetime = freeze_datetime.add(seconds=60)
    with pendulum_freeze_time(freeze_datetime):
        evaluate_sensors(workspace_context, executor)
        last_tick = _get_last_tick(instance, start_skip_sensor)
        validate_tick(last_tick, start_skip_sensor, freeze_datetime, TickStatus.SUCCESS)
        assert last_sensor_start_time == last_tick.cursor

    freeze_datetime = freeze_datetime.add(seconds=60)
    with pendulum_freeze_time(freeze_datetime):
        instance.stop_sensor(
            start_skip_sensor.get_external_origin_id(),
            start_skip_sensor.selector_id,
            start_skip_sensor,
        )
        instance.start_sensor(start_skip_sensor)
        evaluate_sensors(workspace_context, executor)
        last_tick = _get_last_tick(instance, start_skip_sensor)
        validate_tick(last_tick, start_skip_sensor, freeze_datetime, TickStatus.SKIPPED)
        assert last_tick.cursor  # last sensor start time is still set
        assert last_tick.cursor != last_sensor_start_time
        last_sensor_start_time = last_tick.cursor

    freeze_datetime = freeze_datetime.add(seconds=60)
    with pendulum_freeze_time(freeze_datetime):
        evaluate_sensors(workspace_context, executor)
        last_tick = _get_last_tick(instance, start_skip_sensor)
        validate_tick(last_tick, start_skip_sensor, freeze_datetime, TickStatus.SUCCESS)
        assert last_sensor_start_time == last_tick.cursor


def _get_last_tick(instance, sensor):
    ticks = instance.get_ticks(sensor.get_external_origin_id(), sensor.selector_id)
    return ticks[0]
