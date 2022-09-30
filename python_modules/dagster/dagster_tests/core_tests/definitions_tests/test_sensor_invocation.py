import json
from typing import Optional
from unittest import mock

import pytest

from dagster import (
    AssetIn,
    AssetKey,
    AssetOut,
    AssetSelection,
    DagsterInstance,
    DagsterInvariantViolationError,
    DagsterRunStatus,
    DailyPartitionsDefinition,
    PartitionKeyRange,
    PartitionMapping,
    PartitionsDefinition,
    RunRequest,
    SensorEvaluationContext,
    StaticPartitionsDefinition,
    asset,
    build_multi_asset_sensor_context,
    build_run_status_sensor_context,
    build_sensor_context,
    define_asset_job,
    job,
    materialize,
    multi_asset,
    multi_asset_sensor,
    op,
    repository,
    run_failure_sensor,
    run_status_sensor,
    sensor,
)
from dagster._check import CheckError
from dagster._core.errors import DagsterInvalidInvocationError, DagsterInvalidSubsetError
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
        ctx = build_multi_asset_sensor_context(
            asset_keys=[AssetKey("asset_a"), AssetKey("asset_b")],
            instance=instance,
            repository_def=my_repo,
        )
        assert list(a_and_b_sensor(ctx))[0].run_config == {}


def test_multi_asset_nonexistent_key():
    @multi_asset_sensor(asset_keys=[AssetKey("nonexistent_key")])
    def failing_sensor(context):  # pylint: disable=unused-argument
        pass

    @repository
    def my_repo():
        return [failing_sensor]

    with pytest.raises(DagsterInvalidSubsetError):
        list(
            failing_sensor(
                build_multi_asset_sensor_context(
                    asset_keys=[AssetKey("nonexistent_key")], repository_def=my_repo
                )
            )
        )


def test_multi_asset_sensor_selection():
    @multi_asset(outs={"a": AssetOut(key="asset_a"), "b": AssetOut(key="asset_b")})
    def two_assets():
        return 1, 2

    @multi_asset_sensor(asset_keys=[AssetKey("asset_a")])
    def passing_sensor(context):  # pylint: disable=unused-argument
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
        assert (
            context.assets_defs_by_key[  # pylint: disable=comparison-with-callable
                AssetKey("asset_a")
            ]
            == two_assets
        )
        assert (
            context.assets_defs_by_key[  # pylint: disable=comparison-with-callable
                AssetKey("asset_b")
            ]
            == two_assets
        )
        assert len(context.assets_defs_by_key) == 2

    @repository
    def my_repo():
        return [two_assets, passing_sensor]

    assert passing_sensor.asset_selection.children == (AssetKey("asset_a"), AssetKey("asset_b"))
    with instance_for_test() as instance:
        ctx = build_multi_asset_sensor_context(
            asset_keys=[AssetKey("asset_a"), AssetKey("asset_b")],
            instance=instance,
            repository_def=my_repo,
        )
        list(passing_sensor(ctx))


def test_multi_asset_sensor_invalid_partitions():
    static_partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(partitions_def=static_partitions_def)
    def static_partitions_asset():
        return 1

    @asset(partitions_def=DailyPartitionsDefinition("2020-01-01"))
    def daily_asset():
        return 1

    @repository
    def my_repo():
        return [static_partitions_asset, daily_asset]

    with instance_for_test() as instance:
        with build_multi_asset_sensor_context(
            asset_keys=[static_partitions_asset.key], instance=instance, repository_def=my_repo
        ) as context:
            with pytest.raises(DagsterInvalidInvocationError):
                context.get_downstream_partition_keys(
                    "2020-01-01",
                    to_asset_key=AssetKey("static_partitions_asset"),
                    from_asset_key=AssetKey("daily_asset"),
                )


def test_partitions_multi_asset_sensor_context():
    daily_partitions_def = DailyPartitionsDefinition("2020-01-01")

    @asset(partitions_def=daily_partitions_def)
    def daily_partitions_asset():
        return 1

    @asset(partitions_def=daily_partitions_def)
    def daily_partitions_asset_2():
        return 1

    @repository
    def my_repo():
        return [daily_partitions_asset, daily_partitions_asset_2]

    asset_job = define_asset_job(
        "yay", selection="daily_partitions_asset", partitions_def=daily_partitions_def
    )

    @multi_asset_sensor(asset_keys=[daily_partitions_asset.key, daily_partitions_asset_2.key])
    def two_asset_sensor(context):
        partition_1 = next(
            iter(
                context.latest_materialization_records_by_partition(
                    daily_partitions_asset.key
                ).keys()
            )
        )
        partition_2 = next(
            iter(
                context.latest_materialization_records_by_partition(
                    daily_partitions_asset_2.key
                ).keys()
            )
        )

        if partition_1 == partition_2:
            context.advance_all_cursors()
            return asset_job.run_request_for_partition(partition_1, run_key=None)

    with instance_for_test() as instance:
        materialize(
            [daily_partitions_asset, daily_partitions_asset_2],
            partition_key="2022-08-01",
            instance=instance,
        )
        ctx = build_multi_asset_sensor_context(
            asset_keys=[daily_partitions_asset.key, daily_partitions_asset_2.key],
            instance=instance,
            repository_def=my_repo,
        )
        assert list(two_asset_sensor(ctx))[0].tags["dagster/partition"] == "2022-08-01"
        assert ctx.get_cursor_partition(AssetKey("daily_partitions_asset")) == "2022-08-01"


