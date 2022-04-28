from typing import AbstractSet, Dict, Mapping, Optional, Set, cast

from dagster import check
from dagster.core.definitions import GraphDefinition, NodeDefinition, OpDefinition
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.partition import PartitionsDefinition
from dagster.core.errors import DagsterInvalidDefinitionError

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

    @staticmethod
    def from_graph(
        graph_def: GraphDefinition,
        asset_keys_by_input_name: Optional[Mapping[str, AssetKey]] = None,
        asset_keys_by_output_name: Optional[Mapping[str, AssetKey]] = None,
        internal_asset_deps: Optional[Mapping[str, Set[AssetKey]]] = None,
    ):
        asset_keys_by_input_name = check.opt_dict_param(
            asset_keys_by_input_name, "asset_keys_by_input_name", key_type=str, value_type=AssetKey
        )
        asset_keys_by_output_name = check.opt_dict_param(
            asset_keys_by_output_name,
            "asset_keys_by_output_name",
            key_type=str,
            value_type=AssetKey,
        )
        internal_asset_deps = check.opt_dict_param(
            internal_asset_deps, "internal_asset_deps", key_type=str, value_type=set
        )

        transformed_internal_asset_deps = {}
        if internal_asset_deps:
            for output_name, asset_keys in internal_asset_deps.items():
                check.invariant(
                    output_name in asset_keys_by_output_name,
                    f"output_name {output_name} specified in internal_asset_deps does not exist in the decorated function",
                )
                transformed_internal_asset_deps[asset_keys_by_output_name[output_name]] = asset_keys

        return AssetsDefinition(
            asset_keys_by_input_name=_infer_asset_keys_by_input_names(
                graph_def,
                asset_keys_by_input_name or {},
            ),
            asset_keys_by_output_name=_infer_asset_keys_by_output_names(
                graph_def, asset_keys_by_output_name or {}
            ),
            node_def=graph_def,
            asset_deps=transformed_internal_asset_deps or None,
        )

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


def _infer_asset_keys_by_input_names(
    graph_def: GraphDefinition, asset_keys_by_input_name: Mapping[str, AssetKey]
) -> Mapping[str, AssetKey]:
    all_input_names = {graph_input.definition.name for graph_input in graph_def.input_mappings}

    if asset_keys_by_input_name:
        check.invariant(
            set(asset_keys_by_input_name.keys()) == all_input_names,
            "The set of input names keys specified in the asset_keys_by_input_name argument must "
            "equal the set of asset keys inputted by this GraphDefinition. \n"
            f"asset_keys_by_input_name keys: {set(asset_keys_by_input_name.keys())} \n"
            f"expected keys: {all_input_names}",
        )

    # If asset key is not supplied in asset_keys_by_input_name, create asset key
    # from input name
    inferred_input_names_by_asset_key: Dict[str, AssetKey] = {
        input_name: asset_keys_by_input_name.get(input_name, AssetKey([input_name]))
        for input_name in all_input_names
    }

    return inferred_input_names_by_asset_key


def _infer_asset_keys_by_output_names(
    graph_def: GraphDefinition, asset_keys_by_output_name: Mapping[str, AssetKey]
) -> Mapping[str, AssetKey]:
    output_names = set([output_def.name for output_def in graph_def.output_defs])
    if asset_keys_by_output_name:
        check.invariant(
            set(asset_keys_by_output_name.keys()) == output_names,
            "The set of output names keys specified in the asset_keys_by_output_name argument must "
            "equal the set of asset keys outputted by this GraphDefinition. \n"
            f"asset_keys_by_input_name keys: {set(asset_keys_by_output_name.keys())} \n"
            f"expected keys: {output_names}",
        )

    inferred_asset_keys_by_output_names: Dict[str, AssetKey] = {
        output_name: asset_key for output_name, asset_key in asset_keys_by_output_name.items()
    }

    output_names = list(output_names)
    if (
        len(output_names) == 1
        and output_names[0] not in asset_keys_by_output_name
        and output_names[0] == "result"
    ):
        # If there is only one output and the name is the default "result", generate asset key
        # from the name of the node
        inferred_asset_keys_by_output_names[output_names[0]] = AssetKey([graph_def.name])

    for output_name in output_names:
        if output_name not in inferred_asset_keys_by_output_names:
            inferred_asset_keys_by_output_names[output_name] = AssetKey([output_name])
    return inferred_asset_keys_by_output_names
