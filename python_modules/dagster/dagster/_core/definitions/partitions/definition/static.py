from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.partitions.context import (
    PartitionLoadingContext,
    partition_loading_context,
)
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.utils.base import (
    raise_error_on_duplicate_partition_keys,
    raise_error_on_invalid_partition_key_substring,
)
from dagster._core.types.pagination import PaginatedResults

if TYPE_CHECKING:
    from dagster._core.instance import DynamicPartitionsStore


class StaticPartitionsDefinition(PartitionsDefinition[str]):
    """A statically-defined set of partitions.

    We recommended limiting partition counts for each asset to 100,000 partitions or fewer.

    Example:
        .. code-block:: python

            from dagster import StaticPartitionsDefinition, asset

            oceans_partitions_def = StaticPartitionsDefinition(
                ["arctic", "atlantic", "indian", "pacific", "southern"]
            )

            @asset(partitions_def=oceans_partitions_defs)
            def ml_model_for_each_ocean():
                ...
    """

    def __init__(self, partition_keys: Sequence[str]):
        # for back compat reasons we allow str as a Sequence[str] here
        if not isinstance(partition_keys, str):
            check.sequence_param(
                partition_keys,
                "partition_keys",
                of_type=str,
            )

        raise_error_on_invalid_partition_key_substring(partition_keys)
        raise_error_on_duplicate_partition_keys(partition_keys)

        self._partition_keys = partition_keys

    @public
    def get_partition_keys(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> Sequence[str]:
        """Returns a list of strings representing the partition keys of the PartitionsDefinition.

        Args:
            current_time (Optional[datetime]): A datetime object representing the current time, only
                applicable to time-based partitions definitions.
            dynamic_partitions_store (Optional[DynamicPartitionsStore]): The DynamicPartitionsStore
                object that is responsible for fetching dynamic partitions. Only applicable to
                DynamicPartitionsDefinitions.

        Returns:
            Sequence[str]

        """
        return self._partition_keys

    def get_paginated_partition_keys(
        self,
        context: PartitionLoadingContext,
        limit: int,
        ascending: bool,
        cursor: Optional[str] = None,
    ) -> PaginatedResults[str]:
        with partition_loading_context(new_ctx=context):
            partition_keys = self.get_partition_keys()
            return PaginatedResults.create_from_sequence(
                partition_keys, limit=limit, ascending=ascending, cursor=cursor
            )

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other) -> bool:
        return isinstance(other, StaticPartitionsDefinition) and (
            self is other or self._partition_keys == other.get_partition_keys()
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}(partition_keys={self._partition_keys})"

    def get_num_partitions(self) -> int:
        # We don't currently throw an error when a duplicate partition key is defined
        # in a static partitions definition, though we will at 1.3.0.
        # This ensures that partition counts are correct in the Dagster UI.
        return len(set(self.get_partition_keys()))
