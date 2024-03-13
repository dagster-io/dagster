from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

from toposort import CircularDependencyError, toposort

import dagster._check as check
from dagster._core.definitions.asset_checks import has_only_asset_checks
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.hook_definition import HookDefinition
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.selector.subset_selector import AssetSelectionData
from dagster._utils.merger import merge_dicts

from .asset_layer import AssetLayer
from .assets import AssetsDefinition
from .config import ConfigMapping
from .dependency import (
    BlockingAssetChecksDependencyDefinition,
    DependencyDefinition,
    DependencyMapping,
    IDependencyDefinition,
    NodeHandle,
    NodeInvocation,
    NodeOutputHandle,
)
from .events import AssetKey
from .executor_definition import ExecutorDefinition
from .graph_definition import GraphDefinition
from .job_definition import JobDefinition, default_job_io_manager
from .metadata import RawMetadataValue
from .partition import PartitionedConfig, PartitionsDefinition
from .resource_definition import ResourceDefinition
from .resource_requirement import ensure_requirements_satisfied
from .source_asset import SourceAsset
from .utils import DEFAULT_IO_MANAGER_KEY

# Prefix for auto created jobs that are used to materialize assets
ASSET_BASE_JOB_PREFIX = "__ASSET_JOB"

if TYPE_CHECKING:
    from dagster._core.definitions.run_config import RunConfig

    from .asset_check_spec import AssetCheckSpec


def is_base_asset_job_name(name: str) -> bool:
    return name.startswith(ASSET_BASE_JOB_PREFIX)


def get_base_asset_jobs(
    asset_graph: AssetGraph,
    resource_defs: Optional[Mapping[str, ResourceDefinition]],
    executor_def: Optional[ExecutorDefinition],
) -> Sequence[JobDefinition]:
    if len(asset_graph.all_partitions_defs) == 0:
        return [
            build_assets_job(
                name=ASSET_BASE_JOB_PREFIX,
                asset_graph=asset_graph,
                executor_def=executor_def,
                resource_defs=resource_defs,
            )
        ]
    else:
        jobs = []
        for i, partitions_def in enumerate(asset_graph.all_partitions_defs):
            executable_asset_keys = asset_graph.executable_asset_keys & {
                *asset_graph.asset_keys_for_partitions_def(partitions_def=partitions_def),
                *asset_graph.unpartitioned_asset_keys,
            }
            jobs.append(
                build_assets_job(
                    f"{ASSET_BASE_JOB_PREFIX}_{i}",
                    # For now, to preserve behavior keep all asset checks in all base jobs.
                    # When checks support partitions, they should only go in the corresponding
                    # partitioned job.
                    asset_graph.get_subset(
                        executable_asset_keys, asset_check_keys=asset_graph.asset_check_keys
                    ),
                    resource_defs=resource_defs,
                    executor_def=executor_def,
                    partitions_def=partitions_def,
                )
            )
        return jobs


