"""Shared utilities for building partition status responses.

This module contains status-agnostic algorithms for building partition status
representations used by both regular assets and asset checks.
"""

from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition import (
    MultiPartitionsDefinition,
    PartitionsDefinition,
    TimeWindowPartitionsDefinition,
)
from dagster._core.definitions.partitions.subset import PartitionsSubset, TimeWindowPartitionsSubset
from dagster._core.instance import DynamicPartitionsStore
from dagster._record import record

StatusT = TypeVar("StatusT", bound=Enum)


@record
class TimePartitionRange(Generic[StatusT]):
    """Generic time partition range with status (status-agnostic)."""

    start_time: float
    end_time: float
    start_key: str
    end_key: str
    status: StatusT


def convert_time_window_subset_to_generic_ranges(
    subset: TimeWindowPartitionsSubset,
    status: StatusT,
) -> Sequence[TimePartitionRange[StatusT]]:
    """Convert a TimeWindowPartitionsSubset to generic range objects.

    Args:
        subset: Subset containing time windows
        status: Status to assign to all ranges

    Returns:
        List of TimePartitionRange objects with the given status
    """
    ranges = []
    partitions_def = subset.partitions_def

    for time_window in subset.included_time_windows:
        partition_key_range = partitions_def.get_partition_key_range_for_time_window(
            time_window.to_public_time_window()
        )
        ranges.append(
            TimePartitionRange(
                start_time=time_window.start_timestamp,
                end_time=time_window.end_timestamp,
                start_key=partition_key_range.start,
                end_key=partition_key_range.end,
                status=status,
            )
        )

    return ranges


def build_time_partition_ranges_generic(
    subsets: Mapping[StatusT, TimeWindowPartitionsSubset],
) -> Sequence[TimePartitionRange[StatusT]]:
    """Build time-based ranges for all provided statuses.

    Algorithm:
    1. For each status, convert its TimeWindowPartitionsSubset to ranges
    2. Combine all ranges into single list
    3. Sort by start time

    Args:
        subsets: Mapping from status enum to TimeWindowPartitionsSubset

    Returns:
        List of TimePartitionRange objects sorted by start time
    """
    all_ranges = []

    # Convert each status subset to ranges
    for status, subset in subsets.items():
        if subset:
            all_ranges.extend(convert_time_window_subset_to_generic_ranges(subset, status))

    # Sort by start time
    all_ranges.sort(key=lambda r: r.start_time)

    return all_ranges


def extract_partition_keys_by_status(
    subsets: Mapping[StatusT, Optional[PartitionsSubset]],
    partitions_def: PartitionsDefinition,
    dynamic_partitions_store: DynamicPartitionsStore,
) -> Mapping[StatusT, Sequence[str]]:
    """Extract and sort partition keys for each status.

    Args:
        subsets: Mapping from status enum to PartitionsSubset (can contain None values)
        partitions_def: Partition definition for creating empty subsets
        dynamic_partitions_store: Store for loading dynamic partitions

    Returns:
        Mapping from status to sorted list of partition keys
    """
    with partition_loading_context(dynamic_partitions_store=dynamic_partitions_store):
        result = {}

        for status, subset in subsets.items():
            if subset is None:
                result[status] = []
            else:
                result[status] = sorted(subset.get_partition_keys())

        return result


@record
class MultiPartitionRange(Generic[StatusT]):
    """Generic multi-partition range (status-agnostic).

    Represents a range in the primary dimension with associated secondary
    dimension statuses (which can be recursive).
    """

    primary_dim_start_key: str
    primary_dim_end_key: str
    primary_dim_start_time: Optional[float]
    primary_dim_end_time: Optional[float]
    secondary_dim: Any  # Recursive structure - can be any partition status type


