from unittest import mock

import pytest

from dagster import (
    AssetKey,
    AssetOut,
    DagsterInstance,
    DagsterInvariantViolationError,
    DagsterRunStatus,
    RunRequest,
    SensorEvaluationContext,
    asset,
    build_multi_asset_sensor_context,
    build_partitioned_asset_sensor_context,
    build_run_status_sensor_context,
    build_sensor_context,
    job,
    materialize,
    multi_asset,
    multi_asset_sensor,
    op,
    repository,
    run_failure_sensor,
    run_status_sensor,
    sensor,
    StaticPartitionsDefinition,
    DailyPartitionsDefinition,
    partitioned_asset_sensor,
    define_asset_job,
)
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvalidInvocationError
from dagster._core.test_utils import instance_for_test
from dagster._legacy import SensorExecutionContext


def test_sensor_context_backcompat():
    # If an instance of SensorEvaluationContext is a SensorExecutionContext, then annotating as
    # SensorExecutionContext and passing in a SensorEvaluationContext should pass mypy
    assert isinstance(SensorEvaluationContext(None, None, None, None, None), SensorExecutionContext)


def test_sensor_invocation_args():

    # Test no arg invocation
    @sensor(job_name="foo_pipeline")
    def basic_sensor_no_arg():
        return RunRequest(run_key=None, run_config={}, tags={})

    assert basic_sensor_no_arg().run_config == {}

    # Test underscore name
    @sensor(job_name="foo_pipeline")
    def basic_sensor(_):
        return RunRequest(run_key=None, run_config={}, tags={})

    assert basic_sensor(build_sensor_context()).run_config == {}
    assert basic_sensor(None).run_config == {}

    # Test sensor arbitrary arg name
    @sensor(job_name="foo_pipeline")
    def basic_sensor_with_context(_arbitrary_context):
        return RunRequest(run_key=None, run_config={}, tags={})

    context = build_sensor_context()

    # Pass context as positional arg
    assert basic_sensor_with_context(context).run_config == {}

    # pass context as kwarg
    assert basic_sensor_with_context(_arbitrary_context=context).run_config == {}

    # pass context as wrong kwarg
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Sensor invocation expected argument '_arbitrary_context'.",
    ):
        basic_sensor_with_context(  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
            bad_context=context
        )

    # pass context with no args
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Sensor evaluation function expected context argument, but no context argument was "
        "provided when invoking.",
    ):
        basic_sensor_with_context()  # pylint: disable=no-value-for-parameter

    # pass context with too many args
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Sensor invocation received multiple arguments. Only a first positional context "
        "parameter should be provided when invoking.",
    ):
        basic_sensor_with_context(  # pylint: disable=redundant-keyword-arg
            context, _arbitrary_context=None
        )


def test_instance_access_built_sensor():
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Attempted to initialize dagster instance, but no instance reference was provided.",
    ):
        build_sensor_context().instance  # pylint: disable=expression-not-assigned

    with instance_for_test() as instance:
        assert isinstance(build_sensor_context(instance).instance, DagsterInstance)


def test_instance_access_with_mock():
    mock_instance = mock.MagicMock(spec=DagsterInstance)
    assert build_sensor_context(instance=mock_instance).instance == mock_instance


def test_sensor_w_no_job():
    @sensor()
    def no_job_sensor():
        pass

    with pytest.raises(
        Exception,
        match=r".* Sensor evaluation function returned a RunRequest for a sensor lacking a "
        r"specified target .*",
    ):
        no_job_sensor.check_valid_run_requests(
            [
                RunRequest(
                    run_key=None,
                    run_config=None,
                    tags=None,
                )
            ]
        )


