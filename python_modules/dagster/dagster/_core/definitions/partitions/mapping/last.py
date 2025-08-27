from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple, Optional

from dagster._annotations import public
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
@public
class LastPartitionMapping(PartitionMapping, NamedTuple("_LastPartitionMapping", [])):
    """Maps all dependencies to the last partition in the upstream asset.

    Commonly used in the case when the downstream asset is not partitioned, in which the entire
    downstream asset depends on the last partition of the upstream asset.
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
            last = upstream_partitions_def.get_last_partition_key()

            upstream_subset = upstream_partitions_def.empty_subset()
            if last is not None:
                upstream_subset = upstream_subset.with_partition_keys([last])

            return UpstreamPartitionsResult(
                partitions_subset=upstream_subset,
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
            last_upstream_partition = upstream_partitions_def.get_last_partition_key()
            if last_upstream_partition and last_upstream_partition in upstream_partitions_subset:
                return downstream_partitions_def.subset_with_all_partitions()
            else:
                return downstream_partitions_def.empty_subset()

    @property
    def description(self) -> str:
        return "Each downstream partition depends on the last partition of the upstream asset."
