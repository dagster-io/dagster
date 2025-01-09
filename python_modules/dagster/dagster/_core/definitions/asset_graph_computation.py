import itertools
from collections import defaultdict
from collections.abc import Mapping
from functools import cached_property
from typing import AbstractSet, Optional, cast  # noqa: UP035

import dagster._check as check
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey, EntityKey
from dagster._core.definitions.asset_spec import AssetExecutionType
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.dependency import NodeHandle, NodeOutputHandle
from dagster._core.definitions.graph_definition import GraphDefinition, SubselectedGraphDefinition
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.op_selection import get_graph_subset
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.utils import toposort_flatten
from dagster._record import IHaveNew, copy, record, record_custom


@record_custom
class AssetGraphComputation(IHaveNew):
    """A computation whose purpose is to materialize assets, observe assets, and/or evaluate asset
    checks.

    Binds a NodeDefinition to the asset keys and asset check keys that it interacts with.
    """

    node_def: NodeDefinition
    keys_by_input_name: Mapping[str, AssetKey]
    keys_by_output_name: Mapping[str, AssetKey]
    check_keys_by_output_name: Mapping[str, AssetCheckKey]
    backfill_policy: Optional[BackfillPolicy]
    can_subset: bool
    is_subset: bool
    selected_asset_keys: AbstractSet[AssetKey]
    selected_asset_check_keys: AbstractSet[AssetCheckKey]
    execution_type: AssetExecutionType

    def __new__(
        cls,
        node_def: NodeDefinition,
        keys_by_input_name: Mapping[str, AssetKey],
        keys_by_output_name: Mapping[str, AssetKey],
        check_keys_by_output_name: Mapping[str, AssetCheckKey],
        backfill_policy: Optional[BackfillPolicy],
        can_subset: bool,
        is_subset: bool,
        selected_asset_keys: AbstractSet[AssetKey],
        selected_asset_check_keys: AbstractSet[AssetCheckKey],
        execution_type: AssetExecutionType,
    ):
        result = super().__new__(
            cls,
            node_def=node_def,
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name=keys_by_output_name,
            check_keys_by_output_name=check_keys_by_output_name,
            backfill_policy=backfill_policy,
            can_subset=can_subset,
            is_subset=is_subset,
            selected_asset_keys=selected_asset_keys,
            selected_asset_check_keys=selected_asset_check_keys,
            execution_type=execution_type,
        )
        result.output_names_by_key  # eagerly compute this to catch any errors at contruction time  # noqa: B018
        return result

    @cached_property
    def output_names_by_key(self) -> Mapping[AssetKey, str]:
        output_names_by_key: dict[AssetKey, str] = {}
        for output_name, key in self.keys_by_output_name.items():
            if key in output_names_by_key:
                check.failed(
                    f"Outputs '{output_names_by_key[key]}' and '{output_name}' both target the "
                    "same asset key. Each asset key should correspond to a single output."
                )
            output_names_by_key[key] = output_name

        return output_names_by_key

    @cached_property
    def entity_keys_by_op_output_handle(
        self,
    ) -> Mapping[NodeOutputHandle, EntityKey]:
        result = {}
        for output_name, key in itertools.chain(
            self.keys_by_output_name.items(), self.check_keys_by_output_name.items()
        ):
            output_def, node_handle = self.full_node_def.resolve_output_to_origin(output_name, None)
            result[NodeOutputHandle(node_handle=node_handle, output_name=output_def.name)] = key

        return result

    @property
    def full_node_def(self) -> NodeDefinition:
        node_def = self.node_def
        while isinstance(node_def, SubselectedGraphDefinition):
            node_def = node_def.parent_graph_def

        return node_def

    def subset_for(
        self,
        selected_asset_keys: AbstractSet[AssetKey],
        selected_asset_check_keys: Optional[AbstractSet[AssetCheckKey]],
    ) -> "AssetGraphComputation":
        check.invariant(
            self.can_subset,
            f"Attempted to subset AssetsDefinition for {self.node_def.name}, but can_subset=False.",
        )

        # Set of assets within selected_asset_keys which are outputted by this AssetDefinition
        asset_subselection = selected_asset_keys & self.selected_asset_keys
        if selected_asset_check_keys is None:
            # filter to checks that target selected asset keys
            asset_check_subselection = {
                key for key in self.selected_asset_check_keys if key.asset_key in asset_subselection
            }
        else:
            asset_check_subselection = selected_asset_check_keys & self.selected_asset_check_keys

        # Early escape if all assets and checks in AssetsDefinition are selected
        if (
            asset_subselection == self.selected_asset_keys
            and asset_check_subselection == self.selected_asset_check_keys
        ):
            return self
        elif isinstance(self.node_def, GraphDefinition):  # Node is graph-backed asset
            subsetted_node = self._subset_graph_backed_asset(
                asset_subselection, asset_check_subselection
            )

            return copy(
                self,
                node_def=subsetted_node,
                selected_asset_keys=selected_asset_keys & self.selected_asset_keys,
                selected_asset_check_keys=asset_check_subselection,
                is_subset=True,
            )
        else:
            # multi_asset subsetting
            return copy(
                self,
                selected_asset_keys=asset_subselection,
                selected_asset_check_keys=asset_check_subselection,
                is_subset=True,
            )

    def _subset_graph_backed_asset(
        self,
        selected_asset_keys: AbstractSet[AssetKey],
        selected_asset_check_keys: AbstractSet[AssetCheckKey],
    ) -> SubselectedGraphDefinition:
        if not isinstance(self.node_def, GraphDefinition):
            raise DagsterInvalidInvocationError(
                "Method _subset_graph_backed_asset cannot subset an asset that is not a graph"
            )

        dep_op_handles_by_entity_key = cast(
            # because self.node_def is a graph, these NodeHandles that reference ops inside it will
            # not be None
            Mapping[EntityKey, AbstractSet[NodeHandle]],
            self.dep_op_handles_by_entity_key,
        )
        op_selection: list[str] = []
        for asset_key in selected_asset_keys:
            dep_node_handles = dep_op_handles_by_entity_key[asset_key]
            for dep_op_handle in dep_node_handles:
                op_selection.append(".".join(dep_op_handle.path))
        for asset_check_key in selected_asset_check_keys:
            dep_op_handles = dep_op_handles_by_entity_key[asset_check_key]
            for dep_op_handle in dep_op_handles:
                op_selection.append(".".join(dep_op_handle.path))

        selected_outputs_by_op_handle: dict[NodeHandle, set[str]] = defaultdict(set)
        for (
            op_output_handle,
            entity_keys,
        ) in self.entity_keys_by_dep_op_output_handle.items():
            if any(
                key in selected_asset_keys or key in selected_asset_check_keys
                for key in entity_keys
            ):
                selected_outputs_by_op_handle[op_output_handle.node_handle].add(
                    op_output_handle.output_name
                )

        return get_graph_subset(
            self.node_def, op_selection, selected_outputs_by_op_handle=selected_outputs_by_op_handle
        )

    @cached_property
    def dep_op_handles_by_entity_key(
        self,
    ) -> Mapping[EntityKey, AbstractSet[Optional[NodeHandle]]]:
        result = defaultdict(set)
        for op_output_handle, keys in self.entity_keys_by_dep_op_output_handle.items():
            for key in keys:
                result[key].add(op_output_handle.node_handle)

        return result

    @cached_property
    def entity_keys_by_dep_op_output_handle(
        self,
    ) -> Mapping[NodeOutputHandle, AbstractSet[EntityKey]]:
        """Returns a mapping between op outputs and the assets and asset checks that, when selected,
        those op outputs need to be produced for.
        For non-graph-backed assets, this is essentially the same as node_keys_by_output_name.
        For graph-backed multi-assets, depending on the asset selection, we often only need to
        execute a subset of the ops and for those ops to only produce a subset of their outputs,
        in order to materialize/observe the asset.
        Op output X will be selected when asset (or asset check) A is selected iff there's at least
        one path in the graph from X to the op output corresponding to A, and no outputs in that
        path directly correspond to other assets.
        """
        entity_keys_by_op_output_handle = self.entity_keys_by_op_output_handle
        if not isinstance(self.full_node_def, GraphDefinition):
            return {
                key: {op_output_handle}
                for key, op_output_handle in entity_keys_by_op_output_handle.items()
            }

        op_output_graph = OpOutputHandleGraph.from_graph(self.full_node_def)
        reverse_toposorted_op_outputs_handles = [
            *reversed(toposort_flatten(op_output_graph.upstream)),
            *(op_output_graph.op_output_handles - op_output_graph.upstream.keys()),
        ]

        result: dict[NodeOutputHandle, set[EntityKey]] = defaultdict(set)

        for op_output_handle in reverse_toposorted_op_outputs_handles:
            asset_key_or_check_key = entity_keys_by_op_output_handle.get(op_output_handle)

            if asset_key_or_check_key:
                result[op_output_handle].add(asset_key_or_check_key)
            else:
                child_op_output_handles = op_output_graph.downstream.get(op_output_handle, set())
                for child_op_output_handle in child_op_output_handles:
                    result[op_output_handle].update(result[child_op_output_handle])

        return result


