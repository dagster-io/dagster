from typing import Optional, Sequence, Union, cast

from dagster import (
    AssetDep,
    AssetsDefinition,
    AutoMaterializePolicy,
    DailyPartitionsDefinition,
    Definitions,
    HourlyPartitionsDefinition,
    PartitionsDefinition,
    RunRequest,
    TimeWindowPartitionMapping,
    asset,
)
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)
from dagster._time import parse_time_string

from auto_materialize_perf_tests.perf_scenario import ActivityHistory, PerfScenario


def asset_def(
    key: str,
    deps: Sequence[Union[str, AssetDep]],
    partitions_def: Optional[PartitionsDefinition] = None,
) -> AssetsDefinition:
    @asset(
        name=key,
        partitions_def=partitions_def,
        deps=deps,
        auto_materialize_policy=AutoMaterializePolicy.eager(),
    )
    def _asset() -> None: ...

    return _asset


hourly_one_year = HourlyPartitionsDefinition(start_date="2022-10-18-00:00")
hourly_two_years = HourlyPartitionsDefinition(start_date="2021-10-18-00:00")
daily_one_year = DailyPartitionsDefinition(start_date="2022-10-18")
daily_four_years = DailyPartitionsDefinition(start_date="2019-10-18")
daily_ten_years = DailyPartitionsDefinition(start_date="2013-10-18")


assets = [
    asset_def("a_1", deps=[], partitions_def=hourly_two_years),
    asset_def("a_2", deps=[], partitions_def=hourly_two_years),
    asset_def("b", deps=["a_1"], partitions_def=daily_four_years),
    asset_def(
        "c",
        deps=[
            "a_1",
            AssetDep("a_2", partition_mapping=TimeWindowPartitionMapping(start_offset=-3)),
        ],
        partitions_def=hourly_one_year,
    ),
    asset_def("d", deps=["a_1", "b"], partitions_def=daily_four_years),
    asset_def("e", deps=["c"], partitions_def=daily_ten_years),
    asset_def("f", deps=["c"], partitions_def=daily_one_year),
    asset_def(
        "leaf",
        deps=[
            "d",
            AssetDep("e", partition_mapping=TimeWindowPartitionMapping(start_offset=-28)),
            "f",
        ],
        partitions_def=daily_four_years,
    ),
]
assets_by_key = {asset_def.key.to_user_string(): asset_def for asset_def in assets}


defs = Definitions(assets)


def build_run_request_for_all_partitions(asset_def: AssetsDefinition) -> RunRequest:
    partitions_def = cast(PartitionsDefinition, asset_def.partitions_def)
    return RunRequest(
        asset_selection=[asset_def.key],
        tags={
            ASSET_PARTITION_RANGE_START_TAG: partitions_def.get_first_partition_key(),
            ASSET_PARTITION_RANGE_END_TAG: partitions_def.get_last_partition_key(),
        },
    )


partition_mappings_galore_perf_scenario = PerfScenario(
    name="partition_mappings_galore",
    defs=defs,
    max_execution_time_seconds=50,
    activity_history=ActivityHistory(
        [build_run_request_for_all_partitions(a) for a in assets]
        + [build_run_request_for_all_partitions(assets_by_key["d"])]
    ),
    current_time=parse_time_string("2023-09-06T00:05"),
)