def test_invalid_partition_mapping():
    partitions_july = DailyPartitionsDefinition("2022-07-01")

    @asset(partitions_def=partitions_july)
    def july_daily_partitions():
        return 1

    @asset(partitions_def=DailyPartitionsDefinition("2022-08-01"))
    def august_daily_partitions():
        return 1

    @repository
    def my_repo():
        return [july_daily_partitions, august_daily_partitions]

    @multi_asset_sensor(asset_keys=[july_daily_partitions.key])
    def asset_sensor(context):
        partition = next(
            iter(
                context.latest_materialization_records_by_partition(
                    july_daily_partitions.key
                ).keys()
            )
        )

        # Line errors because we're trying to map to a partition that doesn't exist
        context.get_downstream_partition_keys(
            partition,
            to_asset_key=august_daily_partitions.key,
            from_asset_key=july_daily_partitions.key,
        )

    with instance_for_test() as instance:
        materialize(
            [july_daily_partitions],
            partition_key="2022-07-01",
            instance=instance,
        )
        ctx = build_multi_asset_sensor_context(
            asset_keys=[july_daily_partitions.key], instance=instance, repository_def=my_repo
        )
        with pytest.warns(UserWarning):
            list(asset_sensor(ctx))


def test_multi_asset_sensor_after_cursor_partition_flag():
    partitions_july = DailyPartitionsDefinition("2022-07-01")

    @asset(partitions_def=partitions_july)
    def july_daily_partitions():
        return 1

    @repository
    def my_repo():
        return [july_daily_partitions]

    @multi_asset_sensor(asset_keys=[july_daily_partitions.key])
    def after_cursor_partitions_asset_sensor(context):
        events = context.latest_materialization_records_by_key(
            [july_daily_partitions.key], after_cursor_partition=True
        )

        if (
            events[july_daily_partitions.key]
            and events[july_daily_partitions.key].event_log_entry.dagster_event.partition
            == "2022-07-10"
        ):  # first sensor invocation
            context.advance_all_cursors()
        else:  # second sensor invocation
            assert context.get_cursor_partition(july_daily_partitions.key) == "2022-07-10"
            materializations_by_key = context.latest_materialization_records_by_key()
            later_materialization = materializations_by_key.get(july_daily_partitions.key)
            assert later_materialization
            assert later_materialization.event_log_entry.dagster_event.partition == "2022-07-05"

            materializations_by_partition = context.latest_materialization_records_by_partition(
                july_daily_partitions.key
            )
            assert list(materializations_by_partition.keys()) == ["2022-07-05"]

            materializations_by_partition = context.latest_materialization_records_by_partition(
                july_daily_partitions.key, after_cursor_partition=True
            )
            # The cursor is set to the 2022-07-10 partition. Future searches with the default
            # after_cursor_partition=True will only return materializations with partitions after
            # 2022-07-10.
            assert set(materializations_by_partition.keys()) == set()

    with instance_for_test() as instance:
        materialize(
            [july_daily_partitions],
            partition_key="2022-07-10",
            instance=instance,
        )
        ctx = build_multi_asset_sensor_context(
            asset_keys=[july_daily_partitions.key], instance=instance, repository_def=my_repo
        )
        list(after_cursor_partitions_asset_sensor(ctx))
        materialize([july_daily_partitions], partition_key="2022-07-05", instance=instance)
        list(after_cursor_partitions_asset_sensor(ctx))


def test_multi_asset_sensor_all_partitions_materialized():
    partitions_july = DailyPartitionsDefinition("2022-07-01")

    @asset(partitions_def=partitions_july)
    def july_daily_partitions():
        return 1

    @repository
    def my_repo():
        return [july_daily_partitions]

    @multi_asset_sensor(asset_keys=[july_daily_partitions.key])
    def asset_sensor(context):
        assert context.all_partitions_materialized(july_daily_partitions.key) == False
        assert (
            context.all_partitions_materialized(
                july_daily_partitions.key, ["2022-07-10", "2022-07-11"]
            )
            == True
        )

    with instance_for_test() as instance:
        materialize(
            [july_daily_partitions],
            partition_key="2022-07-10",
            instance=instance,
        )
        materialize(
            [july_daily_partitions],
            partition_key="2022-07-11",
            instance=instance,
        )
        ctx = build_multi_asset_sensor_context(
            asset_keys=[july_daily_partitions.key], instance=instance, repository_def=my_repo
        )
        list(asset_sensor(ctx))


