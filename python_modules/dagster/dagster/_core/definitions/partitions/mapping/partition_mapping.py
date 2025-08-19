from abc import ABC, abstractmethod, abstractproperty
from collections.abc import Sequence
from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING, Optional

from dagster._annotations import public
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset
from dagster._record import record

if TYPE_CHECKING:
    from dagster._core.instance import DynamicPartitionsStore


@record
class UpstreamPartitionsResult:
    """Represents the result of mapping a PartitionsSubset to the corresponding
    partitions in another PartitionsDefinition.

    partitions_subset (PartitionsSubset): The resulting partitions subset that was
        mapped to. Only contains partitions for existent partitions, filtering out nonexistent partitions.
    required_but_nonexistent_subset (PartitionsSubset): A set of invalid partition keys in to_partitions_def
        that partitions in from_partitions_subset were mapped to.
    """

    partitions_subset: PartitionsSubset
    required_but_nonexistent_subset: PartitionsSubset

    @cached_property
    def required_but_nonexistent_partition_keys(self) -> Sequence[str]:
        return list(self.required_but_nonexistent_subset.get_partition_keys())


@public
class PartitionMapping(ABC):
    """Defines a correspondence between the partitions in an asset and the partitions in an asset
    that it depends on.

    Overriding PartitionMapping outside of Dagster is not supported. The abstract methods of this
    class may change at any time.
    """

    @public
    @abstractmethod
    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> PartitionsSubset:
        """Returns the subset of partition keys in the downstream asset that use the data in the given
        partition key subset of the upstream asset.

        Args:
            upstream_partitions_subset (Union[PartitionKeyRange, PartitionsSubset]): The
                subset of partition keys in the upstream asset.
            downstream_partitions_def (PartitionsDefinition): The partitions definition for the
                downstream asset.
        """

    @abstractmethod
    def validate_partition_mapping(
        self,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: Optional[PartitionsDefinition],
    ) -> None:
        """Raises an exception if the mapping is not valid for the two partitions definitions
        due to some incompatibility between the definitions (ignoring specific keys or subsets).
        For example, a StaticPartitionMapping is invalid if both mapped partitions definitions
        are not StaticPartitionsDefinitions.
        """

    @public
    @abstractmethod
    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> UpstreamPartitionsResult:
        """Returns a UpstreamPartitionsResult object containing the partition keys the downstream
        partitions subset was mapped to in the upstream partitions definition.

        Valid upstream partitions will be included in UpstreamPartitionsResult.partitions_subset.
        Invalid upstream partitions will be included in UpstreamPartitionsResult.required_but_nonexistent_subset.

        For example, if an upstream asset is time-partitioned and starts in June 2023, and the
        downstream asset is time-partitioned and starts in May 2023, this function would return a
        UpstreamPartitionsResult(PartitionsSubset("2023-06-01"), required_but_nonexistent_subset=PartitionsSubset("2023-05-01"))
        when downstream_partitions_subset contains 2023-05-01 and 2023-06-01.
        """

    @abstractproperty
    def description(self) -> str:
        """A human-readable description of the partition mapping, displayed in the Dagster UI."""
        raise NotImplementedError()
