from dagster import (
    DailyPartitionsDefinition,
    DimensionPartitionMapping,
    HourlyPartitionsDefinition,
    IdentityPartitionMapping,
    MultiPartitionMapping,
    MultiPartitionsDefinition,
    StaticPartitionMapping,
    StaticPartitionsDefinition,
    TimeWindowPartitionMapping,
)

from ...scenario_utils.base_scenario import asset_def

fanned_out_partitions_def = StaticPartitionsDefinition(["a_1", "a_2", "a_3"])
one_partition_partitions_def = StaticPartitionsDefinition(["a"])
two_partitions_partitions_def = StaticPartitionsDefinition(["a", "b"])
other_two_partitions_partitions_def = StaticPartitionsDefinition(["1", "2"])

multipartitioned_self_dependency = [
    asset_def(
        "asset1",
        partitions_def=MultiPartitionsDefinition(
            {
                "time": DailyPartitionsDefinition(start_date="2020-01-01"),
                "abc": StaticPartitionsDefinition(["a", "b", "c"]),
            }
        ),
        deps={
            "asset1": MultiPartitionMapping(
                {
                    "time": DimensionPartitionMapping(
                        "time", TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
                    ),
                    "abc": DimensionPartitionMapping("abc", IdentityPartitionMapping()),
                }
            )
        },
    )
]

one_asset_self_dependency = [
    asset_def(
        "asset1",
        partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
        deps={"asset1": TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)},
    )
]

root_assets_different_partitions_same_downstream = [
    asset_def("root1", partitions_def=two_partitions_partitions_def),
    asset_def("root2", partitions_def=other_two_partitions_partitions_def),
    asset_def(
        "downstream",
        {"root1": None, "root2": StaticPartitionMapping({"1": "a", "2": "b"})},
        partitions_def=two_partitions_partitions_def,
    ),
]


two_assets_in_sequence_fan_in_partitions = [
    asset_def("asset1", partitions_def=fanned_out_partitions_def),
    asset_def(
        "asset2",
        {"asset1": StaticPartitionMapping({"a_1": "a", "a_2": "a", "a_3": "a"})},
        partitions_def=one_partition_partitions_def,
    ),
]

two_assets_in_sequence_fan_out_partitions = [
    asset_def("asset1", partitions_def=one_partition_partitions_def),
    asset_def(
        "asset2",
        {"asset1": StaticPartitionMapping({"a": ["a_1", "a_2", "a_3"]})},
        partitions_def=fanned_out_partitions_def,
    ),
]

one_parent_starts_later_and_nonexistent_upstream_partitions_not_allowed = [
    asset_def("asset1", partitions_def=HourlyPartitionsDefinition("2023-01-01-03:00")),
    asset_def("asset2", partitions_def=HourlyPartitionsDefinition("2023-01-01-00:00")),
    asset_def(
        "asset3",
        partitions_def=HourlyPartitionsDefinition("2023-01-01-00:00"),
        deps=["asset1", "asset2"],
    ),
]

one_parent_starts_later_and_nonexistent_upstream_partitions_allowed = [
    asset_def("asset1", partitions_def=HourlyPartitionsDefinition("2023-01-01-03:00")),
    asset_def("asset2", partitions_def=HourlyPartitionsDefinition("2023-01-01-00:00")),
    asset_def(
        "asset3",
        partitions_def=HourlyPartitionsDefinition("2023-01-01-00:00"),
        deps={
            "asset1": TimeWindowPartitionMapping(allow_nonexistent_upstream_partitions=True),
            "asset2": TimeWindowPartitionMapping(),
        },
    ),
]
