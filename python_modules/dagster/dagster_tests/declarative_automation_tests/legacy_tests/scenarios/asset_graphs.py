import dagster as dg
from dagster import BackfillPolicy

from dagster_tests.declarative_automation_tests.scenario_utils.base_scenario import asset_def

fanned_out_partitions_def = dg.StaticPartitionsDefinition(["a_1", "a_2", "a_3"])
one_partition_partitions_def = dg.StaticPartitionsDefinition(["a"])
two_partitions_partitions_def = dg.StaticPartitionsDefinition(["a", "b"])
other_two_partitions_partitions_def = dg.StaticPartitionsDefinition(["1", "2"])

multipartitioned_self_dependency = [
    asset_def(
        "asset1",
        partitions_def=dg.MultiPartitionsDefinition(
            {
                "time": dg.DailyPartitionsDefinition(start_date="2020-01-01"),
                "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
            }
        ),
        deps={
            "asset1": dg.MultiPartitionMapping(
                {
                    "time": dg.DimensionPartitionMapping(
                        "time", dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
                    ),
                    "abc": dg.DimensionPartitionMapping("abc", dg.IdentityPartitionMapping()),
                }
            )
        },
    )
]

one_asset_self_dependency = [
    asset_def(
        "asset1",
        partitions_def=dg.DailyPartitionsDefinition(start_date="2020-01-01"),
        deps={"asset1": dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)},
    )
]

self_dependant_asset_downstream_of_regular_asset = [
    asset_def(
        "regular_asset",
        partitions_def=dg.DailyPartitionsDefinition("2023-01-01"),
        backfill_policy=BackfillPolicy.single_run(),
    ),
    asset_def(
        "self_dependant",
        partitions_def=dg.DailyPartitionsDefinition("2023-01-01"),
        deps={
            "self_dependant": dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
            "regular_asset": dg.TimeWindowPartitionMapping(),
        },
        backfill_policy=BackfillPolicy.multi_run(max_partitions_per_run=1),
    ),
]


regular_asset_downstream_of_self_dependant_asset = [
    asset_def(
        "self_dependant",
        partitions_def=dg.DailyPartitionsDefinition("2023-01-01"),
        backfill_policy=BackfillPolicy.multi_run(1),
        deps={
            "self_dependant": dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
        },
    ),
    asset_def(
        "regular_asset",
        partitions_def=dg.DailyPartitionsDefinition("2023-01-01"),
        backfill_policy=BackfillPolicy.multi_run(2),
        deps={
            "self_dependant": dg.TimeWindowPartitionMapping(),
        },
    ),
]

self_dependant_asset_downstream_of_regular_asset_multiple_run = [
    asset_def(
        "regular_asset",
        partitions_def=dg.DailyPartitionsDefinition("2023-01-01"),
        backfill_policy=BackfillPolicy.multi_run(max_partitions_per_run=1),
    ),
    asset_def(
        "self_dependant",
        partitions_def=dg.DailyPartitionsDefinition("2023-01-01"),
        deps={
            "self_dependant": dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
            "regular_asset": dg.TimeWindowPartitionMapping(),
        },
        backfill_policy=BackfillPolicy.multi_run(max_partitions_per_run=1),
    ),
]

self_dependant_asset_with_grouped_run_backfill_policy = [
    asset_def(
        "self_dependant",
        partitions_def=dg.DailyPartitionsDefinition("2023-01-01"),
        deps={"self_dependant": dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)},
        backfill_policy=BackfillPolicy.multi_run(3),
    )
]

self_dependant_asset_with_single_run_backfill_policy = [
    asset_def(
        "self_dependant",
        partitions_def=dg.DailyPartitionsDefinition("2023-01-01"),
        deps={"self_dependant": dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)},
        backfill_policy=BackfillPolicy.single_run(),
    )
]

self_dependant_asset_with_no_backfill_policy = [
    asset_def(
        "self_dependant",
        partitions_def=dg.DailyPartitionsDefinition("2023-01-01"),
        deps={"self_dependant": dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)},
    )
]

root_assets_different_partitions_same_downstream = [
    asset_def("root1", partitions_def=two_partitions_partitions_def),
    asset_def("root2", partitions_def=other_two_partitions_partitions_def),
    asset_def(
        "downstream",
        {"root1": None, "root2": dg.StaticPartitionMapping({"1": "a", "2": "b"})},
        partitions_def=two_partitions_partitions_def,
    ),
]


two_assets_in_sequence_fan_in_partitions = [
    asset_def("asset1", partitions_def=fanned_out_partitions_def),
    asset_def(
        "asset2",
        {"asset1": dg.StaticPartitionMapping({"a_1": "a", "a_2": "a", "a_3": "a"})},
        partitions_def=one_partition_partitions_def,
    ),
]

two_assets_in_sequence_fan_out_partitions = [
    asset_def("asset1", partitions_def=one_partition_partitions_def),
    asset_def(
        "asset2",
        {"asset1": dg.StaticPartitionMapping({"a": ["a_1", "a_2", "a_3"]})},
        partitions_def=fanned_out_partitions_def,
    ),
]

one_parent_starts_later_and_nonexistent_upstream_partitions_not_allowed = [
    asset_def("asset1", partitions_def=dg.HourlyPartitionsDefinition("2023-01-01-03:00")),
    asset_def("asset2", partitions_def=dg.HourlyPartitionsDefinition("2023-01-01-00:00")),
    asset_def(
        "asset3",
        partitions_def=dg.HourlyPartitionsDefinition("2023-01-01-00:00"),
        deps=["asset1", "asset2"],
    ),
]


# parent and child have the same partitions definition, grandparent and other_parent have differing
# partitions definitions
matching_partitions_with_different_subsets = [
    asset_def("grandparent", partitions_def=dg.DailyPartitionsDefinition("2021-01-01")),
    asset_def(
        "parent",
        partitions_def=dg.DailyPartitionsDefinition("2023-01-01"),
        deps={
            "grandparent": dg.TimeWindowPartitionMapping(),
        },
    ),
    asset_def("other_parent", partitions_def=dg.DailyPartitionsDefinition("2022-02-01")),
    asset_def(
        "child",
        partitions_def=dg.DailyPartitionsDefinition("2023-01-01"),
        deps={
            "parent": dg.TimeWindowPartitionMapping(),
            "other_parent": dg.TimeWindowPartitionMapping(),
        },
    ),
]


child_with_two_parents_with_identical_partitions = [
    asset_def(
        "parent_a",
        partitions_def=dg.DailyPartitionsDefinition("2023-01-01"),
    ),
    asset_def("parent_b", partitions_def=dg.DailyPartitionsDefinition("2023-01-01")),
    asset_def(
        "child",
        partitions_def=dg.DailyPartitionsDefinition("2023-01-01"),
        deps={
            "parent_a": dg.TimeWindowPartitionMapping(),
            "parent_b": dg.TimeWindowPartitionMapping(),
        },
    ),
]


one_parent_starts_later_and_nonexistent_upstream_partitions_allowed = [
    asset_def("asset1", partitions_def=dg.HourlyPartitionsDefinition("2023-01-01-03:00")),
    asset_def("asset2", partitions_def=dg.HourlyPartitionsDefinition("2023-01-01-00:00")),
    asset_def(
        "asset3",
        partitions_def=dg.HourlyPartitionsDefinition("2023-01-01-00:00"),
        deps={
            "asset1": dg.TimeWindowPartitionMapping(allow_nonexistent_upstream_partitions=True),
            "asset2": dg.TimeWindowPartitionMapping(),
        },
    ),
]
