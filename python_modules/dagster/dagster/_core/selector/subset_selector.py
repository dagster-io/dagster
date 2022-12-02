import re
import sys
from collections import defaultdict, deque
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    MutableSet,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
)

from typing_extensions import Literal, TypeAlias

from dagster._core.definitions.dependency import DependencyStructure
from dagster._core.definitions.events import AssetKey
from dagster._core.errors import DagsterExecutionStepNotFoundError, DagsterInvalidSubsetError
from dagster._utils import check

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition
    from dagster._core.definitions.job_definition import JobDefinition
    from dagster._core.definitions.pipeline_definition import PipelineDefinition
    from dagster._core.definitions.source_asset import SourceAsset

MAX_NUM = sys.maxsize

T = TypeVar("T")
DependencyGraph: TypeAlias = Mapping[str, Mapping[T, AbstractSet[T]]]


class OpSelectionData(
    NamedTuple(
        "_OpSelectionData",
        [
            ("op_selection", Sequence[str]),
            ("resolved_op_selection", AbstractSet[str]),
            ("parent_job_def", "JobDefinition"),
        ],
    )
):
    """The data about op selection.

    Attributes:
        op_selection (List[str]): The queries of op selection.
        resolved_op_selection (AbstractSet[str]): The names of selected ops.
        parent_job_def (JobDefinition): The definition of the full job. This is used for constructing
            pipeline snapshot lineage.
    """

    def __new__(
        cls,
        op_selection: Sequence[str],
        resolved_op_selection: AbstractSet[str],
        parent_job_def: "JobDefinition",
    ):
        from dagster._core.definitions.job_definition import JobDefinition

        return super(OpSelectionData, cls).__new__(
            cls,
            op_selection=check.sequence_param(op_selection, "op_selection", str),
            resolved_op_selection=check.set_param(
                resolved_op_selection, "resolved_op_selection", str
            ),
            parent_job_def=check.inst_param(parent_job_def, "parent_job_def", JobDefinition),
        )


class AssetSelectionData(
    NamedTuple(
        "_AssetSelectionData",
        [
            ("asset_selection", AbstractSet[AssetKey]),
            ("parent_job_def", "JobDefinition"),
        ],
    )
):
    """The data about asset selection.

    Attributes:
        asset_selection (FrozenSet[AssetKey]): The set of assets to be materialized within the job.
        parent_job_def (JobDefinition): The definition of the full job. This is used for constructing
            pipeline snapshot lineage.
    """

    def __new__(cls, asset_selection: AbstractSet[AssetKey], parent_job_def: "JobDefinition"):
        from dagster._core.definitions.job_definition import JobDefinition

        return super(AssetSelectionData, cls).__new__(
            cls,
            asset_selection=check.set_param(asset_selection, "asset_selection", AssetKey),
            parent_job_def=check.inst_param(parent_job_def, "parent_job_def", JobDefinition),
        )


def generate_asset_dep_graph(
    assets_defs: Iterable["AssetsDefinition"], source_assets: Iterable["SourceAsset"]
) -> DependencyGraph:
    from dagster._core.definitions.resolved_asset_deps import ResolvedAssetDependencies

    resolved_asset_deps = ResolvedAssetDependencies(assets_defs, source_assets)

    upstream: Dict[AssetKey, Set[AssetKey]] = {}
    downstream: Dict[AssetKey, Set[AssetKey]] = {}
    for assets_def in assets_defs:
        for asset_key in assets_def.keys:
            upstream[asset_key] = set()
            downstream[asset_key] = downstream.get(asset_key, set())
            # for each asset upstream of this one, set that as upstream, and this downstream of it
            upstream_asset_keys = resolved_asset_deps.get_resolved_upstream_asset_keys(
                assets_def, asset_key
            )
            for upstream_key in upstream_asset_keys:
                upstream[asset_key].add(upstream_key)
                downstream[upstream_key] = downstream.get(upstream_key, set()) | {asset_key}
    return {"upstream": upstream, "downstream": downstream}