@record
class OpOutputHandleGraph:
    """A graph where each node is a NodeOutputHandle corresponding to an op. There's an edge from
    op_output_1 to op_output_2 if op_output_2 is part of an op that has an input that's connected to
    op_output_1.
    """

    op_output_handles: AbstractSet[NodeOutputHandle]
    upstream: Mapping[NodeOutputHandle, AbstractSet[NodeOutputHandle]]
    downstream: Mapping[NodeOutputHandle, AbstractSet[NodeOutputHandle]]

    @staticmethod
    def from_graph(graph_def: "GraphDefinition") -> "OpOutputHandleGraph":
        op_output_handles = graph_def.get_op_output_handles(None)
        input_output_pairs = graph_def.get_op_input_output_handle_pairs(None)

        op_output_handles_by_op_handle: dict[NodeHandle, set[NodeOutputHandle]] = defaultdict(set)
        for op_output_handle in op_output_handles:
            op_output_handles_by_op_handle[op_output_handle.node_handle].add(op_output_handle)

        downstream_op_output_handles_by_op_output_handle: dict[
            NodeOutputHandle, set[NodeOutputHandle]
        ] = defaultdict(set)
        upstream_op_output_handles_by_op_output_handle: dict[
            NodeOutputHandle, set[NodeOutputHandle]
        ] = defaultdict(set)

        for op_output_handle, op_input_handle in input_output_pairs:
            downstream_op_output_handles = op_output_handles_by_op_handle[
                op_input_handle.node_handle
            ]
            for downstream_op_output_handle in downstream_op_output_handles:
                upstream_op_output_handles_by_op_output_handle[downstream_op_output_handle].add(
                    op_output_handle
                )
                downstream_op_output_handles_by_op_output_handle[op_output_handle].add(
                    downstream_op_output_handle
                )

        return OpOutputHandleGraph(
            op_output_handles=op_output_handles,
            downstream=downstream_op_output_handles_by_op_output_handle,
            upstream=upstream_op_output_handles_by_op_output_handle,
        )