def test_multi_asset_sensor_custom_partition_mapping():
    class LastDownstreamPartitionMapping(PartitionMapping):
        def get_upstream_partitions_for_partition_range(
            self,
            downstream_partition_key_range: Optional[PartitionKeyRange],
            downstream_partitions_def: Optional[PartitionsDefinition],
            upstream_partitions_def: PartitionsDefinition,
        ) -> PartitionKeyRange:
            raise NotImplementedError()

        def get_downstream_partitions_for_partition_range(
            self,
            upstream_partition_key_range: PartitionKeyRange,
            downstream_partitions_def: Optional[PartitionsDefinition],
            upstream_partitions_def: PartitionsDefinition,
        ) -> PartitionKeyRange:
            if not isinstance(downstream_partitions_def, PartitionsDefinition):
                raise DagsterInvariantViolationError(
                    "Expected downstream_partitions_def to be a PartitionsDefinition"
                )
            first_partition_key = downstream_partitions_def.get_first_partition_key()
            return PartitionKeyRange(first_partition_key, first_partition_key)

    @asset(partitions_def=DailyPartitionsDefinition("2022-07-01"))
    def july_daily_partitions():
        return 1

    @asset(
        partitions_def=DailyPartitionsDefinition("2022-08-01"),
        ins={
            "upstream": AssetIn(
                key=july_daily_partitions.key, partition_mapping=LastDownstreamPartitionMapping()
            )
        },
    )
    def downstream_daily_partitions(upstream):  # pylint: disable=unused-argument
        return 1

    @repository
    def my_repo():
        return [july_daily_partitions, downstream_daily_partitions]

    @multi_asset_sensor(asset_keys=[july_daily_partitions.key])
    def asset_sensor(context):
        for partition_key, _ in context.latest_materialization_records_by_partition(
            july_daily_partitions.key
        ).items():
            for downstream_partition in context.get_downstream_partition_keys(
                partition_key,
                to_asset_key=downstream_daily_partitions.key,
                from_asset_key=july_daily_partitions.key,
            ):
                assert downstream_partition == "2022-08-01"

    with instance_for_test() as instance:
        materialize(
            [july_daily_partitions],
            partition_key="2022-07-10",
            instance=instance,
        )
        ctx = build_multi_asset_sensor_context(
            asset_keys=[july_daily_partitions.key], instance=instance, repository_def=my_repo
        )
        list(asset_sensor(ctx))


def test_multi_asset_sensor_retains_ordering_and_fetches_latest_per_partition():
    partition_ordering = ["2022-07-15", "2022-07-14", "2022-07-13", "2022-07-12", "2022-07-15"]
    partitions_july = DailyPartitionsDefinition("2022-07-01")

    @asset(partitions_def=partitions_july)
    def july_daily_partitions():
        return 1

    @repository
    def my_repo():
        return [july_daily_partitions]

    @multi_asset_sensor(asset_keys=[july_daily_partitions.key])
    def asset_sensor(context):
        assert (
            list(
                context.latest_materialization_records_by_partition(
                    july_daily_partitions.key
                ).keys()
            )
            == partition_ordering[
                1:
            ]  # 2022-07-15 is duplicated, so we fetch the later materialization and ignore the first materialization
        )

    with instance_for_test() as instance:
        for partition in partition_ordering:
            materialize(
                [july_daily_partitions],
                partition_key=partition,
                instance=instance,
            )
        ctx = build_multi_asset_sensor_context(
            asset_keys=[july_daily_partitions.key], instance=instance, repository_def=my_repo
        )
        list(asset_sensor(ctx))