def generate_dep_graph(pipeline_def: "PipelineDefinition") -> DependencyGraph:
    """'pipeline to dependency graph. It currently only supports top-level solids.

    Args:
        pipeline (PipelineDefinition): The pipeline to execute.

    Returns:
        graph (Dict[str, Dict[str, Set[str]]]): the input and output dependency graph. e.g.
            ```
            {
                "upstream": {
                    "solid_one_1": set(),
                    "solid_one_2": set(),
                    "solid_two": {"solid_one_1", "solid_one_2"},
                    "solid_three": {"solid_two"},
                },
                "downstream": {
                    "solid_one_1": {"solid_two"},
                    "solid_one_2": {"solid_two"},
                    "solid_two": {"solid_three"},
                    "solid_three": set(),
                },
            }
            ```
    """
    dependency_structure = check.inst_param(
        pipeline_def.dependency_structure, "dependency_structure", DependencyStructure
    )
    item_names = [i.name for i in pipeline_def.solids]

    # defaultdict isn't appropriate because we also want to include items without dependencies
    graph: Dict[str, Dict[str, MutableSet[str]]] = {"upstream": {}, "downstream": {}}
    for item_name in item_names:
        graph["upstream"][item_name] = set()
        upstream_dep = dependency_structure.input_to_upstream_outputs_for_node(item_name)
        for upstreams in upstream_dep.values():
            for up in upstreams:
                graph["upstream"][item_name].add(up.node_name)

        graph["downstream"][item_name] = set()
        downstream_dep = dependency_structure.output_to_downstream_inputs_for_node(item_name)
        for downstreams in downstream_dep.values():
            for down in downstreams:
                graph["downstream"][item_name].add(down.solid_name)

    return graph


Direction = Literal["downstream", "upstream"]


class Traverser:
    def __init__(self, graph: DependencyGraph):
        self.graph = graph

    # `depth=None` is infinite depth
    def _fetch_items(self, item_name: T, depth: int, direction: Direction) -> AbstractSet[T]:
        dep_graph = self.graph[direction]
        stack = deque([item_name])
        result: Set[T] = set()
        curr_depth = 0
        while stack:
            # stop when reach the given depth
            if curr_depth >= depth:
                break
            curr_level_len = len(stack)
            while stack and curr_level_len > 0:
                curr_item = stack.popleft()
                curr_level_len -= 1
                empty_set: Set[str] = set()
                for item in dep_graph.get(curr_item, empty_set):
                    if item not in result:
                        stack.append(item)
                        result.add(item)
            curr_depth += 1
        return result

    def fetch_upstream(self, item_name: T, depth: int) -> AbstractSet[T]:
        # return a set of ancestors of the given item, up to the given depth
        return self._fetch_items(item_name, depth, "upstream")

    def fetch_downstream(self, item_name: T, depth: int) -> AbstractSet[T]:
        # return a set of descendants of the given item, down to the given depth
        return self._fetch_items(item_name, depth, "downstream")


def fetch_connected(
    item: T,
    graph: DependencyGraph,
    *,
    direction: Direction,
    depth: Optional[int] = None,
) -> AbstractSet[T]:
    if depth is None:
        depth = MAX_NUM
    if direction == "downstream":
        return Traverser(graph).fetch_downstream(item, depth)
    elif direction == "upstream":
        return Traverser(graph).fetch_upstream(item, depth)


def fetch_sinks(graph: DependencyGraph, within_selection: AbstractSet[T]) -> AbstractSet[T]:
    """
    A sink is an asset that has no downstream dependencies within the provided selection.
    It can have other dependencies outside of the selection.
    """
    traverser = Traverser(graph)
    sinks: Set[T] = set()
    for item in within_selection:
        if len(traverser.fetch_downstream(item, depth=MAX_NUM) & within_selection) == 0:
            sinks.add(item)
    return sinks


def fetch_sources(graph: DependencyGraph, within_selection: AbstractSet[T]) -> AbstractSet[T]:
    """
    A source is a node that has no upstream dependencies within the provided selection.
    It can have other dependencies outside of the selection.
    """
    traverser = Traverser(graph)
    sources = set()
    for item in within_selection:
        if len(traverser.fetch_upstream(item, depth=MAX_NUM) & within_selection) == 0:
            sources.add(item)
    return sources


def fetch_connected_assets_definitions(
    asset: "AssetsDefinition",
    graph: DependencyGraph,
    name_to_definition_map: Mapping[str, "AssetsDefinition"],
    *,
    direction: Direction,
    depth: Optional[int] = MAX_NUM,
) -> FrozenSet["AssetsDefinition"]:
    depth = MAX_NUM if depth is None else depth
    names = [asset_key.to_user_string() for asset_key in asset.keys]
    connected_names = [
        n for name in names for n in fetch_connected(name, graph, direction=direction, depth=depth)
    ]
    return frozenset(name_to_definition_map[n] for n in connected_names)