def test_run_status_sensor():
    @run_status_sensor(run_status=DagsterRunStatus.SUCCESS)
    def status_sensor(context):
        assert context.dagster_event.event_type_value == "PIPELINE_SUCCESS"

    @op
    def succeeds():
        return 1

    @job
    def my_job_2():
        succeeds()

    instance = DagsterInstance.ephemeral()
    result = my_job_2.execute_in_process(instance=instance, raise_on_error=False)

    dagster_run = result.dagster_run
    dagster_event = result.get_job_success_event()

    context = build_run_status_sensor_context(
        sensor_name="status_sensor",
        dagster_instance=instance,
        dagster_run=dagster_run,
        dagster_event=dagster_event,
    )

    status_sensor(context)


def test_run_failure_sensor():
    @run_failure_sensor
    def failure_sensor(context):
        assert context.dagster_event.event_type_value == "PIPELINE_FAILURE"

    @op
    def will_fail():
        raise Exception("failure")

    @job
    def my_job():
        will_fail()

    instance = DagsterInstance.ephemeral()
    result = my_job.execute_in_process(instance=instance, raise_on_error=False)

    dagster_run = result.dagster_run
    dagster_event = result.get_job_failure_event()

    context = build_run_status_sensor_context(
        sensor_name="failure_sensor",
        dagster_instance=instance,
        dagster_run=dagster_run,
        dagster_event=dagster_event,
    ).for_run_failure()

    failure_sensor(context)


def test_run_status_sensor_run_request():
    @op
    def succeeds():
        return 1

    @job
    def my_job_2():
        succeeds()

    instance = DagsterInstance.ephemeral()
    result = my_job_2.execute_in_process(instance=instance, raise_on_error=False)

    dagster_run = result.dagster_run
    dagster_event = result.get_job_success_event()

    context = build_run_status_sensor_context(
        sensor_name="status_sensor",
        dagster_instance=instance,
        dagster_run=dagster_run,
        dagster_event=dagster_event,
    )

    @run_status_sensor(run_status=DagsterRunStatus.SUCCESS)
    def basic_sensor(_):
        return RunRequest(run_key=None, run_config={}, tags={})

    assert basic_sensor(context).run_config == {}

    # test with context
    @run_status_sensor(run_status=DagsterRunStatus.SUCCESS)
    def basic_sensor_w_arg(context):
        assert context.dagster_event.event_type_value == "PIPELINE_SUCCESS"
        return RunRequest(run_key=None, run_config={}, tags={})

    assert basic_sensor_w_arg(context).run_config == {}


def test_run_failure_w_run_request():
    @op
    def will_fail():
        raise Exception("failure")

    @job
    def my_job():
        will_fail()

    instance = DagsterInstance.ephemeral()
    result = my_job.execute_in_process(instance=instance, raise_on_error=False)

    dagster_run = result.dagster_run
    dagster_event = result.get_job_failure_event()

    context = build_run_status_sensor_context(
        sensor_name="failure_sensor",
        dagster_instance=instance,
        dagster_run=dagster_run,
        dagster_event=dagster_event,
    ).for_run_failure()

    # Test no arg invocation
    @run_failure_sensor
    def basic_sensor(_):
        return RunRequest(run_key=None, run_config={}, tags={})

    assert basic_sensor(context).run_config == {}

    # test with context
    @run_failure_sensor
    def basic_sensor_w_arg(context):
        assert context.dagster_event.event_type_value == "PIPELINE_FAILURE"
        return RunRequest(run_key=None, run_config={}, tags={})

    assert basic_sensor_w_arg(context).run_config == {}


def test_multi_asset_sensor():
    @op
    def an_op():
        return 1

    @job
    def the_job():
        an_op()

    @asset
    def asset_a():
        return 1

    @asset
    def asset_b():
        return 1

    @multi_asset_sensor(asset_keys=[AssetKey("asset_a"), AssetKey("asset_b")], job=the_job)
    def a_and_b_sensor(context):
        asset_events = context.latest_materialization_records_by_key()
        if all(asset_events.values()):
            context.advance_all_cursors()
            return RunRequest(run_key=context.cursor, run_config={})

    @repository
    def my_repo():
        return [asset_a, asset_b, a_and_b_sensor]

    with instance_for_test() as instance:
        materialize([asset_a, asset_b], instance=instance)
        ctx = build_multi_asset_sensor_context(assets=[asset_a, asset_b], instance=instance)
        assert list(my_repo.get_sensor_def("a_and_b_sensor")(ctx))[0].run_config == {}


