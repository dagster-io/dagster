from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple, Optional

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.mapping.partition_mapping import (
    PartitionMapping,
    UpstreamPartitionsResult,
)
from dagster._core.definitions.partitions.subset.all import AllPartitionsSubset
from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset
from dagster._serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.instance import DynamicPartitionsStore


@whitelist_for_serdes
@public
class AllPartitionMapping(PartitionMapping, NamedTuple("_AllPartitionMapping", [])):
    """Maps every partition in the downstream asset to every partition in the upstream asset.

    Commonly used in the case when the downstream asset is not partitioned, in which the entire
    downstream asset depends on all partitions of the upstream asset.
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
        with partition_loading_context(current_time, dynamic_partitions_store) as ctx:
            if ctx.dynamic_partitions_store is not None and ctx.effective_dt is not None:
                partitions_subset = AllPartitionsSubset(
                    partitions_def=upstream_partitions_def, context=ctx
                )
            else:
                partitions_subset = upstream_partitions_def.subset_with_all_partitions()
            return UpstreamPartitionsResult(
                partitions_subset=partitions_subset,
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
            if upstream_partitions_subset is None:
                check.failed("upstream asset is not partitioned")

            if len(upstream_partitions_subset) == 0:
                return downstream_partitions_def.empty_subset()

            return downstream_partitions_def.subset_with_all_partitions()

    @property
    def description(self) -> str:
        return "Each downstream partition depends on all partitions of the upstream asset."
