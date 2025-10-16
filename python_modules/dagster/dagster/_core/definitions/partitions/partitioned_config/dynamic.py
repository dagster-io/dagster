from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Callable, Optional

import dagster._check as check
from dagster._annotations import deprecated_param, public
from dagster._core.definitions.partitions.definition.dynamic import DynamicPartitionsDefinition
from dagster._core.definitions.partitions.partitioned_config.partitioned_config import (
    PartitionConfigFn,
    PartitionedConfig,
)
from dagster._utils.warnings import normalize_renamed_param


@deprecated_param(
    param="tags_for_partition_fn",
    breaking_version="2.0",
    additional_warn_text="Use tags_for_partition_key_fn instead.",
)
@public
def dynamic_partitioned_config(
    partition_fn: Callable[[Optional[datetime]], Sequence[str]],
    tags_for_partition_fn: Optional[Callable[[str], Mapping[str, str]]] = None,
    tags_for_partition_key_fn: Optional[Callable[[str], Mapping[str, str]]] = None,
) -> Callable[[PartitionConfigFn], PartitionedConfig]:
    """Creates a dynamic partitioned config for a job.

    The provided partition_fn returns a list of strings identifying the set of partitions, given
    an optional datetime argument (representing the current time).  The list of partitions returned
    may change over time.

    The decorated function takes in a partition key and returns a valid run config for a particular
    target job.

    Args:
        partition_fn (Callable[[datetime.datetime], Sequence[str]]): A function that generates a
            list of valid partition keys, which serve as the range of values that can be provided
            to the decorated run config function.
        tags_for_partition_fn (Optional[Callable[[str], Mapping[str, str]]]): A function that
            accepts a partition key and returns a dictionary of tags to attach to runs for that
            partition.

    Returns:
        PartitionedConfig
    """
    check.callable_param(partition_fn, "partition_fn")

    tags_for_partition_key_fn = normalize_renamed_param(
        tags_for_partition_key_fn,
        "tags_for_partition_key_fn",
        tags_for_partition_fn,
        "tags_for_partition_fn",
    )

    def inner(fn: PartitionConfigFn) -> PartitionedConfig:
        return PartitionedConfig(
            partitions_def=DynamicPartitionsDefinition(partition_fn),
            run_config_for_partition_key_fn=fn,
            decorated_fn=fn,
            tags_for_partition_key_fn=tags_for_partition_key_fn,
        )

    return inner
