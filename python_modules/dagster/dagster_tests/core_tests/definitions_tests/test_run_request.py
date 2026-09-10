from collections.abc import Sequence
from typing import cast

import dagster as dg
import pytest
from dagster._core.definitions.events import AssetKeyPartitionKey


@pytest.mark.parametrize(
    "prior_partitions,dynamic_partitions_requests,expect_success",
    [
        (["a"], [], True),
        ([], [], False),
        ([], [dg.AddDynamicPartitionsRequest("something", ["a"])], True),
        ([], [dg.AddDynamicPartitionsRequest("something_else", ["a"])], False),
        (["a"], [dg.DeleteDynamicPartitionsRequest("something", ["a"])], False),
        (["a"], [dg.DeleteDynamicPartitionsRequest("something_else", ["a"])], True),
    ],
)
def test_validate_dynamic_partitions(
    prior_partitions: Sequence[str],
    dynamic_partitions_requests: Sequence[
        dg.AddDynamicPartitionsRequest | dg.DeleteDynamicPartitionsRequest
    ],
    expect_success: bool,
):
    partitions_def = dg.DynamicPartitionsDefinition(name="something")

    @dg.job(partitions_def=partitions_def)
    def job1():
        pass

    run_request = dg.RunRequest(partition_key="a")
    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions(cast("str", partitions_def.name), prior_partitions)

        if expect_success:
            run_request.with_resolved_tags_and_config(
                target_definition=job1,
                dynamic_partitions_requests=dynamic_partitions_requests,
                dynamic_partitions_store=instance,
            )
        else:
            with pytest.raises(
                dg.DagsterUnknownPartitionError, match=r"Could not find a partition with key `a`."
            ):
                run_request.with_resolved_tags_and_config(
                    target_definition=job1,
                    dynamic_partitions_requests=dynamic_partitions_requests,
                    dynamic_partitions_store=instance,
                )


def test_for_asset_partition_range() -> None:
    partitions_def = dg.StaticPartitionsDefinition(["a", "b", "c"])

    @dg.asset(partitions_def=partitions_def)
    def partitioned_asset() -> None: ...

    @dg.asset(partitions_def=partitions_def)
    def other_partitioned_asset() -> None: ...

    @dg.asset
    def unpartitioned_asset() -> None: ...

    defs = dg.Definitions(assets=[partitioned_asset, other_partitioned_asset, unpartitioned_asset])

    @dg.sensor(asset_selection=[partitioned_asset, other_partitioned_asset, unpartitioned_asset])
    def range_sensor():
        return dg.RunRequest.for_asset_partition_range(
            run_key="a-b",
            asset_selection=[
                partitioned_asset.key,
                other_partitioned_asset.key,
                unpartitioned_asset.key,
            ],
            partition_key_range=dg.PartitionKeyRange("a", "b"),
            run_config={"foo": "bar"},
            tags={"tagkey": "tagvalue"},
        )

    with dg.instance_for_test() as instance:
        context = dg.build_sensor_context(definitions=defs, instance=instance)
        run_requests = range_sensor.evaluate_tick(context).run_requests
        assert run_requests is not None
        request = run_requests[0]

    assert request.requires_backfill_daemon()
    assert request.run_key == "a-b"
    assert request.run_config == {"foo": "bar"}
    assert request.tags["tagkey"] == "tagvalue"
    assert request.asset_graph_subset
    assert set(request.asset_graph_subset.iterate_asset_partitions()) == {
        AssetKeyPartitionKey(partitioned_asset.key, "a"),
        AssetKeyPartitionKey(partitioned_asset.key, "b"),
        AssetKeyPartitionKey(other_partitioned_asset.key, "a"),
        AssetKeyPartitionKey(other_partitioned_asset.key, "b"),
        AssetKeyPartitionKey(unpartitioned_asset.key),
    }


def test_for_asset_partition_range_requires_multiple_partitions() -> None:
    partitions_def = dg.StaticPartitionsDefinition(["a", "b"])

    @dg.asset(partitions_def=partitions_def)
    def partitioned_asset() -> None: ...

    defs = dg.Definitions(assets=[partitioned_asset])

    @dg.sensor(asset_selection=[partitioned_asset])
    def range_sensor():
        return dg.RunRequest.for_asset_partition_range(
            asset_selection=[partitioned_asset.key],
            partition_key_range=dg.PartitionKeyRange("a", "a"),
        )

    with dg.instance_for_test() as instance:
        context = dg.build_sensor_context(definitions=defs, instance=instance)
        with pytest.raises(
            dg.DagsterInvalidInvocationError,
            match="partition_key_range must contain at least two partitions",
        ):
            range_sensor.evaluate_tick(context)