def build_assets_job(
    name: str,
    asset_graph: AssetGraph,
    resource_defs: Optional[Mapping[str, object]] = None,
    description: Optional[str] = None,
    config: Optional[
        Union[ConfigMapping, Mapping[str, object], PartitionedConfig, "RunConfig"]
    ] = None,
    tags: Optional[Mapping[str, str]] = None,
    metadata: Optional[Mapping[str, RawMetadataValue]] = None,
    executor_def: Optional[ExecutorDefinition] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    hooks: Optional[AbstractSet[HookDefinition]] = None,
    op_retry_policy: Optional[RetryPolicy] = None,
    _asset_selection_data: Optional[AssetSelectionData] = None,
) -> JobDefinition:
    """Builds a job that materializes the given assets. This is a private function that is used
    during resolution of jobs created with `define_asset_job`.

    The dependencies between the ops in the job are determined by the asset dependencies defined
    in the metadata on the provided asset nodes.

    Args:
        name (str): The name of the job.
        asset_graph (AssetGraph): The asset graph that contains the assets and checks to be executed.
        resource_defs (Optional[Mapping[str, object]]): Resource defs to be included in
            this job.
        description (Optional[str]): A description of the job.
        op_retry_policy (Optional[RetryPolicy]): The default retry policy for all ops that compute assets in this job.
            Only used if retry policy is not defined on the asset definition.

    Examples:
        .. code-block:: python

            @asset
            def asset1():
                return 5

            @asset
            def asset2(asset1):
                return my_upstream_asset + 1

            my_assets_job = build_assets_job("my_assets_job", assets=[asset1, asset2])

    Returns:
        JobDefinition: A job that materializes the given assets.
    """
    from dagster._core.execution.build_resources import wrap_resources_for_execution

    resource_defs = check.opt_mapping_param(resource_defs, "resource_defs")
    resource_defs = merge_dicts({DEFAULT_IO_MANAGER_KEY: default_job_io_manager}, resource_defs)
    wrapped_resource_defs = wrap_resources_for_execution(resource_defs)

    # figure out what partitions (if any) exist for this job
    partitions_def = partitions_def or build_job_partitions_from_assets(
        asset_graph.assets_defs_for_keys(asset_graph.executable_asset_keys)
    )

    deps, assets_defs_by_node_handle = build_node_deps(asset_graph)

    # attempt to resolve cycles using multi-asset subsetting
    if _has_cycles(deps):
        asset_graph = _attempt_resolve_node_cycles(asset_graph)
        deps, assets_defs_by_node_handle = build_node_deps(asset_graph)

    node_defs = [
        asset.node_def
        for asset in asset_graph.assets_defs_for_keys(
            [
                *asset_graph.executable_asset_keys,
                *asset_graph.asset_check_keys,
            ]
        )
    ]

    graph = GraphDefinition(
        name=name,
        node_defs=node_defs,
        dependencies=deps,
        description=description,
        input_mappings=None,
        output_mappings=None,
        config=None,
    )

    asset_layer = AssetLayer.from_graph_and_assets_node_mapping(
        graph_def=graph,
        assets_defs_by_outer_node_handle=assets_defs_by_node_handle,
        asset_graph=asset_graph,
    )

    all_resource_defs = get_all_resource_defs(asset_graph, wrapped_resource_defs)

    if _asset_selection_data:
        original_job = _asset_selection_data.parent_job_def
        return graph.to_job(
            resource_defs=all_resource_defs,
            config=config,
            tags=tags,
            executor_def=executor_def,
            partitions_def=partitions_def,
            asset_layer=asset_layer,
            _asset_selection_data=_asset_selection_data,
            metadata=original_job.metadata,
            logger_defs=original_job.loggers,
            hooks=original_job.hook_defs,
            op_retry_policy=original_job._op_retry_policy,  # noqa: SLF001
            version_strategy=original_job.version_strategy,
        )

    return graph.to_job(
        resource_defs=all_resource_defs,
        config=config,
        tags=tags,
        metadata=metadata,
        executor_def=executor_def,
        partitions_def=partitions_def,
        asset_layer=asset_layer,
        hooks=hooks,
        op_retry_policy=op_retry_policy,
        _asset_selection_data=_asset_selection_data,
    )


def build_job_partitions_from_assets(
    assets: Iterable[Union[AssetsDefinition, SourceAsset]],
) -> Optional[PartitionsDefinition]:
    assets_with_partitions_defs = [assets_def for assets_def in assets if assets_def.partitions_def]

    if len(assets_with_partitions_defs) == 0:
        return None

    first_asset_with_partitions_def: Union[AssetsDefinition, SourceAsset] = (
        assets_with_partitions_defs[0]
    )
    for asset in assets_with_partitions_defs:
        if asset.partitions_def != first_asset_with_partitions_def.partitions_def:
            first_asset_key = _key_for_asset(asset).to_string()
            second_asset_key = _key_for_asset(first_asset_with_partitions_def).to_string()
            raise DagsterInvalidDefinitionError(
                "When an assets job contains multiple partitioned assets, they must have the "
                f"same partitions definitions, but asset '{first_asset_key}' and asset "
                f"'{second_asset_key}' have different partitions definitions. "
            )

    return first_asset_with_partitions_def.partitions_def


