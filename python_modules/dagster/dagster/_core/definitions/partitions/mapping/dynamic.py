from collections.abc import Sequence
from datetime import datetime
from typing import NamedTuple

import dagster._check as check
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition import MultiPartitionsDefinition, PartitionsDefinition
from dagster._core.definitions.partitions.mapping import PartitionMapping, UpstreamPartitionsResult
from dagster._core.definitions.partitions.subset.default import DefaultPartitionsSubset
from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset
from dagster._core.definitions.partitions.utils.multi import MultiPartitionKey
from dagster._core.instance import DynamicPartitionsStore
from dagster._serdes import whitelist_for_serdes


DYNAMIC_MAPPING_SPLIT = ","


@whitelist_for_serdes
class DynamicPartitionMapping(
    PartitionMapping,
    NamedTuple("_DynamicPartitionMapping", [("dynamic_mapping_partition_name", str)]),
):
    """Map upstream to downstream partitions dynamically based on a dynamic partition mapping.

    To use this mapping, define a dynamic partitions definition, and add mapping in the format:
    ["<downstream>,<upstream>"]
    E.g.: '["A,A", "A,B"]'

    As with regular dynamic partitions, the mapping ones would typically be created/removed in a sensor.

    ```py
    asset_map = dg.DynamiPartitionsDefinition(name="asset_map")
    asset_mapping = DynamicPartitionMapping(asset_map.name)

    @dg.sensor()
    def asset_mapping_sensor():
        # Build dynamic partition requests with the expected mapping format

    @dg.asset(
        ins={"upstream_asset": dg.AssetIn(key="upstream_asset", partition_mapping=asset_mapping)}
    )
    def downstream_asset(upstream_asset: dict[str, Any]):
        # Use the upstream_asset data with the right partitions loaded
    ```
    """

    @staticmethod
    def _massage_map_key(
        map_key: str,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: PartitionsDefinition,
    ) -> tuple[str | MultiPartitionKey, str | MultiPartitionKey]:
        if len(map_key.split(DYNAMIC_MAPPING_SPLIT)) != 2:
            check.failed(f"Invalid mapping key: {map_key}")
        downstream, upstream = map_key.split(DYNAMIC_MAPPING_SPLIT)
        if isinstance(downstream_partitions_def, MultiPartitionsDefinition):
            downstream = MultiPartitionKey(
                dict(zip(downstream_partitions_def.partition_dimension_names, downstream.split("|"), strict=True))
            )
        if isinstance(upstream_partitions_def, MultiPartitionsDefinition):
            upstream = MultiPartitionKey(
                dict(zip(upstream_partitions_def.partition_dimension_names, upstream.split("|"), strict=True))
            )
        return downstream, upstream

    def get_upstream_mapped_partitions_result_for_partitions(
        self,
        downstream_partitions_subset: PartitionsSubset | None,
        downstream_partitions_def: PartitionsDefinition | None,
        upstream_partitions_def: PartitionsDefinition,
        current_time: datetime | None = None,
        dynamic_partitions_store: DynamicPartitionsStore | None = None,
    ) -> UpstreamPartitionsResult | None:
        """Get the upstream partitions for the downstream partitions."""
        if downstream_partitions_def is None:
            check.failed("downstream asset is not partitioned")
            return
        if upstream_partitions_def is None:
            check.failed("upstream asset is not partitioned")
            return
        if downstream_partitions_subset is None:
            check.failed("downstream has no partition subset")
            return

        with partition_loading_context(current_time, dynamic_partitions_store) as ctx:
            if ctx.dynamic_partitions_store is None:
                check.failed("dynamic_partitions_store is None")

            downstream_keys = list(downstream_partitions_subset.get_partition_keys())

            dynamic_mapping = [
                self._massage_map_key(key, upstream_partitions_def, downstream_partitions_def)
                for key in ctx.dynamic_partitions_store.get_dynamic_partitions(self.dynamic_mapping_partition_name)
            ]

            all_expected: set[str] = set()
            for downstream_key in downstream_keys:
                expected_upstream: Sequence[str] = [
                    upstream for downstream, upstream in dynamic_mapping if downstream == downstream_key
                ]
                if not isinstance(expected_upstream, Sequence) or isinstance(expected_upstream, str):
                    check.failed(f"expected_upstream is not a sequence: {expected_upstream}")
                    return

                all_expected |= set(expected_upstream)

            upstream_partition_keys = set(
                upstream_partitions_def.get_partition_keys(dynamic_partitions_store=ctx.dynamic_partitions_store)
            )

            return UpstreamPartitionsResult(
                partitions_subset=upstream_partitions_def.subset_with_partition_keys(
                    upstream_partition_keys & all_expected
                ),
                required_but_nonexistent_subset=DefaultPartitionsSubset(all_expected - upstream_partition_keys),
            )

    def get_downstream_partitions_for_partitions(
        self,
        upstream_partitions_subset: PartitionsSubset,
        upstream_partitions_def: PartitionsDefinition,
        downstream_partitions_def: PartitionsDefinition,
        current_time: datetime | None = None,
        dynamic_partitions_store: DynamicPartitionsStore | None = None,
    ) -> PartitionsSubset | None:
        """Get the downstream partitions for the upstream partitions."""
        if downstream_partitions_def is None:
            check.failed("downstream asset is not partitioned")
            return
        if upstream_partitions_def is None:
            check.failed("upstream asset is not partitioned")
            return

        with partition_loading_context(current_time, dynamic_partitions_store) as ctx:
            if ctx.dynamic_partitions_store is None:
                check.failed("dynamic_partitions_store is None")
                return

            dynamic_mapping = [
                self._massage_map_key(key, upstream_partitions_def, downstream_partitions_def)
                for key in ctx.dynamic_partitions_store.get_dynamic_partitions(self.dynamic_mapping_partition_name)
            ]

            upstream_partition_keys = set(upstream_partitions_subset.get_partition_keys())
            expected_downstream = {
                downstream for downstream, upstream in dynamic_mapping if upstream in upstream_partition_keys
            }

            downstream_partition_keys = set(
                downstream_partitions_def.get_partition_keys(dynamic_partitions_store=ctx.dynamic_partitions_store)
            )
            return downstream_partitions_def.empty_subset().with_partition_keys(
                list(downstream_partition_keys & expected_downstream)
            )

    @property
    def description(self) -> str:
        """Get the description of the partition mapping."""
        return "Dynamic mapping of partitions based user-input functions."
