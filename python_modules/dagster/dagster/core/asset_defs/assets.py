import warnings
from typing import AbstractSet, Dict, Iterable, Mapping, Optional, Sequence, Set, cast

import dagster._check as check
from dagster.core.definitions import GraphDefinition, NodeDefinition, NodeHandle, OpDefinition
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.partition import PartitionsDefinition
from dagster.utils.backcompat import ExperimentalWarning, experimental

from .partition_mapping import PartitionMapping
from .source_asset import SourceAsset


class AssetsDefinition:
    def __init__(
        self,
        asset_keys_by_input_name: Mapping[str, AssetKey],
        asset_keys_by_output_name: Mapping[str, AssetKey],
        node_def: NodeDefinition,
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_mappings: Optional[Mapping[AssetKey, PartitionMapping]] = None,
        asset_deps: Optional[Mapping[AssetKey, AbstractSet[AssetKey]]] = None,
        selected_asset_keys: Optional[AbstractSet[AssetKey]] = None,
        can_subset: bool = False,
        # if adding new fields, make sure to handle them in both with_replaced_asset_keys and subset_for
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

        if selected_asset_keys is not None:
            self._selected_asset_keys = selected_asset_keys
        else:
            self._selected_asset_keys = all_asset_keys
        self._can_subset = can_subset

    def __call__(self, *args, **kwargs):
        return self._node_def(*args, **kwargs)

    @staticmethod
    @experimental
    def from_graph(
        graph_def: GraphDefinition,
        asset_keys_by_input_name: Optional[Mapping[str, AssetKey]] = None,
        asset_keys_by_output_name: Optional[Mapping[str, AssetKey]] = None,
        internal_asset_deps: Optional[Mapping[str, Set[AssetKey]]] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
    ) -> "AssetsDefinition":
        """
        Constructs an AssetsDefinition from a GraphDefinition.

        Args:
            graph_def (GraphDefinition): The GraphDefinition that is an asset.
            asset_keys_by_input_name (Optional[Mapping[str, AssetKey]]): A mapping of the input
                names of the decorated graph to their corresponding asset keys. If not provided,
                the input asset keys will be created from the graph input names.
            asset_keys_by_output_name (Optional[Mapping[str, AssetKey]]): A mapping of the output
                names of the decorated graph to their corresponding asset keys. If not provided,
                the output asset keys will be created from the graph output names.
            internal_asset_deps (Optional[Mapping[str, Set[AssetKey]]]): By default, it is assumed
                that all assets produced by the graph depend on all assets that are consumed by that
                graph. If this default is not correct, you pass in a map of output names to a
                corrected set of AssetKeys that they depend on. Any AssetKeys in this list must be
                either used as input to the asset or produced within the graph.
            partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
                compose the assets.
        """
        graph_def = check.inst_param(graph_def, "graph_def", GraphDefinition)
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
            partitions_def=check.opt_inst_param(
                partitions_def, "partitions_def", PartitionsDefinition
            ),
        )

    @property
    def can_subset(self) -> bool:
        return self._can_subset

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
            len(self.asset_keys) == 1,
            "Tried to retrieve asset key from an assets definition with multiple asset keys: "
            + ", ".join([str(ak.to_string()) for ak in self._asset_keys_by_output_name.values()]),
        )

        return next(iter(self.asset_keys))

    @property
    def asset_keys(self) -> AbstractSet[AssetKey]:
        return self._selected_asset_keys

    @property
    def dependency_asset_keys(self) -> Iterable[AssetKey]:
        # the input asset keys that are directly upstream of a selected asset key
        upstream_keys = set().union(*(self.asset_deps[key] for key in self.asset_keys))
        input_keys = set(self._asset_keys_by_input_name.values())
        return upstream_keys.intersection(input_keys)

    @property
    def node_asset_keys_by_output_name(self) -> Mapping[str, AssetKey]:
        """AssetKey for each output on the underlying NodeDefinition"""
        return self._asset_keys_by_output_name

    @property
    def node_asset_keys_by_input_name(self) -> Mapping[str, AssetKey]:
        """AssetKey for each input on the underlying NodeDefinition"""
        return self._asset_keys_by_input_name

    @property
    def asset_keys_by_output_name(self) -> Mapping[str, AssetKey]:
        return {
            name: key
            for name, key in self.node_asset_keys_by_output_name.items()
            if key in self.asset_keys
        }

    @property
    def asset_keys_by_input_name(self) -> Mapping[str, AssetKey]:
        upstream_keys = set().union(*(self.asset_deps[key] for key in self.asset_keys))
        return {
            name: key
            for name, key in self.node_asset_keys_by_input_name.items()
            if key in upstream_keys
        }

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
                    for input_name, key in self._asset_keys_by_input_name.items()
                },
                asset_keys_by_output_name={
                    output_name: output_asset_key_replacements.get(key, key)
                    for output_name, key in self._asset_keys_by_output_name.items()
                },
                node_def=self.node_def,
                partitions_def=self.partitions_def,
                partition_mappings=self._partition_mappings,
                asset_deps={
                    # replace both the keys and the values in this mapping
                    output_asset_key_replacements.get(key, key): {
                        input_asset_key_replacements.get(
                            upstream_key,
                            output_asset_key_replacements.get(upstream_key, upstream_key),
                        )
                        for upstream_key in value
                    }
                    for key, value in self.asset_deps.items()
                },
                can_subset=self.can_subset,
                selected_asset_keys={
                    output_asset_key_replacements.get(key, key) for key in self._selected_asset_keys
                },
            )

    def subset_for(self, selected_asset_keys: AbstractSet[AssetKey]) -> "AssetsDefinition":
        """
        Create a subset of this AssetsDefinition that will only materialize the assets in the
        selected set.

        Args:
            selected_asset_keys (AbstractSet[AssetKey]): The total set of asset keys
        """
        check.invariant(
            self.can_subset,
            f"Attempted to subset AssetsDefinition for {self.node_def.name}, but can_subset=False.",
        )
        return AssetsDefinition(
            # keep track of the original mapping
            asset_keys_by_input_name=self._asset_keys_by_input_name,
            asset_keys_by_output_name=self._asset_keys_by_output_name,
            # TODO: subset this properly for graph-backed-assets
            node_def=self.node_def,
            partitions_def=self.partitions_def,
            partition_mappings=self._partition_mappings,
            asset_deps=self._asset_deps,
            can_subset=self.can_subset,
            selected_asset_keys=selected_asset_keys & self.asset_keys,
        )

    def to_source_assets(self) -> Sequence[SourceAsset]:
        result = []
        for output_name, asset_key in self.asset_keys_by_output_name.items():
            # This could maybe be sped up by batching
            output_def = self.node_def.resolve_output_to_origin(
                output_name, NodeHandle(self.node_def.name, parent=None)
            )[0]
            result.append(
                SourceAsset(
                    key=asset_key,
                    metadata=output_def.metadata,
                    io_manager_key=output_def.io_manager_key,
                    description=output_def.description,
                )
            )

        return result


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
    output_names = [output_def.name for output_def in graph_def.output_defs]
    if asset_keys_by_output_name:
        check.invariant(
            set(asset_keys_by_output_name.keys()) == set(output_names),
            "The set of output names keys specified in the asset_keys_by_output_name argument must "
            "equal the set of asset keys outputted by this GraphDefinition. \n"
            f"asset_keys_by_input_name keys: {set(asset_keys_by_output_name.keys())} \n"
            f"expected keys: {set(output_names)}",
        )

    inferred_asset_keys_by_output_names: Dict[str, AssetKey] = {
        output_name: asset_key for output_name, asset_key in asset_keys_by_output_name.items()
    }

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
