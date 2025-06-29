import warnings
from functools import lru_cache
from typing import TYPE_CHECKING, Optional

from dagster._utils.warnings import disable_dagster_warnings

if TYPE_CHECKING:
    from dagster._core.definitions.partitions.definition import PartitionsDefinition
    from dagster._core.definitions.partitions.mapping import PartitionMapping


def infer_partition_mapping(
    partition_mapping: Optional["PartitionMapping"],
    downstream_partitions_def: Optional["PartitionsDefinition"],
    upstream_partitions_def: Optional["PartitionsDefinition"],
) -> "PartitionMapping":
    from dagster._core.definitions.partitions.definition import TimeWindowPartitionsDefinition
    from dagster._core.definitions.partitions.mapping import (
        AllPartitionMapping,
        IdentityPartitionMapping,
        TimeWindowPartitionMapping,
    )
    from dagster._core.definitions.partitions.mapping.multi.multi_to_single import (
        MultiToSingleDimensionPartitionMapping,
        get_infer_single_to_multi_dimension_deps_result,
    )

    if partition_mapping is not None:
        return partition_mapping
    elif upstream_partitions_def and downstream_partitions_def:
        if get_infer_single_to_multi_dimension_deps_result(
            upstream_partitions_def, downstream_partitions_def
        ).can_infer:
            with disable_dagster_warnings():
                return MultiToSingleDimensionPartitionMapping()
        elif isinstance(upstream_partitions_def, TimeWindowPartitionsDefinition) and isinstance(
            downstream_partitions_def, TimeWindowPartitionsDefinition
        ):
            return TimeWindowPartitionMapping()
        else:
            return IdentityPartitionMapping()
    else:
        return AllPartitionMapping()


@lru_cache(maxsize=1)
def get_builtin_partition_mapping_types() -> tuple[type["PartitionMapping"], ...]:
    from dagster._core.definitions.partitions.mapping import (
        AllPartitionMapping,
        IdentityPartitionMapping,
        LastPartitionMapping,
        MultiPartitionMapping,
        MultiToSingleDimensionPartitionMapping,
        SpecificPartitionsPartitionMapping,
        StaticPartitionMapping,
        TimeWindowPartitionMapping,
    )

    return (
        AllPartitionMapping,
        IdentityPartitionMapping,
        LastPartitionMapping,
        SpecificPartitionsPartitionMapping,
        StaticPartitionMapping,
        TimeWindowPartitionMapping,
        MultiToSingleDimensionPartitionMapping,
        MultiPartitionMapping,
    )


def warn_if_partition_mapping_not_builtin(partition_mapping: "PartitionMapping") -> None:
    builtin_partition_mappings = get_builtin_partition_mapping_types()
    if not isinstance(partition_mapping, builtin_partition_mappings):
        warnings.warn(
            f"Non-built-in PartitionMappings, such as {type(partition_mapping).__name__} "
            "are deprecated and will not work with asset reconciliation. The built-in "
            "partition mappings are "
            + ", ".join(
                builtin_partition_mapping.__name__
                for builtin_partition_mapping in builtin_partition_mappings
            )
            + ".",
            category=DeprecationWarning,
        )
