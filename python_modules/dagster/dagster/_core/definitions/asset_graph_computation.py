import itertools
from collections import defaultdict
from functools import cached_property
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    cast,
)

import dagster._check as check
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey, AssetKeyOrCheckKey
from dagster._core.definitions.asset_spec import AssetExecutionType
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.dependency import NodeHandle, NodeInputHandle, NodeOutputHandle
from dagster._core.definitions.graph_definition import GraphDefinition, SubselectedGraphDefinition
from dagster._core.definitions.op_selection import get_graph_subset
from dagster._core.definitions.output import OutputMapping
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.utils import toposort_flatten
from dagster._record import IHaveNew, copy, record, record_custom
from dagster._utils.warnings import disable_dagster_warnings

from .node_definition import NodeDefinition

if TYPE_CHECKING:
    from .asset_graph import AssetGraph


@record(checked=False)
class AtomicExecutionSet:
    keys: AbstractSet[AssetKeyOrCheckKey]

    @cached_property
    def unique_id(self) -> str:
        from .assets import unique_id_from_asset_and_check_keys

        return unique_id_from_asset_and_check_keys(self.keys)


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
    backfill_policies_by_op_handle: Mapping[Optional[NodeHandle], BackfillPolicy]
    atomic_execution_sets: Sequence[AtomicExecutionSet]
    execution_types_by_key: Mapping[AssetKey, AssetExecutionType]

    # subselection-related attributes
    is_subset: bool
    selected_asset_keys: AbstractSet[AssetKey]
    selected_asset_check_keys: AbstractSet[AssetCheckKey]

    def __new__(
        cls,
        node_def: NodeDefinition,
        keys_by_input_name: Mapping[str, AssetKey],
        keys_by_output_name: Mapping[str, AssetKey],
        check_keys_by_output_name: Mapping[str, AssetCheckKey],
        backfill_policies_by_op_handle: Mapping[Optional[NodeHandle], BackfillPolicy],
        atomic_execution_sets: Sequence[AtomicExecutionSet],
        is_subset: bool,
        selected_asset_keys: AbstractSet[AssetKey],
        selected_asset_check_keys: AbstractSet[AssetCheckKey],
        execution_types_by_key: Mapping[AssetKey, AssetExecutionType],
    ):
        for atomic_execution_set in atomic_execution_sets:
            if len(atomic_execution_set.keys) < 2:
                check.failed(
                    f"Atomic execution sets must have more than one key: {atomic_execution_set}"
                )

        result = super().__new__(
            cls,
            node_def=node_def,
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name=keys_by_output_name,
            check_keys_by_output_name=check_keys_by_output_name,
            atomic_execution_sets=atomic_execution_sets,
            backfill_policies_by_op_handle=backfill_policies_by_op_handle,
            is_subset=is_subset,
            selected_asset_keys=selected_asset_keys,
            selected_asset_check_keys=selected_asset_check_keys,
            execution_types_by_key=execution_types_by_key,
        )
        result.output_names_by_key  # eagerly compute this to catch any errors at contruction time  # noqa: B018
        return result

    @cached_property
    def output_names_by_key(self) -> Mapping[AssetKey, str]:
        output_names_by_key: Dict[AssetKey, str] = {}
        for output_name, key in self.keys_by_output_name.items():
            if key in output_names_by_key:
                check.failed(
                    f"Outputs '{output_names_by_key[key]}' and '{output_name}' both target the "
                    "same asset key. Each asset key should correspond to a single output."
                )
            output_names_by_key[key] = output_name

        return output_names_by_key

    def can_subset_to(self, asset_or_check_keys: AbstractSet[AssetKeyOrCheckKey]) -> bool:
        visited_execution_set_ids = set()
        for asset_or_check_key in asset_or_check_keys:
            execution_set = self.execution_sets_by_asset_or_check_key.get(asset_or_check_key)
            if (
                execution_set is not None
                and execution_set.unique_id not in visited_execution_set_ids
            ):
                for execution_set_asset_key_or_check_key in execution_set.keys:
                    if execution_set_asset_key_or_check_key not in asset_or_check_keys:
                        return False
                visited_execution_set_ids.add(execution_set.unique_id)

        return True

    def get_execution_set_identifier(self, asset_or_check_key: AssetKeyOrCheckKey) -> Optional[str]:
        execution_set = self.execution_sets_by_asset_or_check_key.get(asset_or_check_key)
        if execution_set is None:
            return None

        return execution_set.unique_id

    @cached_property
    def execution_sets_by_asset_or_check_key(
        self,
    ) -> Mapping[AssetKeyOrCheckKey, AtomicExecutionSet]:
        return {
            key: atomic_execution_set
            for atomic_execution_set in self.atomic_execution_sets
            for key in atomic_execution_set.keys
        }

    @cached_property
    def asset_or_check_keys_by_op_output_handle(
        self,
    ) -> Mapping[NodeOutputHandle, AssetKeyOrCheckKey]:
        result = {}
        for output_name, key in itertools.chain(
            self.keys_by_output_name.items(), self.check_keys_by_output_name.items()
        ):
            output_def, node_handle = self.full_node_def.resolve_output_to_origin(output_name, None)
            result[NodeOutputHandle(node_handle=node_handle, output_name=output_def.name)] = key

        return result

    @cached_property
    def asset_or_check_keys_by_op_handle(
        self,
    ) -> Mapping[NodeOutputHandle, AbstractSet[AssetKeyOrCheckKey]]:
        result = defaultdict(set)
        for op_output_handle, key in self.asset_or_check_keys_by_op_output_handle.items():
            result[op_output_handle.node_handle].add(key)

        return result

    @cached_property
    def asset_keys_by_node_input_handle(self) -> Mapping[NodeInputHandle, AssetKey]:
        full_node_def = self.full_node_def

        # handles that aren't mapped to any higher-level inputs
        keys_by_outer_node_input_handle: Dict[NodeInputHandle, AssetKey] = {}

        for input_name, asset_key in self.keys_by_input_name.items():
            keys_by_outer_node_input_handle[
                NodeInputHandle(node_handle=None, input_name=input_name)
            ] = asset_key

        for output_name, asset_key in self.keys_by_output_name.items():
            for destination in full_node_def.resolve_output_to_destinations(output_name, None):
                keys_by_outer_node_input_handle[destination] = asset_key

        if isinstance(full_node_def, GraphDefinition):
            stack: List[Tuple[GraphDefinition, Optional[NodeHandle]]] = [(full_node_def, None)]

            while stack:
                graph_def, parent_node_handle = stack.pop()

                for node_name, input_assets in graph_def.input_assets.items():
                    node_handle = NodeHandle(node_name, parent_node_handle)
                    for input_name, assets_def in input_assets.items():
                        input_handle = NodeInputHandle(
                            node_handle=node_handle, input_name=input_name
                        )
                        keys_by_outer_node_input_handle[input_handle] = assets_def.key

                for node_name, node in graph_def.node_dict.items():
                    if isinstance(node.definition, GraphDefinition):
                        stack.append((node.definition, NodeHandle(node_name, parent_node_handle)))

            result: Dict[NodeInputHandle, AssetKey] = {**keys_by_outer_node_input_handle}
            for node_input_handle, asset_key in keys_by_outer_node_input_handle.items():
                for op_input_handle in full_node_def.get_node(
                    node_input_handle.node_handle
                ).definition.resolve_input_to_destinations(node_input_handle):
                    result[op_input_handle] = asset_key
            return result
        else:
            return keys_by_outer_node_input_handle

    @cached_property
    def op_output_handles_by_asset_or_check_key(
        self,
    ) -> Mapping[AssetKeyOrCheckKey, NodeOutputHandle]:
        return {
            key: output_handle
            for output_handle, key in self.asset_or_check_keys_by_op_output_handle.items()
        }

    @property
    def full_node_def(self) -> NodeDefinition:
        node_def = self.node_def
        while isinstance(node_def, SubselectedGraphDefinition):
            node_def = node_def.parent_graph_def

        return node_def

    @staticmethod
    def merge(
        computations: Sequence["AssetGraphComputation"],
        asset_graph: "AssetGraph",
        outer_graph_name: str,
    ) -> "AssetGraphComputation":
        from .asset_job import _attempt_resolve_node_cycles, _has_cycles, build_node_deps

        deps, computations_by_node_invocation = build_node_deps(computations, asset_graph)

        # attempt to resolve cycles using multi-asset subsetting
        if _has_cycles(deps):
            asset_graph = _attempt_resolve_node_cycles(asset_graph)
            deps, computations_by_node_invocation = build_node_deps(
                [
                    assets_def.computation
                    for assets_def in asset_graph.assets_defs
                    if assets_def.computation is not None
                ],
                asset_graph,
            )

        merged_keys_by_output_name: Dict[str, AssetKey] = {}
        merged_check_keys_by_output_name: Dict[str, AssetCheckKey] = {}
        merged_selected_asset_keys: Set[AssetKey] = set()
        merged_selected_asset_check_keys: Set[AssetCheckKey] = set()
        merged_atomic_execution_sets: Sequence[AtomicExecutionSet] = []
        merged_execution_types_by_key: Dict[AssetKey, AssetExecutionType] = {}
        merged_backfill_policies_by_op_handle: Dict[NodeHandle, BackfillPolicy] = {}
        output_mappings_by_name: Dict[str, OutputMapping] = {}
        for node_invocation, computation in computations_by_node_invocation.items():
            merged_selected_asset_keys.update(computation.selected_asset_keys)
            merged_selected_asset_check_keys.update(computation.selected_asset_check_keys)
            merged_atomic_execution_sets.extend(computation.atomic_execution_sets)
            merged_execution_types_by_key.update(computation.execution_types_by_key)
            node_handle = NodeHandle(name=node_invocation.resolved_name, parent=None)
            for op_handle, backfill_policy in computation.backfill_policies_by_op_handle.items():
                merged_backfill_policies_by_op_handle[node_handle.with_child(op_handle)] = (
                    backfill_policy
                )

            for output_name, asset_key in computation.keys_by_output_name.items():
                if output_name in computation.node_def.output_dict:
                    graph_output_name = asset_key.to_python_identifier()
                    merged_keys_by_output_name[graph_output_name] = asset_key
                    if (
                        graph_output_name in output_mappings_by_name
                        and asset_key not in computation.selected_asset_keys
                    ):
                        # TODO: add comment explaining why we get here - cycle resolution
                        continue

                    output_mappings_by_name[graph_output_name] = OutputMapping(
                        graph_output_name=graph_output_name,
                        mapped_node_name=node_invocation.resolved_name,
                        mapped_node_output_name=output_name,
                    )

            for output_name, asset_check_key in computation.check_keys_by_output_name.items():
                if (
                    asset_check_key in computation.selected_asset_check_keys
                    and output_name in computation.node_def.output_dict
                ):
                    graph_output_name = asset_check_key.to_python_identifier()
                    merged_check_keys_by_output_name[graph_output_name] = asset_check_key
                    if (
                        graph_output_name in output_mappings_by_name
                        and asset_check_key not in computation.selected_asset_check_keys
                    ):
                        # TODO: add comment explaining why we get here - cycle resolution
                        continue

                    output_mappings_by_name[graph_output_name] = OutputMapping(
                        graph_output_name=graph_output_name,
                        mapped_node_name=node_invocation.resolved_name,
                        mapped_node_output_name=output_name,
                    )
        from .asset_spec import AssetSpec
        from .assets import AssetsDefinition

        input_assets: Dict[str, Dict[str, AssetsDefinition]] = defaultdict(dict)
        for node_invocation, computation in computations_by_node_invocation.items():
            for input_name, asset_key in computation.keys_by_input_name.items():
                if (
                    not deps[node_invocation].get(input_name)
                    # if the node_def is a subsetted graph, it might not have all the inputs that
                    # are in keys_by_input_name
                    and input_name in computation.node_def.input_dict
                ):
                    if asset_graph.has(asset_key):
                        asset_spec = asset_graph.get(asset_key).to_asset_spec()
                    else:
                        asset_spec = AssetSpec(asset_key)

                    with disable_dagster_warnings():
                        assets_def = AssetsDefinition(specs=[asset_spec])

                    input_assets[node_invocation.resolved_name][input_name] = assets_def

        graph_def = GraphDefinition(
            name=outer_graph_name,
            node_defs=[computation.node_def for computation in computations],
            dependencies=deps,
            output_mappings=list(output_mappings_by_name.values()),
            input_mappings=None,
            input_assets=input_assets,
        )
        return AssetGraphComputation(
            node_def=graph_def,
            keys_by_input_name={},
            keys_by_output_name=merged_keys_by_output_name,
            check_keys_by_output_name=merged_check_keys_by_output_name,
            backfill_policies_by_op_handle=merged_backfill_policies_by_op_handle,
            atomic_execution_sets=merged_atomic_execution_sets,
            is_subset=any(computation.is_subset for computation in computations),
            selected_asset_keys=merged_selected_asset_keys,
            selected_asset_check_keys=merged_selected_asset_check_keys,
            execution_types_by_key=merged_execution_types_by_key,
        )

    def subset_for(
        self,
        selected_asset_keys: AbstractSet[AssetKey],
        selected_asset_check_keys: Optional[AbstractSet[AssetCheckKey]],
    ) -> "AssetGraphComputation":
        check.invariant(
            self.can_subset_to(selected_asset_keys | (selected_asset_check_keys or set())),
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

        dep_op_handles_by_asset_or_check_key = cast(
            # because self.node_def is a graph, these NodeHandles that reference ops inside it will
            # not be None
            Mapping[AssetKeyOrCheckKey, AbstractSet[NodeHandle]],
            self.dep_op_handles_by_asset_or_check_key,
        )
        op_selection: List[str] = []
        for asset_key in selected_asset_keys:
            dep_node_handles = dep_op_handles_by_asset_or_check_key[asset_key]
            for dep_op_handle in dep_node_handles:
                op_selection.append(".".join(dep_op_handle.path))
        for asset_check_key in selected_asset_check_keys:
            dep_op_handles = dep_op_handles_by_asset_or_check_key[asset_check_key]
            for dep_op_handle in dep_op_handles:
                op_selection.append(".".join(dep_op_handle.path))

        selected_outputs_by_op_handle: Dict[NodeHandle, Set[str]] = defaultdict(set)
        for (
            op_output_handle,
            asset_or_check_keys,
        ) in self.asset_or_check_keys_by_dep_op_output_handle.items():
            if any(
                key in selected_asset_keys or key in selected_asset_check_keys
                for key in asset_or_check_keys
            ):
                selected_outputs_by_op_handle[op_output_handle.node_handle].add(
                    op_output_handle.output_name
                )

        return get_graph_subset(
            self.node_def, op_selection, selected_outputs_by_op_handle=selected_outputs_by_op_handle
        )

    @cached_property
    def dep_op_handles_by_asset_or_check_key(
        self,
    ) -> Mapping[AssetKeyOrCheckKey, AbstractSet[Optional[NodeHandle]]]:
        result = defaultdict(set)
        for op_output_handle, keys in self.asset_or_check_keys_by_dep_op_output_handle.items():
            for key in keys:
                result[key].add(op_output_handle.node_handle)

        return result

    @cached_property
    def asset_or_check_keys_by_dep_op_output_handle(
        self,
    ) -> Mapping[NodeOutputHandle, AbstractSet[AssetKeyOrCheckKey]]:
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
        asset_or_check_keys_by_op_output_handle = self.asset_or_check_keys_by_op_output_handle
        if not isinstance(self.full_node_def, GraphDefinition):
            return {
                key: {op_output_handle}
                for key, op_output_handle in asset_or_check_keys_by_op_output_handle.items()
            }

        op_output_graph = OpOutputHandleGraph.from_graph(self.full_node_def)
        reverse_toposorted_op_outputs_handles = [
            *reversed(toposort_flatten(op_output_graph.upstream)),
            *(op_output_graph.op_output_handles - op_output_graph.upstream.keys()),
        ]

        result: Dict[NodeOutputHandle, Set[AssetKeyOrCheckKey]] = defaultdict(set)

        for op_output_handle in reverse_toposorted_op_outputs_handles:
            asset_key_or_check_key = asset_or_check_keys_by_op_output_handle.get(op_output_handle)

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

        op_output_handles_by_op_handle: Dict[NodeHandle, Set[NodeOutputHandle]] = defaultdict(set)
        for op_output_handle in op_output_handles:
            op_output_handles_by_op_handle[op_output_handle.node_handle].add(op_output_handle)

        downstream_op_output_handles_by_op_output_handle: Dict[
            NodeOutputHandle, Set[NodeOutputHandle]
        ] = defaultdict(set)
        upstream_op_output_handles_by_op_output_handle: Dict[
            NodeOutputHandle, Set[NodeOutputHandle]
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
