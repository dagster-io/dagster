from typing import AbstractSet, Mapping, Optional

from dagster import check
from dagster.core.definitions import NodeDefinition, OpDefinition
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.partition import PartitionsDefinition

from .partition_mapping import PartitionMapping


class AssetsDefinition:
    def __init__(
        self,
        asset_keys_by_input_name: Mapping[AssetKey, str],
        asset_keys_by_output_name: Mapping[AssetKey, str],
        op: OpDefinition,
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_mappings: Optional[Mapping[AssetKey, PartitionMapping]] = None,
        asset_deps: Optional[Mapping[AssetKey, AbstractSet[AssetKey]]] = None,
    ):
        self._op = op
        self._asset_keys_by_input_name = asset_keys_by_input_name
        self._asset_keys_by_output_name = asset_keys_by_output_name

        self._partitions_def = partitions_def
        self._partition_mappings = partition_mappings or {}

        all_input_asset_keys = set(asset_keys_by_input_name.values())
        self._asset_deps = asset_deps or {
            output_key: all_input_asset_keys for output_key in asset_keys_by_output_name.values()
        }

    def __call__(self, *args, **kwargs):
        return self._op(*args, **kwargs)

    @property
    def op(self) -> OpDefinition:
        return self._op

    @property
    def node_def(self) -> NodeDefinition:
        return self._op

    @property
    def asset_deps(self) -> Mapping[AssetKey, AbstractSet[AssetKey]]:
        return self._asset_deps

    @property
    def asset_keys(self) -> AbstractSet[AssetKey]:
        return set(self.asset_keys_by_output_name.values())

    @property
    def asset_keys_by_output_name(self) -> Mapping[str, AssetKey]:
        return self._asset_keys_by_output_name

    @property
    def asset_keys_by_input_name(self) -> Mapping[str, AssetKey]:
        return self._asset_keys_by_input_name

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        return self._partitions_def

    def get_partition_mapping(self, in_asset_key: AssetKey) -> PartitionMapping:
        if self._partitions_def is None:
            check.failed("Asset is not partitioned")

        return self._partition_mappings.get(
            in_asset_key,
            self._partitions_def.get_default_partition_mapping(),
        )
