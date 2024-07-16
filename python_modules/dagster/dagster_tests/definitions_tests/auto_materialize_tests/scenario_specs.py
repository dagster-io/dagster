import datetime

from dagster import AssetSpec, MultiPartitionKey, StaticPartitionsDefinition
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_spec import (
    SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE,
    AssetExecutionType,
)
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
from dagster._core.definitions.partition import DynamicPartitionsDefinition
from dagster._core.definitions.partition_mapping import StaticPartitionMapping
from dagster._core.definitions.time_window_partition_mapping import TimeWindowPartitionMapping
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
)
from dagster._time import parse_time_string

from .scenario_state import MultiAssetSpec, ScenarioSpec

############
# PARTITIONS
############

one_partitions_def = StaticPartitionsDefinition(["1"])
two_partitions_def = StaticPartitionsDefinition(["1", "2"])
three_partitions_def = StaticPartitionsDefinition(["1", "2", "3"])

time_partitions_start_str = "2013-01-05"
time_partitions_start_datetime = parse_time_string(time_partitions_start_str)
hourly_partitions_def = HourlyPartitionsDefinition(start_date=time_partitions_start_str + "-00:00")
daily_partitions_def = DailyPartitionsDefinition(start_date=time_partitions_start_str)
time_multipartitions_def = MultiPartitionsDefinition(
    {"time": daily_partitions_def, "static": two_partitions_def}
)
static_multipartitions_def = MultiPartitionsDefinition(
    {"static1": two_partitions_def, "static2": two_partitions_def}
)

self_partition_mapping = TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)

##############
# BASIC STATES
##############
one_asset = ScenarioSpec(asset_specs=[AssetSpec("A")])

one_upstream_observable_asset = ScenarioSpec(
    [
        AssetSpec(
            "A",
            metadata={
                SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE: AssetExecutionType.OBSERVATION.value
            },
        ),
        AssetSpec("B", deps=["A"]),
    ]
)

two_assets_in_sequence = ScenarioSpec(
    asset_specs=[AssetSpec("A"), AssetSpec("B", deps=["A"])],
)

three_assets_in_sequence = ScenarioSpec(
    asset_specs=[AssetSpec("A"), AssetSpec("B", deps=["A"]), AssetSpec("C", deps=["B"])],
)

two_assets_depend_on_one = ScenarioSpec(
    asset_specs=[AssetSpec("A"), AssetSpec("B", deps=["A"]), AssetSpec("C", deps=["A"])]
)

one_asset_depends_on_two = ScenarioSpec(
    asset_specs=[AssetSpec("A"), AssetSpec("B"), AssetSpec("C", deps=["A", "B"])]
)

diamond = ScenarioSpec(
    asset_specs=[
        AssetSpec(key="A"),
        AssetSpec(key="B", deps=["A"]),
        AssetSpec(key="C", deps=["A"]),
        AssetSpec(key="D", deps=["B", "C"]),
    ]
)

three_assets_not_subsettable = ScenarioSpec(
    asset_specs=[MultiAssetSpec(specs=[AssetSpec("A"), AssetSpec("B"), AssetSpec("C")])]
)

two_disconnected_graphs = ScenarioSpec(
    asset_specs=[
        AssetSpec("A"),
        AssetSpec("B", deps=["A"]),
        AssetSpec("C"),
        AssetSpec("D", deps=["C"]),
    ]
)

##################
# PARTITION STATES
##################

one_asset_self_dependency = one_asset.with_asset_properties(
    partitions_def=hourly_partitions_def,
    deps=[AssetDep("A", partition_mapping=self_partition_mapping)],
)

hourly_to_daily = two_assets_in_sequence.with_asset_properties(
    keys=["A"], partitions_def=hourly_partitions_def
).with_asset_properties(keys=["B"], partitions_def=daily_partitions_def)

two_assets_in_sequence_fan_in_partitions = two_assets_in_sequence.with_asset_properties(
    keys=["A"], partitions_def=three_partitions_def
).with_asset_properties(
    keys=["B"],
    partitions_def=one_partitions_def,
    deps=[AssetDep("A", partition_mapping=StaticPartitionMapping({"1": "1", "2": "1", "3": "1"}))],
)

two_assets_in_sequence_fan_out_partitions = two_assets_in_sequence.with_asset_properties(
    keys=["A"], partitions_def=one_partitions_def
).with_asset_properties(
    keys=["B"],
    partitions_def=three_partitions_def,
    deps=[AssetDep("A", partition_mapping=StaticPartitionMapping({"1": ["1", "2", "3"]}))],
)
dynamic_partitions_def = DynamicPartitionsDefinition(name="dynamic")


###########
# UTILITIES
###########


def day_partition_key(time: datetime.datetime, delta: int = 0) -> str:
    """Returns the partition key of a day partition delta days from the initial time."""
    return (time + datetime.timedelta(days=delta - 1)).strftime("%Y-%m-%d")


def hour_partition_key(time: datetime.datetime, delta: int = 0) -> str:
    """Returns the partition key of a day partition delta days from the initial time."""
    return (time + datetime.timedelta(hours=delta - 1)).strftime("%Y-%m-%d-%H:00")


def multi_partition_key(**kwargs) -> MultiPartitionKey:
    """Returns a MultiPartitionKey based off of the given kwargs."""
    return MultiPartitionKey(kwargs)