def test_multi_asset_sensor_partial_selection():
    @multi_asset(outs={"a": AssetOut(key="asset_a"), "b": AssetOut(key="asset_b")})
    def two_assets():
        return 1, 2

    @multi_asset_sensor(asset_keys=[AssetKey("asset_a")])
    def failing_sensor(context):
        pass

    with pytest.raises(DagsterInvalidDefinitionError, match="must select all other asset keys"):

        @repository
        def my_repo():
            return [two_assets, failing_sensor]

    @multi_asset_sensor(asset_keys=[AssetKey("asset_a"), AssetKey("asset_b")])
    def passing_sensor(context):
        pass

    @repository
    def my_repo():
        return [two_assets, passing_sensor]


def test_multi_asset_sensor_has_assets():
    @multi_asset(outs={"a": AssetOut(key="asset_a"), "b": AssetOut(key="asset_b")})
    def two_assets():
        return 1, 2

    @multi_asset_sensor(asset_keys=[AssetKey("asset_a"), AssetKey("asset_b")])
    def passing_sensor(context):
        assert isinstance(context.assets[0], AssetsDefinition)
        assert False

    @repository
    def my_repo():
        return [two_assets, passing_sensor]

    assert len(my_repo.get_sensor_def("passing_sensor").assets) == 1
    assert my_repo.get_sensor_def("passing_sensor").assets[0] == two_assets


def test_partitioned_asset_sensor_invalid_partitions():
    static_partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(partitions_def=static_partitions_def)
    def static_partitions_asset():
        return 1

    with instance_for_test() as instance:
        with build_partitioned_asset_sensor_context(
            assets=[static_partitions_asset], instance=instance
        ) as context:
            with pytest.raises(DagsterInvalidInvocationError):
                context.map_partition(
                    "2020-01-01", static_partitions_def, DailyPartitionsDefinition("2020-01-01")
                )


def test_partitioned_asset_sensor_context():
    daily_partitions_def = DailyPartitionsDefinition("2020-01-01")

    @asset(partitions_def=daily_partitions_def)
    def daily_partitions_asset():
        return 1

    @asset(partitions_def=daily_partitions_def)
    def daily_partitions_asset_2():
        return 1

    asset_job = define_asset_job(
        "yay", selection="daily_partitions_asset", partitions_def=daily_partitions_def
    )

    @partitioned_asset_sensor(assets=[daily_partitions_asset, daily_partitions_asset_2])
    def two_asset_sensor(context):
        asset_events = context.latest_materialization_records_by_key()

        first_asset_event = asset_events.get(AssetKey("daily_partitions_asset"))
        second_asset_event = asset_events.get(AssetKey("daily_partitions_asset_2"))

        if first_asset_event and second_asset_event:
            partition_1 = context.get_partition_from_event_log_record(first_asset_event)
            partition_2 = context.get_partition_from_event_log_record(second_asset_event)
            if partition_1 == partition_2:
                context.advance_all_cursors()
                return asset_job.run_request_for_partition(partition_1, run_key=None)

    with instance_for_test() as instance:
        materialize(
            [daily_partitions_asset, daily_partitions_asset_2],
            partition_key="2022-08-01",
            instance=instance,
        )
        ctx = build_partitioned_asset_sensor_context(
            [daily_partitions_asset, daily_partitions_asset_2], instance=instance
        )
        assert list(two_asset_sensor(ctx))[0].tags['dagster/partition'] == '2022-08-01'
        assert ctx.get_cursor_partition(AssetKey("daily_partitions_asset")) == "2022-08-01"
