import warnings
from typing import AbstractSet, Iterable, Mapping, Optional, cast

from dagster import check
from dagster.core.definitions import NodeDefinition, OpDefinition
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.partition import PartitionsDefinition
from dagster.utils.backcompat import ExperimentalWarning

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
        # if adding new fields, make sure to handle them in the with_replaced_asset_keys method
    ):
        self._node_def = node_def
        self._asset_keys_by_input_name = check.dict_param(
            asset_keys_by_input_name,
            "asset_keys_by_input_name",
            key_type=str,
            value_type=AssetKey,
        )
        self._asset_keys_by_output_name = check.dict_param(
            asset_keys_by_output_name,
            "asset_keys_by_output_name",
            key_type=str,
            value_type=AssetKey,
        )

        self._partitions_def = partitions_def
        self._partition_mappings = partition_mappings or {}

        # if not specified assume all output assets depend on all input assets
        all_asset_keys = set(asset_keys_by_output_name.values())
        self._asset_deps = asset_deps or {
            out_asset_key: set(asset_keys_by_input_name.values())
            for out_asset_key in all_asset_keys
        }
        check.invariant(
            set(self._asset_deps.keys()) == all_asset_keys,
            "The set of asset keys with dependencies specified in the asset_deps argument must "
            "equal the set of asset keys produced by this AssetsDefinition. \n"
            f"asset_deps keys: {set(self._asset_deps.keys())} \n"
            f"expected keys: {all_asset_keys}",
        )

    def __call__(self, *args, **kwargs):
        return self._node_def(*args, **kwargs)

    @property
    def op(self) -> OpDefinition:
        check.invariant(
            isinstance(self._node_def, OpDefinition),
            "The NodeDefinition for this AssetsDefinition is not of type OpDefinition.",
        )
        return cast(OpDefinition, self._node_def)

    @property
    def node_def(self) -> NodeDefinition:
        return self._node_def

    @property
    def asset_deps(self) -> Mapping[AssetKey, AbstractSet[AssetKey]]:
        return self._asset_deps

    @property
    def asset_key(self) -> AssetKey:
        check.invariant(
            len(self._asset_keys_by_output_name) == 1,
            "Tried to retrieve asset key from an assets definition with multiple asset keys: "
            + ", ".join([str(ak.to_string()) for ak in self._asset_keys_by_output_name.values()]),
        )

        return next(iter(self._asset_keys_by_output_name.values()))

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

    @property
    def dependency_asset_keys(self) -> Iterable[AssetKey]:
        return self._asset_keys_by_input_name.values()

    def get_partition_mapping(self, in_asset_key: AssetKey) -> PartitionMapping:
        if self._partitions_def is None:
            check.failed("Asset is not partitioned")

        return self._partition_mappings.get(
            in_asset_key,
            self._partitions_def.get_default_partition_mapping(),
        )

    def with_replaced_asset_keys(
        self,
        output_asset_key_replacements: Mapping[AssetKey, AssetKey],
        input_asset_key_replacements: Mapping[AssetKey, AssetKey],
    ) -> "AssetsDefinition":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)

            return self.__class__(
                asset_keys_by_input_name={
                    input_name: input_asset_key_replacements.get(key, key)
                    for input_name, key in self.asset_keys_by_input_name.items()
                },
                asset_keys_by_output_name={
                    output_name: output_asset_key_replacements.get(key, key)
                    for output_name, key in self.asset_keys_by_output_name.items()
                },
                node_def=self.node_def,
                partitions_def=self.partitions_def,
                partition_mappings=self._partition_mappings,
            )
