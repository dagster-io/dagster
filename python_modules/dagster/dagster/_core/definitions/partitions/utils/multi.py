from typing import TYPE_CHECKING, Optional, cast

import dagster._check as check

if TYPE_CHECKING:
    from dagster._core.definitions.partitions.definition.base import PartitionsDefinition
    from dagster._core.definitions.partitions.definition.time_window import (
        TimeWindowPartitionsDefinition,
    )


def has_one_dimension_time_window_partitioning(
    partitions_def: Optional["PartitionsDefinition"],
) -> bool:
    from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
    from dagster._core.definitions.partitions.definition.time_window import (
        TimeWindowPartitionsDefinition,
    )

    if isinstance(partitions_def, TimeWindowPartitionsDefinition):
        return True
    elif isinstance(partitions_def, MultiPartitionsDefinition):
        time_window_dims = [
            dim
            for dim in partitions_def.partitions_defs
            if isinstance(dim.partitions_def, TimeWindowPartitionsDefinition)
        ]
        if len(time_window_dims) == 1:
            return True

    return False


def get_time_partitions_def(
    partitions_def: Optional["PartitionsDefinition"],
) -> Optional["TimeWindowPartitionsDefinition"]:
    """For a given PartitionsDefinition, return the associated TimeWindowPartitionsDefinition if it
    exists.
    """
    from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
    from dagster._core.definitions.partitions.definition.time_window import (
        TimeWindowPartitionsDefinition,
    )

    if partitions_def is None:
        return None
    elif isinstance(partitions_def, TimeWindowPartitionsDefinition):
        return partitions_def
    elif isinstance(
        partitions_def, MultiPartitionsDefinition
    ) and has_one_dimension_time_window_partitioning(partitions_def):
        return cast(
            "TimeWindowPartitionsDefinition", partitions_def.time_window_dimension.partitions_def
        )
    else:
        return None


def get_time_partition_key(
    partitions_def: Optional["PartitionsDefinition"], partition_key: Optional[str]
) -> str:
    from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
    from dagster._core.definitions.partitions.definition.time_window import (
        TimeWindowPartitionsDefinition,
    )

    if partitions_def is None or partition_key is None:
        check.failed(
            "Cannot get time partitions key from when partitions def is None or partition key is"
            " None"
        )
    elif isinstance(partitions_def, TimeWindowPartitionsDefinition):
        return partition_key
    elif isinstance(partitions_def, MultiPartitionsDefinition):
        return partitions_def.get_partition_key_from_str(partition_key).keys_by_dimension[
            partitions_def.time_window_dimension.name
        ]
    else:
        check.failed(f"Cannot get time partition from non-time partitions def {partitions_def}")