def test_multi_asset_sensor_update_cursor_no_overwrite():
    @asset(partitions_def=DailyPartitionsDefinition("2022-07-01"))
    def july_asset():
        return 1

    @asset(partitions_def=DailyPartitionsDefinition("2022-08-01"))
    def august_asset():
        return 1

    @repository
    def my_repo():
        return [july_asset, august_asset]

    @multi_asset_sensor(asset_keys=[july_asset.key, august_asset.key])
    def after_cursor_partitions_asset_sensor(context):
        events = context.latest_materialization_records_by_key()

        if (
            events[july_asset.key]
            and events[july_asset.key].event_log_entry.dagster_event.partition == "2022-07-10"
        ):  # first sensor invocation
            context.advance_cursor({july_asset.key: events[july_asset.key]})
        else:  # second sensor invocation
            materialization = events[august_asset.key]
            assert materialization
            context.advance_cursor({august_asset.key: materialization})

            cursor = json.loads(context.cursor)
            partition, _ = cursor[str(july_asset.key)]
            assert partition == "2022-07-10"

    with instance_for_test() as instance:
        materialize(
            [july_asset],
            partition_key="2022-07-10",
            instance=instance,
        )
        ctx = build_multi_asset_sensor_context(
            asset_keys=[july_asset.key, august_asset.key], instance=instance, repository_def=my_repo
        )
        list(after_cursor_partitions_asset_sensor(ctx))
        materialize([august_asset], partition_key="2022-08-05", instance=instance)
        list(after_cursor_partitions_asset_sensor(ctx))


def test_multi_asset_sensor_advance_cursor_no_update_on_older_materialization():
    @asset(partitions_def=DailyPartitionsDefinition("2022-07-01"))
    def july_asset():
        return 1

    @repository
    def my_repo():
        return [july_asset]

    @multi_asset_sensor(asset_keys=[july_asset.key])
    def after_cursor_partitions_asset_sensor(context):
        events = context.materialization_records_for_key(july_asset.key, limit=2)

        context.advance_cursor({july_asset.key: events[1]})  # advance to later materialization
        context.advance_cursor(
            {july_asset.key: events[0]}
        )  # attempt to advance to earlier materialization

        cursor = json.loads(context.cursor)
        partition, storage_id = cursor[str(july_asset.key)]
        assert partition == "2022-07-10"
        assert storage_id == events[1].storage_id
        assert storage_id > events[0].storage_id

    with instance_for_test() as instance:
        materialize(
            [july_asset],
            partition_key="2022-07-05",
            instance=instance,
        )
        materialize([july_asset], partition_key="2022-07-10", instance=instance)
        ctx = build_multi_asset_sensor_context(
            asset_keys=[july_asset.key], instance=instance, repository_def=my_repo
        )
        list(after_cursor_partitions_asset_sensor(ctx))


def test_multi_asset_sensor_latest_materialization_records_per_asset_by_partition():
    @asset(partitions_def=DailyPartitionsDefinition("2022-07-01"))
    def july_asset():
        return 1

    @asset(partitions_def=DailyPartitionsDefinition("2022-07-01"))
    def july_asset_2():
        return 1

    @repository
    def my_repo():
        return [july_asset, july_asset_2]

    @multi_asset_sensor(asset_keys=[july_asset.key, july_asset_2.key])
    def my_sensor(context):
        events = context.latest_materialization_records_per_asset_by_partition()
        for partition_key, asset_and_materialization in events.items():
            assert partition_key == "2022-08-04"
            assert len(asset_and_materialization) == 2

    with instance_for_test() as instance:
        materialize(
            [july_asset_2, july_asset],
            partition_key="2022-08-04",
            instance=instance,
        )
        materialize([july_asset], partition_key="2022-08-04", instance=instance)
        ctx = build_multi_asset_sensor_context(
            asset_keys=[july_asset.key, july_asset_2.key], instance=instance, repository_def=my_repo
        )
        list(my_sensor(ctx))


def test_asset_keys_or_selection_mandatory():
    with pytest.raises(CheckError, match="Must provide asset_keys or asset_selection"):

        @multi_asset_sensor()
        def asset_selection_sensor(context):  # pylint: disable=unused-argument
            pass


def test_build_multi_asset_sensor_context_asset_selection():
    from dagster_tests.core_tests.asset_defs_tests.test_asset_selection import (
        alice,
        bob,
        candace,
        danny,
        edgar,
        fiona,
        george,
    )

    @multi_asset_sensor(
        asset_selection=AssetSelection.groups("ladies").upstream(depth=1, include_self=False)
    )
    def asset_selection_sensor(context):
        assert context.asset_keys == [candace.key, danny.key, alice.key]

    @repository
    def my_repo():
        return [alice, bob, candace, danny, edgar, fiona, george, asset_selection_sensor]

    with instance_for_test() as instance:
        ctx = build_multi_asset_sensor_context(
            asset_selection=AssetSelection.groups("ladies").upstream(depth=1, include_self=False),
            instance=instance,
            repository_def=my_repo,
        )
        asset_selection_sensor(ctx)


def test_asset_selection_or_asset_keys_mandatory_on_context():
    @repository
    def my_repo():
        return []

    with instance_for_test() as instance:
        with pytest.raises(CheckError, match="Must provide asset_keys or asset_selection"):
            build_multi_asset_sensor_context(
                instance=instance,
                repository_def=my_repo,
            )
