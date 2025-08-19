from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple, Optional

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.mapping.partition_mapping import (
    PartitionMapping,
    UpstreamPartitionsResult,
)
from dagster._core.definitions.partitions.subset.default import DefaultPartitionsSubset
from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.instance import DynamicPartitionsStore


@whitelist_for_serdes
@public
class IdentityPartitionMapping(PartitionMapping, NamedTuple("_IdentityPartitionMapping", [])):
    """Expects that the upstream and downstream assets are partitioned in the same way, and maps
    partitions in the downstream asset to the same partition in the upstream asset.
    """

    def validate_partition_mapping(
        self,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: Optional[PartitionsDefinition],
    ):
        if type(upstream_partitions_def) != type(downstream_partitions_def):
            raise DagsterInvalidDefinitionError(
                "Upstream and downstream partitions definitions must match, or a different partition mapping must be provided. "
                f"Got upstream definition {type(upstream_partitions_def)} and downstream definition {type(downstream_partitions_def)}",
            )

    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: Optional[PartitionsSubset],
        downstream_partitions_def: Optional[PartitionsDefinition],
        upstream_partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> UpstreamPartitionsResult:
        with partition_loading_context(current_time, dynamic_partitions_store):
            if downstream_partitions_subset is None:
                check.failed("downstream asset is not partitioned")

            if downstream_partitions_def == upstream_partitions_def:
                return UpstreamPartitionsResult(
                    partitions_subset=downstream_partitions_subset,
                    required_but_nonexistent_subset=upstream_partitions_def.empty_subset(),
                )

            # must list out the keys before combining them since they might be from
            # different asset keys
            upstream_partition_keys = set(upstream_partitions_def.get_partition_keys())
            downstream_partition_keys = set(downstream_partitions_subset.get_partition_keys())

            return UpstreamPartitionsResult(
                partitions_subset=upstream_partitions_def.subset_with_partition_keys(
                    list(upstream_partition_keys & downstream_partition_keys)
                ),
                required_but_nonexistent_subset=DefaultPartitionsSubset(
                    downstream_partition_keys - upstream_partition_keys,
                ),
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

            if upstream_partitions_def == downstream_partitions_def:
                return upstream_partitions_subset

            upstream_partition_keys = set(upstream_partitions_subset.get_partition_keys())
            downstream_partition_keys = set(downstream_partitions_def.get_partition_keys())

            return downstream_partitions_def.empty_subset().with_partition_keys(
                list(downstream_partition_keys & upstream_partition_keys)
            )

    @property
    def description(self) -> str:
        return (
            "Assumes upstream and downstream assets share the same partitions definition. "
            "Maps each partition in the downstream asset to the same partition in the upstream asset."
        )