def _key_for_asset(asset: Union[AssetsDefinition, SourceAsset]) -> AssetKey:
    if isinstance(asset, AssetsDefinition):
        return next(iter(asset.keys))
    else:
        return asset.key


def _get_blocking_asset_check_output_handles_by_asset_key(
    assets_defs_by_node_handle: Mapping[NodeHandle, AssetsDefinition],
) -> Mapping[AssetKey, AbstractSet[NodeOutputHandle]]:
    """For each asset key, returns the set of node output handles that correspond to asset check
    specs that should block the execution of downstream assets if they fail.
    """
    check_specs_by_node_output_handle: Mapping[NodeOutputHandle, AssetCheckSpec] = {}

    for node_handle, assets_def in assets_defs_by_node_handle.items():
        for output_name, check_spec in assets_def.check_specs_by_output_name.items():
            check_specs_by_node_output_handle[
                NodeOutputHandle(node_handle, output_name=output_name)
            ] = check_spec

    blocking_asset_check_output_handles_by_asset_key: Dict[AssetKey, Set[NodeOutputHandle]] = (
        defaultdict(set)
    )
    for node_output_handle, check_spec in check_specs_by_node_output_handle.items():
        if check_spec.blocking:
            blocking_asset_check_output_handles_by_asset_key[check_spec.asset_key].add(
                node_output_handle
            )

    return blocking_asset_check_output_handles_by_asset_key


def build_node_deps(
    asset_graph: AssetGraph,
) -> Tuple[
    DependencyMapping[NodeInvocation],
    Mapping[NodeHandle, AssetsDefinition],
]:
    # sort so that nodes get a consistent name
    assets_defs = sorted(asset_graph.assets_defs, key=lambda ad: (sorted((ak for ak in ad.keys))))

    # if the same graph/op is used in multiple assets_definitions, their invocations must have
    # different names. we keep track of definitions that share a name and add a suffix to their
    # invocations to solve this issue
    collisions: Dict[str, int] = {}
    assets_defs_by_node_handle: Dict[NodeHandle, AssetsDefinition] = {}
    node_alias_and_output_by_asset_key: Dict[AssetKey, Tuple[str, str]] = {}
    for assets_def in (ad for ad in assets_defs if ad.is_executable):
        node_name = assets_def.node_def.name
        if collisions.get(node_name):
            collisions[node_name] += 1
            node_alias = f"{node_name}_{collisions[node_name]}"
        else:
            collisions[node_name] = 1
            node_alias = node_name

        # unique handle for each AssetsDefinition
        assets_defs_by_node_handle[NodeHandle(node_alias, parent=None)] = assets_def
        for output_name, key in assets_def.keys_by_output_name.items():
            node_alias_and_output_by_asset_key[key] = (node_alias, output_name)

    blocking_asset_check_output_handles_by_asset_key = (
        _get_blocking_asset_check_output_handles_by_asset_key(
            assets_defs_by_node_handle,
        )
    )

    deps: Dict[NodeInvocation, Dict[str, IDependencyDefinition]] = {}
    for node_handle, assets_def in assets_defs_by_node_handle.items():
        # the key that we'll use to reference the node inside this AssetsDefinition
        node_def_name = assets_def.node_def.name
        alias = node_handle.name if node_handle.name != node_def_name else None
        node_key = NodeInvocation(node_def_name, alias=alias)
        deps[node_key] = {}

        # TODO: We should be able to remove this after a refactor of `AssetsDefinition` and just use
        # a single method. At present using `keys_by_input_name` for asset checks only will exclude
        # `additional_deps`, so we need to use `node_keys_by_input_name`. But using
        # `node_keys_by_input_name` breaks cycle resolution on subsettable multi-assets.
        inputs_map = (
            assets_def.node_keys_by_input_name
            if has_only_asset_checks(assets_def)
            else assets_def.keys_by_input_name
        )

        # connect each input of this AssetsDefinition to the proper upstream node
        for input_name, upstream_asset_key in inputs_map.items():
            # ignore self-deps
            if upstream_asset_key in assets_def.keys:
                continue

            # if this assets def itself performs checks on an upstream key, exempt it from being
            # blocked on other checks
            if upstream_asset_key not in {ck.asset_key for ck in assets_def.check_keys}:
                blocking_asset_check_output_handles = (
                    blocking_asset_check_output_handles_by_asset_key.get(upstream_asset_key)
                )
                asset_check_deps = [
                    DependencyDefinition(
                        node_output_handle.node_handle.name, node_output_handle.output_name
                    )
                    for node_output_handle in blocking_asset_check_output_handles or []
                ]
            else:
                blocking_asset_check_output_handles = set()
                asset_check_deps = []

            if upstream_asset_key in node_alias_and_output_by_asset_key:
                upstream_node_alias, upstream_output_name = node_alias_and_output_by_asset_key[
                    upstream_asset_key
                ]

                asset_dep_def = DependencyDefinition(upstream_node_alias, upstream_output_name)
                if blocking_asset_check_output_handles:
                    deps[node_key][input_name] = BlockingAssetChecksDependencyDefinition(
                        asset_check_dependencies=asset_check_deps, other_dependency=asset_dep_def
                    )
                else:
                    deps[node_key][input_name] = asset_dep_def
            elif asset_check_deps:
                deps[node_key][input_name] = BlockingAssetChecksDependencyDefinition(
                    asset_check_dependencies=asset_check_deps, other_dependency=None
                )
    return deps, assets_defs_by_node_handle


