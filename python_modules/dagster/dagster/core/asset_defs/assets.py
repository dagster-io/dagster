from typing import AbstractSet, Mapping, Optional, Tuple

from dagster import check
from dagster.core.definitions import InputDefinition, NodeDefinition, OpDefinition, OutputDefinition
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.partition import PartitionsDefinition

from .partition_mapping import PartitionMapping


class AssetsDefinition:
    def __init__(
        self,
        asset_keys_by_input_name: Mapping[str, AssetKey],
        asset_keys_by_output_name: Mapping[str, AssetKey],
        node_def: NodeDefinition,
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_mappings: Optional[Mapping[AssetKey, PartitionMapping]] = None,
        asset_deps: Optional[Mapping[AssetKey, AbstractSet[AssetKey]]] = None,
    ):
        self._node_def = node_def
        self._asset_keys_by_input_def = {
            node_def.input_dict[input_name]: asset_key
            for input_name, asset_key in asset_keys_by_input_name.items()
        }

        self._asset_keys_by_output_def = {
            node_def.output_dict[output_name]: asset_key
            for output_name, asset_key in asset_keys_by_output_name.items()
        }
        self._partitions_def = partitions_def
        self._partition_mappings = partition_mappings or {}

        # if not specified assume all output assets depend on all input assets
        self._asset_deps = asset_deps or {
            out_asset_key: self.input_asset_keys for out_asset_key in self.asset_keys
        }

        # ensure that the specified asset_deps make sense
        valid_asset_deps = self.asset_keys | self.input_asset_keys
        for asset_key, dep_asset_keys in self._asset_deps.items():
            invalid_asset_deps = dep_asset_keys.difference(valid_asset_deps)
            check.invariant(
                not invalid_asset_deps,
                f"Invalid asset dependencies: {invalid_asset_deps} specified in `asset_deps` "
                f"argument for AssetsDefinition '{self.node_def.name}' on key '{asset_key}'. "
                "Each specified asset key must be associated with an input to the asset or "
                f"produced by this asset. Valid keys: {valid_asset_deps}",
            )
        check.invariant(
            set(self._asset_deps.keys()) == self.asset_keys,
            "The set of asset keys with dependencies specified in the asset_deps argument must "
            "equal the set of asset keys produced by this AssetsDefinition. \n"
            f"asset_deps keys: {set(self._asset_deps.keys())} \n"
            f"expected keys: {self.asset_keys}",
        )

    def __call__(self, *args, **kwargs):
        return self._node_def(*args, **kwargs)

    @property
    def op(self) -> OpDefinition:
        check.invariant(
            isinstance(self._node_def, OpDefinition),
            "The NodeDefinition for this AssetsDefinition is not of type OpDefinition.",
        )
        return self._node_def

    @property
    def node_def(self) -> NodeDefinition:
        return self._node_def

    @property
    def input_asset_keys(self) -> AbstractSet[AssetKey]:
        return set(self._asset_keys_by_input_def.values())

    @property
    def asset_keys(self) -> AbstractSet[AssetKey]:
        return set(self._asset_keys_by_output_def.values())

    @property
    def asset_deps(self) -> Mapping[AssetKey, AbstractSet[AssetKey]]:
        return self._asset_deps

    @property
    def asset_keys_by_output_def(self) -> Mapping[OutputDefinition, AssetKey]:
        return self._asset_keys_by_output_def

    @property
    def asset_keys_by_input_def(self) -> Mapping[InputDefinition, AssetKey]:
        return self._asset_keys_by_input_def

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
