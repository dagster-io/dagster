from typing import Mapping, Optional

from dagster import check
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
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_mappings: Optional[Mapping[AssetKey, PartitionMapping]] = None,
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
        self._partitions_def = partitions_def
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