def build_multi_partition_ranges_generic(
    subsets: Mapping[StatusT, Optional[PartitionsSubset]],
    partitions_def: MultiPartitionsDefinition,
    dynamic_partitions_store: DynamicPartitionsStore,
    build_secondary_dim: Callable[[Mapping[StatusT, PartitionsSubset]], Any],
) -> Sequence[MultiPartitionRange]:
    """Build 2D run-length encoded partition ranges.

    Algorithm:
    1. For each status, build mapping: primary_key → secondary_subset
    2. Run-length encoding:
       - Iterate through primary dimension keys in order
       - Group consecutive primary keys where ALL secondary patterns match
       - For each group, call build_secondary_dim on secondary dimension subsets
    3. Calculate time bounds if primary dimension is time-based

    Args:
        subsets: Mapping from status enum to PartitionsSubset
        partitions_def: Multi-dimensional partition definition
        dynamic_partitions_store: Store for loading dynamic partitions
        build_secondary_dim: Function to recursively build secondary dimension statuses

    Returns:
        List of MultiPartitionRange objects
    """
    # Get dimension definitions
    primary_dim = partitions_def.primary_dimension
    secondary_dim = partitions_def.secondary_dimension

    # Build mappings: primary_key → {status → secondary_keys}
    with partition_loading_context(dynamic_partitions_store=dynamic_partitions_store):
        primary_keys = list(primary_dim.partitions_def.get_partition_keys())

        # For each status, build mapping: primary_key → set of secondary keys
        dim2_keys_by_dim1_by_status: dict[StatusT, dict[str, set[str]]] = {}

        for status, subset in subsets.items():
            if subset:
                dim2_keys_by_dim1 = defaultdict(set)
                for partition_key in subset.get_partition_keys():
                    multipartition_key = partitions_def.get_partition_key_from_str(partition_key)
                    primary_key_val = multipartition_key.keys_by_dimension[primary_dim.name]
                    secondary_key_val = multipartition_key.keys_by_dimension[secondary_dim.name]
                    dim2_keys_by_dim1[primary_key_val].add(secondary_key_val)
                dim2_keys_by_dim1_by_status[status] = dim2_keys_by_dim1

        # Convert to subsets for each primary key
        primary_to_status_subsets: dict[str, dict[StatusT, PartitionsSubset]] = {}

        for primary_key in primary_keys:
            status_subsets: dict[StatusT, PartitionsSubset] = {}

            # Create secondary subsets for each status
            for status, dim2_keys_by_dim1 in dim2_keys_by_dim1_by_status.items():
                if primary_key in dim2_keys_by_dim1:
                    secondary_keys = dim2_keys_by_dim1[primary_key]
                    status_subsets[status] = (
                        secondary_dim.partitions_def.empty_subset().with_partition_keys(
                            secondary_keys
                        )
                    )

            primary_to_status_subsets[primary_key] = status_subsets

        # Run-length encoding: group consecutive primary keys with identical secondary patterns
        ranges = []
        i = 0
        while i < len(primary_keys):
            start_key = primary_keys[i]
            start_subsets = primary_to_status_subsets[start_key]

            # Skip empty primary keys (no partitions in any status)
            if not start_subsets:
                i += 1
                continue

            # Find end of range with identical secondary patterns
            j = i + 1
            while j < len(primary_keys):
                if primary_to_status_subsets[primary_keys[j]] != start_subsets:
                    break
                j += 1

            end_key = primary_keys[j - 1]

            # Build secondary dimension status recursively
            secondary_statuses = build_secondary_dim(start_subsets)

            # Get time range for primary dimension if it's time-based
            start_time = None
            end_time = None
            if isinstance(primary_dim.partitions_def, TimeWindowPartitionsDefinition):
                start_time_window = primary_dim.partitions_def.time_window_for_partition_key(
                    start_key
                )
                end_time_window = primary_dim.partitions_def.time_window_for_partition_key(end_key)
                start_time = start_time_window.start.timestamp()
                end_time = end_time_window.end.timestamp()

            ranges.append(
                MultiPartitionRange(
                    primary_dim_start_key=start_key,
                    primary_dim_end_key=end_key,
                    primary_dim_start_time=start_time,
                    primary_dim_end_time=end_time,
                    secondary_dim=secondary_statuses,
                )
            )

            i = j

        return ranges