def _has_cycles(
    deps: DependencyMapping[NodeInvocation],
) -> bool:
    """Detect if there are cycles in a dependency dictionary."""
    try:
        node_deps: Dict[str, Set[str]] = {}
        for upstream_node, downstream_deps in deps.items():
            # handle either NodeInvocation or str
            node_name = upstream_node.alias or upstream_node.name
            node_deps[node_name] = set()
            for dep in downstream_deps.values():
                if isinstance(dep, DependencyDefinition):
                    node_deps[node_name].add(dep.node)
                elif isinstance(dep, BlockingAssetChecksDependencyDefinition):
                    for subdep in dep.get_node_dependencies():
                        node_deps[node_name].add(subdep.node)
                else:
                    check.failed(f"Unexpected dependency type {type(dep)}.")
        # make sure that there is a valid topological sorting of these node dependencies
        list(toposort(node_deps))
        return False
    # only try to resolve cycles if we have a cycle
    except CircularDependencyError:
        return True


def _attempt_resolve_node_cycles(asset_graph: AssetGraph) -> AssetGraph:
    """DFS starting at root nodes to color the asset dependency graph. Each time you leave your
    current AssetsDefinition, the color increments.

    At the end of this process, we'll have a coloring for the asset graph such that any asset which
    is downstream of another asset via a different AssetsDefinition will be guaranteed to have
    a different (greater) color.

    Once we have our coloring, if any AssetsDefinition contains assets with different colors,
    we split that AssetsDefinition into a subset for each individual color.

    This ensures that no asset that shares a node with another asset will be downstream of
    that asset via a different node (i.e. there will be no cycles).
    """
    # color for each asset
    colors: Dict[AssetKey, int] = {}

    # recursively color an asset and all of its downstream assets
    def _dfs(key: AssetKey, cur_color: int):
        node = asset_graph.get(key)
        colors[key] = cur_color
        # in an external asset, treat all downstream as if they're in the same node
        cur_node_asset_keys = node.assets_def.keys if node.is_materializable else node.child_keys

        for child_key in node.child_keys:
            # if the downstream asset is in the current node,keep the same color
            new_color = cur_color if child_key in cur_node_asset_keys else cur_color + 1

            # if current color of the downstream asset is less than the new color, re-do dfs
            if colors.get(child_key, -1) < new_color:
                _dfs(child_key, new_color)

    # dfs for each root node; will throw an error if there are key-level cycles
    root_keys = asset_graph.toposorted_asset_keys_by_level[0]
    for key in root_keys:
        _dfs(key, 0)

    color_mapping_by_assets_defs: Dict[AssetsDefinition, Any] = defaultdict(
        lambda: defaultdict(set)
    )
    for key, color in colors.items():
        node = asset_graph.get(key)
        color_mapping_by_assets_defs[node.assets_def][color].add(key)

    subsetted_assets_defs: List[AssetsDefinition] = []
    for assets_def, color_mapping in color_mapping_by_assets_defs.items():
        if assets_def.is_external or len(color_mapping) == 1 or not assets_def.can_subset:
            subsetted_assets_defs.append(assets_def)
        else:
            for asset_keys in color_mapping.values():
                subsetted_assets_defs.append(
                    assets_def.subset_for(asset_keys, selected_asset_check_keys=None)
                )

    return AssetGraph.from_assets(subsetted_assets_defs)


