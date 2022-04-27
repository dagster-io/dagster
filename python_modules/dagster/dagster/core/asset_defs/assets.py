from typing import AbstractSet, Mapping, Optional, cast

from dagster import check
from dagster.core.definitions import NodeDefinition, OpDefinition
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

        all_input_asset_keys = set(asset_keys_by_input_name.values())
        self._asset_deps = asset_deps or {
            output_key: all_input_asset_keys for output_key in asset_keys_by_output_name.values()
        }

    def __call__(self, *args, **kwargs):
        return self._node_def(*args, **kwargs)

    @staticmethod
    def from_graph(
        graph_def: GraphDefinition,
        asset_keys_by_input_name: Mapping[str, AssetKey],
        asset_keys_by_output_name: Mapping[str, AssetKey],
        internal_asset_deps: Optional[Mapping[str, SetAssetKey]] = None,
    ):
        AssetsDefinition(
            asset_keys_by_input_name=_infer_asset_keys_by_input_names(
                graph_def,
                asset_keys_by_input_name or {},
            ),
            asset_keys_by_output_name=_infer_asset_keys_by_output_names(
                graph_def, asset_keys_by_output_name or {}
            ),
            op=graph_def,  # TODO: change this arg name to node_def once dependent PR merged
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
    for in_key in asset_keys_by_input_name.keys():
        if in_key not in all_input_names:
            raise DagsterInvalidDefinitionError(
                f"Key '{in_key}' in provided asset_keys_by_input_name dict does not correspond to "
                "any key provided in the ins dictionary of the decorated op or any argument "
                "to the decorated function"
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
    inferred_asset_keys_by_output_names: Dict[AssetKey, str] = asset_keys_by_output_name.copy()
    output_names = [output.definition.name for output in graph_def.output_mappings]

    if (
        len(output_names) == 1
        and output_names[0] not in asset_keys_by_output_name
        and output_names[0] == "result"
    ):
        # If there is only one output and the name is the default "result", generate asset key
        # from the name of the node
        inferred_asset_keys_by_output_names[output_names[0]] = AssetKey([node_def.name])

    for output_name in asset_keys_by_output_name.keys():
        if output_name not in output_names:
            raise DagsterInvalidDefinitionError(
                f"Key {output_name} in provided asset_keys_by_output_name does not correspond "
                "to any key provided in the out dictionary of the decorated op"
            )

    for output_name in output_names:
        if output_name not in inferred_asset_keys_by_output_names:
            inferred_asset_keys_by_output_names[output_name] = AssetKey([output_name])
    return inferred_asset_keys_by_output_names
