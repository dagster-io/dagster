from collections.abc import Mapping, Sequence
from typing import Callable, Optional

import dagster._check as check
from dagster._annotations import deprecated_param, public
from dagster._core.definitions.partitions.definition.static import StaticPartitionsDefinition
from dagster._core.definitions.partitions.partitioned_config import (
    PartitionConfigFn,
    PartitionedConfig,
)
from dagster._utils.warnings import normalize_renamed_param


@public
@deprecated_param(
    param="tags_for_partition_fn",
    breaking_version="2.0",
    additional_warn_text="Use tags_for_partition_key_fn instead.",
)
def static_partitioned_config(
    partition_keys: Sequence[str],
    tags_for_partition_fn: Optional[Callable[[str], Mapping[str, str]]] = None,
    tags_for_partition_key_fn: Optional[Callable[[str], Mapping[str, str]]] = None,
) -> Callable[[PartitionConfigFn], PartitionedConfig[StaticPartitionsDefinition]]:
    """Creates a static partitioned config for a job.

    The provided partition_keys is a static list of strings identifying the set of partitions. The
    list of partitions is static, so while the run config returned by the decorated function may
    change over time, the list of valid partition keys does not.

    This has performance advantages over `dynamic_partitioned_config` in terms of loading different
    partition views in the Dagster UI.

    The decorated function takes in a partition key and returns a valid run config for a particular
    target job.

    Args:
        partition_keys (Sequence[str]): A list of valid partition keys, which serve as the range of
            values that can be provided to the decorated run config function.
        tags_for_partition_fn (Optional[Callable[[str], Mapping[str, str]]]): A function that
            accepts a partition key and returns a dictionary of tags to attach to runs for that
            partition.
        tags_for_partition_key_fn (Optional[Callable[[str], Mapping[str, str]]]): A function that
            accepts a partition key and returns a dictionary of tags to attach to runs for that
            partition.

    Returns:
        PartitionedConfig
    """
    check.sequence_param(partition_keys, "partition_keys", str)

    tags_for_partition_key_fn = normalize_renamed_param(
        tags_for_partition_key_fn,
        "tags_for_partition_key_fn",
        tags_for_partition_fn,
        "tags_for_partition_fn",
    )

    def inner(
        fn: PartitionConfigFn,
    ) -> PartitionedConfig[StaticPartitionsDefinition]:
        return PartitionedConfig(
            partitions_def=StaticPartitionsDefinition(partition_keys),
            run_config_for_partition_key_fn=fn,
            decorated_fn=fn,
            tags_for_partition_key_fn=tags_for_partition_key_fn,
        )

    return inner
