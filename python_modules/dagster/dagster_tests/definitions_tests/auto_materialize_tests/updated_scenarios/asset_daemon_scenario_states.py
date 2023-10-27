from dagster import AssetSpec, StaticPartitionsDefinition
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
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

time_partitions_start = "2013-01-05"
hourly_partitions_def = HourlyPartitionsDefinition(start_date=time_partitions_start + "-00:00")
daily_partitions_def = DailyPartitionsDefinition(start_date=time_partitions_start)
time_multipartitions_def = MultiPartitionsDefinition(
    {"time": daily_partitions_def, "static": two_partitions_def}
)
static_multipartitions_def = MultiPartitionsDefinition(
    {"static1": two_partitions_def, "static2": two_partitions_def}
)
