from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Generic, Optional, cast

from typing_extensions import TypeVar

from dagster._annotations import public
from dagster._core.definitions.partitions.context import (
    PartitionLoadingContext,
    partition_loading_context,
)
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partitions.utils.base import (
    generate_partition_key_based_definition_id,
)
from dagster._core.errors import DagsterInvalidInvocationError, DagsterUnknownPartitionError
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._core.types.pagination import PaginatedResults

if TYPE_CHECKING:
    from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset
    from dagster._core.instance import DynamicPartitionsStore


T_str = TypeVar("T_str", bound=str, default=str, covariant=True)


@public
class PartitionsDefinition(ABC, Generic[T_str]):
    """Defines a set of partitions, which can be attached to a software-defined asset or job.

    Abstract class with implementations for different kinds of partitions.
    """

    @property
    def partitions_subset_class(self) -> type["PartitionsSubset"]:
        from dagster._core.definitions.partitions.subset.default import DefaultPartitionsSubset

        return DefaultPartitionsSubset

    @abstractmethod
    @public
    def get_partition_keys(
        self,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> Sequence[T_str]:
        """Returns a list of strings representing the partition keys of the PartitionsDefinition.

        Args:
            current_time (Optional[datetime]): A datetime object representing the current time, only
                applicable to time-based partitions definitions.
            dynamic_partitions_store (Optional[DynamicPartitionsStore]): The DynamicPartitionsStore
                object that is responsible for fetching dynamic partitions. Required when the
                partitions definition is a DynamicPartitionsDefinition with a name defined. Users
                can pass the DagsterInstance fetched via `context.instance` to this argument.

        Returns:
            Sequence[str]
        """
        ...

    @abstractmethod
    def get_paginated_partition_keys(
        self,
        context: PartitionLoadingContext,
        limit: int,
        ascending: bool,
        cursor: Optional[str] = None,
    ) -> PaginatedResults[str]:
        """Returns a connection object that contains a list of partition keys and all the necessary
        information to paginate through them.

        Args:
            context (PartitionLoadingContext): The context for loading partition keys.
            limit (int): The maximum number of partition keys to return.
            ascending (bool): Whether to return the partition keys in ascending order.  The order is determined by the partitions definition.
            cursor (Optional[str]): A cursor to track the progress paginating through the returned partition key results.

        Returns:
            PaginatedResults[str]
        """
        ...

    def __str__(self) -> str:
        joined_keys = ", ".join([f"'{key}'" for key in self.get_partition_keys()])
        return joined_keys

    def get_last_partition_key(self) -> Optional[T_str]:
        partition_keys = self.get_partition_keys()
        return partition_keys[-1] if partition_keys else None

    def get_first_partition_key(self) -> Optional[T_str]:
        partition_keys = self.get_partition_keys()
        return partition_keys[0] if partition_keys else None

    def get_partition_keys_in_range(
        self, partition_key_range: PartitionKeyRange
    ) -> Sequence[T_str]:
        keys_exist = {
            partition_key_range.start: self.has_partition_key(partition_key_range.start),
            partition_key_range.end: self.has_partition_key(partition_key_range.end),
        }
        if not all(keys_exist.values()):
            raise DagsterInvalidInvocationError(
                f"""Partition range {partition_key_range.start} to {partition_key_range.end} is
                not a valid range. Nonexistent partition keys:
                {list(key for key in keys_exist if keys_exist[key] is False)}"""
            )

        # in the simple case, simply return the single key in the range
        if partition_key_range.start == partition_key_range.end:
            return [cast("T_str", partition_key_range.start)]

        # defer this call as it is potentially expensive
        partition_keys = self.get_partition_keys()
        return partition_keys[
            partition_keys.index(partition_key_range.start) : partition_keys.index(
                partition_key_range.end
            )
            + 1
        ]

    def empty_subset(self) -> "PartitionsSubset":
        return self.partitions_subset_class.create_empty_subset(self)

    def subset_with_partition_keys(self, partition_keys: Iterable[str]) -> "PartitionsSubset":
        return self.empty_subset().with_partition_keys(partition_keys)

    def subset_with_all_partitions(self) -> "PartitionsSubset":
        return self.subset_with_partition_keys(self.get_partition_keys())

    def deserialize_subset(self, serialized: str) -> "PartitionsSubset":
        return self.partitions_subset_class.from_serialized(self, serialized)

    def can_deserialize_subset(
        self,
        serialized: str,
        serialized_partitions_def_unique_id: Optional[str],
        serialized_partitions_def_class_name: Optional[str],
    ) -> bool:
        return self.partitions_subset_class.can_deserialize(
            self,
            serialized,
            serialized_partitions_def_unique_id,
            serialized_partitions_def_class_name,
        )

    def get_serializable_unique_identifier(self) -> str:
        return generate_partition_key_based_definition_id(self.get_partition_keys())

    def get_tags_for_partition_key(self, partition_key: str) -> Mapping[str, str]:
        tags = {PARTITION_NAME_TAG: partition_key}
        return tags

    def get_num_partitions(self) -> int:
        return len(self.get_partition_keys())

    def has_partition_key(self, partition_key: str) -> bool:
        return partition_key in self.get_partition_keys()

    def validate_partition_key(self, partition_key: str, context: PartitionLoadingContext) -> None:
        with partition_loading_context(new_ctx=context):
            if not self.has_partition_key(partition_key):
                raise DagsterUnknownPartitionError(
                    f"Could not find a partition with key `{partition_key}`."
                )
