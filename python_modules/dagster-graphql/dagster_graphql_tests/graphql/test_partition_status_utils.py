from unittest.mock import MagicMock

import dagster as dg
from dagster._core.definitions.partitions.definition import MultiPartitionsDefinition
from dagster._core.definitions.partitions.subset.default import DefaultPartitionsSubset
from dagster._core.definitions.partitions.utils import PartitionRangeStatus
from dagster._core.instance import DynamicPartitionsStore
from dagster_graphql.implementation.partition_status_utils import (
    build_multi_partition_ranges_generic,
)


def test_build_multi_partition_ranges_generic_ignores_invalid_key_format() -> None:
    """Regression test: a subset paired with a MultiPartitionsDefinition may contain
    keys that are not in the `<primary>|<secondary>` format (e.g. left over from
    when the asset was partitioned by a single dimension). These invalid keys
    should be filtered out rather than crashing
    `MultiPartitionsDefinition.get_partition_key_from_str`.
    """
    # Dimensions are sorted alphabetically; "date" is primary, "letter" is secondary.
    partitions_def = MultiPartitionsDefinition(
        {
            "date": dg.StaticPartitionsDefinition(["2022-01-01", "2022-01-02"]),
            "letter": dg.StaticPartitionsDefinition(["a", "b"]),
        }
    )

    # Subset contains two valid 2D keys plus a stray 1D key that should be ignored.
    subset = DefaultPartitionsSubset({"2022-01-01|a", "2022-01-02|b", "a"})

    ranges = build_multi_partition_ranges_generic(
        {PartitionRangeStatus.MATERIALIZED: subset},
        partitions_def,
        MagicMock(spec=DynamicPartitionsStore),
        build_secondary_dim=lambda status_subsets: {
            status: sorted(s.get_partition_keys()) for status, s in status_subsets.items()
        },
    )

    # Only the two valid 2D keys produce ranges; the "a" key is filtered out.
    assert len(ranges) == 2
    secondaries_by_primary = {
        r.primary_dim_start_key: r.secondary_dim[PartitionRangeStatus.MATERIALIZED] for r in ranges
    }
    assert secondaries_by_primary == {"2022-01-01": ["a"], "2022-01-02": ["b"]}
