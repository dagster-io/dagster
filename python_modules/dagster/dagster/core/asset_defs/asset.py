from typing import Mapping, Optional, Tuple

from dagster.core.definitions import OpDefinition
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.partition import PartitionsDefinition

from .partition_mapping import PartitionMapping


class AssetsDefinition:
    def __init__(
        self,
        input_names_by_asset_key: Mapping[AssetKey, str],
        output_names_by_asset_key: Mapping[AssetKey, str],
        op: OpDefinition,
        partitions_defs_by_asset_key: Optional[Mapping[AssetKey, PartitionsDefinition]] = None,
        partition_mappings: Optional[Mapping[Tuple[AssetKey, AssetKey], PartitionMapping]] = None,
    ):
        self._op = op
        self._input_defs_by_asset_key = {
            asset_key: op.input_dict[input_name]
            for asset_key, input_name in input_names_by_asset_key.items()
        }

        self._output_defs_by_asset_key = {
            asset_key: op.output_dict[output_name]
            for asset_key, output_name in output_names_by_asset_key.items()
        }
        self._partitions_defs_by_asset_key = partitions_defs_by_asset_key or {}
        self._partition_mappings = partition_mappings or {}

    @property
    def op(self) -> OpDefinition:
        return self._op

    @property
    def output_defs_by_asset_key(self):
        return self._output_defs_by_asset_key

    @property
    def input_defs_by_asset_key(self):
        return self._input_defs_by_asset_key

    def get_partitions_def_for_asset_key(self, asset_key: AssetKey) -> PartitionsDefinition:
        return self._partitions_defs_by_asset_key[asset_key]

    def get_partition_mapping(
        self, out_asset_key: AssetKey, in_asset_key: AssetKey
    ) -> PartitionMapping:
        return self._partition_mappings.get(
            (out_asset_key, in_asset_key),
            self.get_partitions_def_for_asset_key(out_asset_key).get_default_partition_mapping(),
        )
