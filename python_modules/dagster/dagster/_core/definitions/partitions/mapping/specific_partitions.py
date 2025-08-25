from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple, Optional

from dagster._annotations import PublicAttr
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.mapping.partition_mapping import (
    PartitionMapping,
    UpstreamPartitionsResult,
)
from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset
from dagster._serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.instance import DynamicPartitionsStore


@whitelist_for_serdes
class SpecificPartitionsPartitionMapping(
    PartitionMapping,
    NamedTuple(
        "_SpecificPartitionsPartitionMapping", [("partition_keys", PublicAttr[Sequence[str]])]
    ),
):
    """Maps to a specific subset of partitions in the upstream asset.

    Example:
        .. code-block:: python

            from dagster import SpecificPartitionsPartitionMapping, StaticPartitionsDefinition, asset

            @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c"]))
            def upstream():
                ...

            @asset(
                ins={
                    "upstream": AssetIn(partition_mapping=SpecificPartitionsPartitionMapping(["a"]))
                }
            )
            def a_downstream(upstream):
                ...
    """

    def validate_partition_mapping(
        self,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: Optional[PartitionsDefinition],
    ):
        pass

    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> UpstreamPartitionsResult:
        with partition_loading_context(current_time, dynamic_partitions_store):
            return UpstreamPartitionsResult(
                partitions_subset=upstream_partitions_def.subset_with_partition_keys(
                    self.partition_keys
                ),
                required_but_nonexistent_subset=upstream_partitions_def.empty_subset(),
            )

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> PartitionsSubset:
        with partition_loading_context(current_time, dynamic_partitions_store):
            # if any of the partition keys in this partition mapping are contained within the upstream
            # partitions subset, then all partitions of the downstream asset are dependencies
            if any(key in upstream_partitions_subset for key in self.partition_keys):
                return downstream_partitions_def.subset_with_all_partitions()
            return downstream_partitions_def.empty_subset()

    @property
    def description(self) -> str:
        return f"Each downstream partition depends on the following upstream partitions: {self.partition_keys}"