def parse_clause(clause: str) -> Optional[Tuple[int, str, int]]:
    def _get_depth(part: str) -> int:
        if part == "":
            return 0
        elif "*" in part:
            return MAX_NUM
        elif set(part) == set("+"):
            return len(part)
        else:
            check.failed(f"Invalid clause part: {part}")

    token_matching = re.compile(r"^(\*?\+*)?([./\w\d\[\]?_-]+)(\+*\*?)?$").search(clause.strip())
    # return None if query is invalid
    parts: Sequence[str] = token_matching.groups() if token_matching is not None else []
    if len(parts) != 3:
        return None

    ancestor_part, item_name, descendant_part = parts
    up_depth = _get_depth(ancestor_part)
    down_depth = _get_depth(descendant_part)

    return (up_depth, item_name, down_depth)


def parse_items_from_selection(selection: Sequence[str]) -> Sequence[str]:
    items: List[str] = []
    for clause in selection:
        parts = parse_clause(clause)
        if parts is None:
            continue
        _u, item, _d = parts
        items.append(item)
    return items


def clause_to_subset(
    graph: DependencyGraph, clause: str, item_name_to_item_fn: Callable[[str], T]
) -> Sequence[T]:
    """Take a selection query and return a list of the selected and qualified items.

    Args:
        graph (Dict[str, Dict[T, Set[T]]]): the input and output dependency graph.
        clause (str): the subselection query in model selection syntax, e.g. "*some_solid+" will
            select all of some_solid's upstream dependencies and its direct downstream dependecies.
        item_name_to_item_fn (Callable[[str], T]): Converts item names found in the clause to items
            of the type held in the graph.

    Returns:
        subset_list (List[T]): a list of selected and qualified items, empty if input is
            invalid.
    """
    # parse clause
    if not isinstance(clause, str):
        return []
    parts = parse_clause(clause)
    if parts is None:
        return []
    up_depth, item_name, down_depth = parts
    # item_name invalid
    item = item_name_to_item_fn(item_name)
    if item not in graph["upstream"]:
        return []

    subset_list: List[T] = []
    traverser = Traverser(graph=graph)
    subset_list.append(item)
    # traverse graph to get up/downsteam items
    subset_list += traverser.fetch_upstream(item, up_depth)
    subset_list += traverser.fetch_downstream(item, down_depth)

    return subset_list


class LeafNodeSelection:
    """Marker for no further nesting selection needed."""


def convert_dot_seperated_string_to_dict(
    tree: Dict[str, Any], splits: Sequence[str]
) -> Dict[str, Any]:
    # For example:
    # "subgraph.subsubgraph.return_one" => {"subgraph": {"subsubgraph": {"return_one": None}}}
    key = splits[0]
    if len(splits) == 1:
        tree[key] = LeafNodeSelection
    else:
        tree[key] = convert_dot_seperated_string_to_dict(
            tree[key] if key in tree else {}, splits[1:]
        )
    return tree


def parse_op_selection(job_def: "JobDefinition", op_selection: Sequence[str]) -> Mapping[str, Any]:
    """
    Examples:
        ["subgraph.return_one", "subgraph.adder", "subgraph.add_one", "add_one"]
        => {"subgraph": {{"return_one": LeafNodeSelection}, {"adder": LeafNodeSelection}, {"add_one": LeafNodeSelection}}, "add_one": LeafNodeSelection}

        ["subgraph.subsubgraph.return_one"]
        => {"subgraph": {"subsubgraph": {"return_one": LeafNodeSelection}}}

        ["top_level_op_1+"]
        => {"top_level_op_1": LeafNodeSelection, "top_level_op_2": LeafNodeSelection}
    """
    if any(["." in item for item in op_selection]):
        resolved_op_selection_dict: Dict[str, Any] = {}
        for item in op_selection:
            convert_dot_seperated_string_to_dict(resolved_op_selection_dict, splits=item.split("."))
        return resolved_op_selection_dict

    return {
        top_level_op: LeafNodeSelection
        for top_level_op in parse_solid_selection(job_def, op_selection)
    }


