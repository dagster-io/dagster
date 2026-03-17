from typing import Any

import dagster as dg
from dagster import OutputContext
from dagster._core.execution.context.input import InputContext


def test_build_output_context_asset_key():
    assert dg.build_output_context(asset_key="apple").asset_key == dg.AssetKey("apple")
    assert dg.build_output_context(asset_key=["apple", "banana"]).asset_key == dg.AssetKey(
        ["apple", "banana"]
    )
    assert dg.build_output_context(asset_key=dg.AssetKey("apple")).asset_key == dg.AssetKey("apple")


def test_build_output_context_asset_spec():
    asset_spec = dg.AssetSpec(
        key="key",
        group_name="group",
        code_version="code_version",
        partitions_def=dg.StaticPartitionsDefinition(["part1"]),
    )

    class TestIOManager(dg.IOManager):
        def handle_output(self, context: OutputContext, obj: object):
            assert context.asset_spec == asset_spec

        def load_input(self, context: InputContext) -> Any:
            pass

    dg.materialize([asset_spec], resources={"io_manager": TestIOManager()})


def test_build_output_context_with_output_metadata():
    expected_metadata = {"foo": "bar"}
    output_context = dg.build_output_context(output_metadata=expected_metadata)

    class TestIOManager(dg.IOManager):
        def handle_output(self, context: OutputContext, obj: object):
            assert context.output_metadata == expected_metadata

        def load_input(self, context: InputContext) -> Any:
            pass

    io_manager = TestIOManager()
    io_manager.handle_output(output_context, "test")


# ########################
# build_input_context
# ########################


def test_input_context_has_asset_partitions_with_partition_key_and_asset_key():
    """build_input_context with partition_key + asset_key auto-derives partition subset."""
    context = dg.build_input_context(
        partition_key="2024-01-15",
        asset_key=dg.AssetKey(["my_asset"]),
    )
    assert context.has_asset_partitions
    assert context.asset_partition_key == "2024-01-15"
    assert context.asset_partition_keys == ["2024-01-15"]
    assert context.asset_partition_key_range == dg.PartitionKeyRange("2024-01-15", "2024-01-15")
    assert context.get_asset_identifier() == ["my_asset", "2024-01-15"]


# ########################
# build_output_context
# ########################


def test_output_context_has_asset_partitions_with_partition_key_and_asset_key():
    """build_output_context with partition_key + asset_key auto-derives partition info."""
    context = dg.build_output_context(
        partition_key="2024-01-15",
        asset_key=dg.AssetKey(["my_asset"]),
    )
    assert context.has_asset_partitions
    assert context.asset_partition_key == "2024-01-15"
    assert context.asset_partition_keys == ["2024-01-15"]
    assert context.asset_partition_key_range == dg.PartitionKeyRange("2024-01-15", "2024-01-15")
    assert context.get_asset_identifier() == ["my_asset", "2024-01-15"]


def test_output_context_no_asset_partitions_without_asset_key():
    """partition_key alone does not create asset partitions."""
    context = dg.build_output_context(partition_key="2024-01-15")
    assert not context.has_asset_partitions


def test_output_context_with_explicit_partitions_def():
    """build_output_context with explicit partitions_def enables full partition expansion and time window."""
    daily = dg.DailyPartitionsDefinition(start_date="2024-01-01")
    instance = dg.DagsterInstance.ephemeral()

    context = dg.build_output_context(
        partition_key="2024-01-15",
        asset_key=dg.AssetKey(["my_asset"]),
        asset_partitions_def=daily,
        instance=instance,
    )
    assert context.has_asset_partitions
    assert context.asset_partition_keys == ["2024-01-15"]
    assert context.asset_partitions_def == daily

    tw = context.asset_partitions_time_window
    assert tw.start.year == 2024
    assert tw.start.month == 1
    assert tw.start.day == 15
    assert tw.end.day == 16
