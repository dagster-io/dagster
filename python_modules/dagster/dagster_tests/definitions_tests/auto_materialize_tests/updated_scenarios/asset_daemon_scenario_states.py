import pendulum
from dagster import AssetSpec, StaticPartitionsDefinition
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
from dagster._core.definitions.partition import DynamicPartitionsDefinition
from dagster._core.definitions.time_window_partition_mapping import TimeWindowPartitionMapping
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
)

from ..asset_daemon_scenario import AssetDaemonScenarioState

diamond = AssetDaemonScenarioState(
    asset_specs=[
        AssetSpec(key="A"),
        AssetSpec(key="B", deps=["A"]),
        AssetSpec(key="C", deps=["A"]),
        AssetSpec(key="D", deps=["B", "C"]),
    ]
)

one_asset = AssetDaemonScenarioState(asset_specs=[AssetSpec("A")])

two_assets_in_sequence = AssetDaemonScenarioState(
    asset_specs=[AssetSpec("A"), AssetSpec("B", deps=["A"])],
)

three_assets_in_sequence = AssetDaemonScenarioState(
    asset_specs=[AssetSpec("A"), AssetSpec("B", deps=["A"]), AssetSpec("C", deps=["B"])],
)

two_assets_depend_on_one = AssetDaemonScenarioState(
    asset_specs=[AssetSpec("A"), AssetSpec("B", deps=["A"]), AssetSpec("C", deps=["A"])]
)

one_asset_depends_on_two = AssetDaemonScenarioState(
    asset_specs=[AssetSpec("A"), AssetSpec("B"), AssetSpec("C", deps=["A", "B"])]
)

one_partitions_def = StaticPartitionsDefinition(["1"])
two_partitions_def = StaticPartitionsDefinition(["1", "2"])
three_partitions_def = StaticPartitionsDefinition(["1", "2", "3"])

time_partitions_start_str = "2013-01-05"
time_partitions_start_datetime = pendulum.parse(time_partitions_start_str)
hourly_partitions_def = HourlyPartitionsDefinition(start_date=time_partitions_start_str + "-00:00")
daily_partitions_def = DailyPartitionsDefinition(start_date=time_partitions_start_str)
time_multipartitions_def = MultiPartitionsDefinition(
    {"time": daily_partitions_def, "static": two_partitions_def}
)
static_multipartitions_def = MultiPartitionsDefinition(
    {"static1": two_partitions_def, "static2": two_partitions_def}
)

self_partition_mapping = TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)

hourly_to_daily = two_assets_in_sequence.with_asset_properties(
    keys=["A"], partitions_def=hourly_partitions_def
).with_asset_properties(keys=["B"], partitions_def=daily_partitions_def)
dynamic_partitions_def = DynamicPartitionsDefinition(name="dynamic")