def parse_solid_selection(
    pipeline_def: "PipelineDefinition",
    solid_selection: Sequence[str],
) -> FrozenSet[str]:
    """Take pipeline definition and a list of solid selection queries (inlcuding names of solid
        invocations. See syntax examples below) and return a set of the qualified solid names.

    It currently only supports top-level solids.

    Query syntax examples:
    - "some_solid": select "some_solid" itself
    - "*some_solid": select "some_solid" and all ancestors (upstream dependencies)
    - "some_solid*": select "some_solid" and all descendants (downstream dependencies)
    - "*some_solid*": select "some_solid" and all of its ancestors and descendants
    - "+some_solid": select "some_solid" and its ancestors at 1 level up
    - "some_solid+++": select "some_solid" and its descendants within 3 levels down

    Note:
    - If one of the query clauses is invalid, we will skip that one and continue to parse the valid
        ones.

    Args:
        pipeline_def (PipelineDefinition): the pipeline to execute.
        solid_selection (List[str]): a list of the solid selection queries (including single solid
            names) to execute.

    Returns:
        FrozenSet[str]: a frozenset of qualified deduplicated solid names, empty if no qualified
            subset selected.
    """
    check.sequence_param(solid_selection, "solid_selection", of_type=str)

    # special case: select all
    if len(solid_selection) == 1 and solid_selection[0] == "*":
        return frozenset(pipeline_def.graph.node_names())

    graph = generate_dep_graph(pipeline_def)
    solids_set: Set[str] = set()

    # loop over clauses
    for clause in solid_selection:
        subset = clause_to_subset(graph, clause, lambda x: x)
        if len(subset) == 0:
            raise DagsterInvalidSubsetError(
                "No qualified {node_type} to execute found for {selection_type}={requested}".format(
                    requested=solid_selection,
                    node_type="ops" if pipeline_def.is_job else "solids",
                    selection_type="op_selection" if pipeline_def.is_job else "solid_selection",
                )
            )
        solids_set.update(subset)

    return frozenset(solids_set)


def parse_step_selection(
    step_deps: Mapping[str, AbstractSet[str]], step_selection: Sequence[str]
) -> FrozenSet[str]:
    """Take the dependency dictionary generated while building execution plan and a list of step key
     selection queries and return a set of the qualified step keys.

    It currently only supports top-level solids.

    Args:
        step_deps (Dict[str, Set[str]]): a dictionary of execution step dependency where the key is
            a step key and the value is a set of direct upstream dependency of the step.
        step_selection (List[str]): a list of the step key selection queries (including single
            step key) to execute.

    Returns:
        FrozenSet[str]: a frozenset of qualified deduplicated solid names, empty if no qualified
            subset selected.
    """
    check.sequence_param(step_selection, "step_selection", of_type=str)
    # reverse step_deps to get the downstream_deps
    # make sure we have all items as keys, including the ones without downstream dependencies
    downstream_deps: Dict[str, Set[str]] = defaultdict(set, {k: set() for k in step_deps.keys()})
    for downstream_key, upstream_keys in step_deps.items():
        for step_key in upstream_keys:
            downstream_deps[step_key].add(downstream_key)

    # generate dep graph
    graph = {"upstream": step_deps, "downstream": downstream_deps}
    steps_set: Set[str] = set()

    step_keys = parse_items_from_selection(step_selection)
    invalid_keys = [key for key in step_keys if key not in step_deps]
    if invalid_keys:
        raise DagsterExecutionStepNotFoundError(
            f"Step selection refers to unknown step{'s' if len(invalid_keys)> 1 else ''}: {', '.join(invalid_keys)}",
            step_keys=invalid_keys,
        )

    # loop over clauses
    for clause in step_selection:
        subset = clause_to_subset(graph, clause, lambda x: x)
        if len(subset) == 0:
            raise DagsterInvalidSubsetError(
                "No qualified steps to execute found for step_selection={requested}".format(
                    requested=step_selection
                ),
            )
        steps_set.update(subset)

    return frozenset(steps_set)


def parse_asset_selection(
    assets_defs: Sequence["AssetsDefinition"],
    source_assets: Sequence["SourceAsset"],
    asset_selection: Sequence[str],
) -> AbstractSet[AssetKey]:
    """Find assets that match the given selection query

    Args:
        assets_defs (Sequence[Assetsdefinition]): A set of AssetsDefinition objects to select over
        asset_selection (List[str]): a list of the asset key selection queries (including single
            asset key) to execute.

    Returns:
        AbstractSet[AssetKey]: a frozenset of qualified deduplicated asset keys, empty if no
            qualified subset selected.
    """
    check.sequence_param(asset_selection, "asset_selection", of_type=str)

    # special case: select *
    if len(asset_selection) == 1 and asset_selection[0] == "*":
        return set().union(*(ad.keys for ad in assets_defs))

    graph = generate_asset_dep_graph(assets_defs, source_assets)
    assets_set: Set[AssetKey] = set()

    # loop over clauses
    for clause in asset_selection:
        subset = clause_to_subset(graph, clause, AssetKey.from_user_string)
        if len(subset) == 0:
            raise DagsterInvalidSubsetError(
                f"No qualified assets to execute found for clause='{clause}'"
            )
        assets_set.update(subset)

    return assets_set