def _ensure_resources_dont_conflict(
    asset_graph: AssetGraph,
    resource_defs: Mapping[str, ResourceDefinition],
) -> None:
    """Ensures that resources between assets, source assets, and provided resource dictionary do not conflict."""
    resource_defs_from_assets = {}
    for asset in asset_graph.assets_defs:
        for resource_key, resource_def in asset.resource_defs.items():
            if resource_key not in resource_defs_from_assets:
                resource_defs_from_assets[resource_key] = resource_def
            if resource_defs_from_assets[resource_key] != resource_def:
                raise DagsterInvalidDefinitionError(
                    f"Conflicting versions of resource with key '{resource_key}' "
                    "were provided to different assets. When constructing a "
                    "job, all resource definitions provided to assets must "
                    "match by reference equality for a given key."
                )
    for resource_key, resource_def in resource_defs.items():
        if (
            resource_key != DEFAULT_IO_MANAGER_KEY
            and resource_key in resource_defs_from_assets
            and resource_defs_from_assets[resource_key] != resource_def
        ):
            raise DagsterInvalidDefinitionError(
                f"resource with key '{resource_key}' provided to job "
                "conflicts with resource provided to assets. When constructing a "
                "job, all resource definitions provided must "
                "match by reference equality for a given key."
            )


def check_resources_satisfy_requirements(
    asset_graph: AssetGraph,
    resource_defs: Mapping[str, ResourceDefinition],
) -> None:
    """Ensures that between the provided resources on an asset and the resource_defs mapping, that all resource requirements are satisfied.

    Note that resources provided on assets cannot satisfy resource requirements provided on other assets.
    """
    _ensure_resources_dont_conflict(asset_graph, resource_defs)

    for assets_def in asset_graph.assets_defs:
        ensure_requirements_satisfied(
            merge_dicts(resource_defs, assets_def.resource_defs),
            list(assets_def.get_resource_requirements()),
        )


def get_all_resource_defs(
    asset_graph: AssetGraph,
    resource_defs: Mapping[str, ResourceDefinition],
) -> Mapping[str, ResourceDefinition]:
    # Ensures that no resource keys conflict, and each asset has its resource requirements satisfied.
    check_resources_satisfy_requirements(asset_graph, resource_defs)

    all_resource_defs = dict(resource_defs)
    for assets_def in asset_graph.assets_defs:
        all_resource_defs = merge_dicts(all_resource_defs, assets_def.resource_defs)

    return all_resource_defs