def test_for_asset_partition_range_requires_same_partitions_definition() -> None:
    daily_partitions_def = dg.DailyPartitionsDefinition(
        start_date="2024-05-01", end_date="2024-06-03"
    )
    monthly_partitions_def = dg.MonthlyPartitionsDefinition(
        start_date="2024-05-01", end_date="2024-07-01"
    )

    @dg.asset(partitions_def=daily_partitions_def)
    def daily_asset() -> None: ...

    @dg.asset(partitions_def=monthly_partitions_def)
    def monthly_asset() -> None: ...

    defs = dg.Definitions(assets=[daily_asset, monthly_asset])

    @dg.sensor(asset_selection=[daily_asset, monthly_asset])
    def range_sensor():
        return dg.RunRequest.for_asset_partition_range(
            asset_selection=[daily_asset.key, monthly_asset.key],
            partition_key_range=dg.PartitionKeyRange("2024-05-01", "2024-06-01"),
        )

    with dg.instance_for_test() as instance:
        context = dg.build_sensor_context(definitions=defs, instance=instance)
        with pytest.raises(
            dg.DagsterInvalidInvocationError,
            match="must have the same partitions definition",
        ):
            range_sensor.evaluate_tick(context)


@pytest.mark.parametrize(
    ("partition_key_range", "invalid_endpoint"),
    [
        (dg.PartitionKeyRange("2024-05-02", "2024-06-01"), "start '2024-05-02'"),
        (dg.PartitionKeyRange("2024-05-01", "2024-05-31"), "end '2024-05-31'"),
    ],
)
def test_for_asset_partition_range_requires_valid_endpoint_keys(
    partition_key_range: dg.PartitionKeyRange, invalid_endpoint: str
) -> None:
    partitions_def = dg.MonthlyPartitionsDefinition(start_date="2024-05-01", end_date="2024-07-01")

    @dg.asset(partitions_def=partitions_def)
    def partitioned_asset() -> None: ...

    defs = dg.Definitions(assets=[partitioned_asset])

    @dg.sensor(asset_selection=[partitioned_asset])
    def range_sensor():
        return dg.RunRequest.for_asset_partition_range(
            asset_selection=[partitioned_asset.key],
            partition_key_range=partition_key_range,
        )

    with dg.instance_for_test() as instance:
        context = dg.build_sensor_context(definitions=defs, instance=instance)
        with pytest.raises(
            dg.DagsterInvalidInvocationError,
            match=f"partition_key_range {invalid_endpoint} is not a valid partition key",
        ):
            range_sensor.evaluate_tick(context)


def test_for_asset_partition_range_includes_pending_dynamic_partitions() -> None:
    partitions_def = dg.DynamicPartitionsDefinition(name="dynamic_range")

    @dg.asset(partitions_def=partitions_def)
    def partitioned_asset() -> None: ...

    @dg.sensor(asset_selection=[partitioned_asset])
    def range_sensor():
        return dg.SensorResult(
            dynamic_partitions_requests=[partitions_def.build_add_request(["a", "b"])],
            run_requests=[
                dg.RunRequest.for_asset_partition_range(
                    asset_selection=[partitioned_asset.key],
                    partition_key_range=dg.PartitionKeyRange("a", "b"),
                )
            ],
        )

    defs = dg.Definitions(assets=[partitioned_asset], sensors=[range_sensor])
    with dg.instance_for_test() as instance:
        context = dg.build_sensor_context(definitions=defs, instance=instance)
        run_requests = range_sensor.evaluate_tick(context).run_requests
        assert run_requests is not None
        request = run_requests[0]

    assert request.asset_graph_subset
    assert set(request.asset_graph_subset.iterate_asset_partitions()) == {
        AssetKeyPartitionKey(partitioned_asset.key, "a"),
        AssetKeyPartitionKey(partitioned_asset.key, "b"),
    }


def test_for_asset_partition_range_rejects_partial_non_subsettable_multi_asset() -> None:
    partitions_def = dg.StaticPartitionsDefinition(["a", "b"])

    @dg.multi_asset(
        outs={"one": dg.AssetOut(), "two": dg.AssetOut()}, partitions_def=partitions_def
    )
    def two_assets():
        yield dg.Output(None, output_name="one")
        yield dg.Output(None, output_name="two")

    @dg.sensor(asset_selection=dg.AssetSelection.assets(*two_assets.keys))
    def range_sensor():
        return dg.RunRequest.for_asset_partition_range(
            asset_selection=[dg.AssetKey("one")],
            partition_key_range=dg.PartitionKeyRange("a", "b"),
        )

    defs = dg.Definitions(assets=[two_assets], sensors=[range_sensor])
    with dg.instance_for_test() as instance:
        context = dg.build_sensor_context(definitions=defs, instance=instance)
        with pytest.raises(
            dg.DagsterInvalidSubsetError,
            match="must include asset keys that are required to execute together",
        ):
            range_sensor.evaluate_tick(context)


def test_for_asset_partition_range_rejects_non_materializable_asset() -> None:
    partitions_def = dg.StaticPartitionsDefinition(["a", "b"])

    @dg.observable_source_asset(partitions_def=partitions_def)
    def source_asset() -> dg.DataVersion:
        return dg.DataVersion("version")

    @dg.sensor(asset_selection=[source_asset])
    def range_sensor():
        return dg.RunRequest.for_asset_partition_range(
            asset_selection=[source_asset.key],
            partition_key_range=dg.PartitionKeyRange("a", "b"),
        )

    defs = dg.Definitions(assets=[source_asset], sensors=[range_sensor])
    with dg.instance_for_test() as instance:
        context = dg.build_sensor_context(definitions=defs, instance=instance)
        with pytest.raises(
            dg.DagsterInvalidSubsetError,
            match="includes non-materializable asset keys",
        ):
            range_sensor.evaluate_tick(context)
