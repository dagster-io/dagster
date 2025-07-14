from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, AbstractSet, Any, Callable, Optional, Union  # noqa: UP035

from toposort import CircularDependencyError

import dagster._check as check
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_checks.asset_checks_definition import has_only_asset_checks
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph, AssetNode
from dagster._core.definitions.assets.job.asset_layer import AssetLayer
from dagster._core.definitions.config import ConfigMapping
from dagster._core.definitions.dependency import (
    BlockingAssetChecksDependencyDefinition,
    DependencyDefinition,
    DependencyMapping,
    IDependencyDefinition,
    NodeHandle,
    NodeInvocation,
    NodeOutputHandle,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.executor_definition import ExecutorDefinition
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.hook_definition import HookDefinition
from dagster._core.definitions.job_definition import JobDefinition, default_job_io_manager
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.metadata import RawMetadataValue
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.partitioned_config import PartitionedConfig
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.resource_requirement import ensure_requirements_satisfied
from dagster._core.definitions.utils import DEFAULT_IO_MANAGER_KEY
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvalidSubsetError
from dagster._core.selector.subset_selector import AssetSelectionData
from dagster._core.utils import toposort
from dagster._utils.merger import merge_dicts

# Name for auto-created job that's used to materialize assets
IMPLICIT_ASSET_JOB_NAME = "__ASSET_JOB"

if TYPE_CHECKING:
    from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckSpec
    from dagster._core.definitions.run_config import RunConfig


def is_reserved_asset_job_name(name: str) -> bool:
    from dagster._core.definitions.target import ANONYMOUS_ASSET_JOB_PREFIX

    return name == IMPLICIT_ASSET_JOB_NAME or name.startswith(ANONYMOUS_ASSET_JOB_PREFIX)


def get_base_asset_job_lambda(
    asset_graph: AssetGraph,
    resource_defs: Optional[Mapping[str, ResourceDefinition]],
    executor_def: Optional[ExecutorDefinition],
    logger_defs: Optional[Mapping[str, LoggerDefinition]],
) -> Callable[[], JobDefinition]:
    def build_asset_job_lambda() -> JobDefinition:
        job_def = build_asset_job(
            name=IMPLICIT_ASSET_JOB_NAME,
            asset_graph=asset_graph,
            executor_def=executor_def,
            resource_defs=resource_defs,
            allow_different_partitions_defs=True,
        )
        job_def.validate_resource_requirements_satisfied()
        if logger_defs and not job_def.has_specified_loggers:
            job_def = job_def.with_logger_defs(logger_defs)
        return job_def

    return build_asset_job_lambda


def build_asset_job(
    name: str,
    asset_graph: AssetGraph,
    allow_different_partitions_defs: bool,
    resource_defs: Optional[Mapping[str, object]] = None,
    description: Optional[str] = None,
    config: Optional[
        Union[ConfigMapping, Mapping[str, object], PartitionedConfig, "RunConfig"]
    ] = None,
    tags: Optional[Mapping[str, str]] = None,
    run_tags: Optional[Mapping[str, str]] = None,
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
        asset_graph (AssetGraph): The asset graph that contains the assets and checks to be
            executed. Any assets in the graph that you do not wish to be executed must be
            unexecutable. You can create an AssetGraph that selects the desired executable assets
            using `get_asset_graph_job_subset`.
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
    partitions_def = _infer_and_validate_common_partitions_def(
        asset_graph,
        asset_graph.executable_asset_keys,
        required_partitions_def=partitions_def,
        allow_different_partitions_defs=allow_different_partitions_defs,
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

    asset_layer = AssetLayer.from_mapping(assets_defs_by_node_handle, asset_graph)

    all_resource_defs = get_all_resource_defs(asset_graph, wrapped_resource_defs)

    if _asset_selection_data:
        original_job = _asset_selection_data.parent_job_def
        return graph.to_job(
            resource_defs=all_resource_defs,
            config=config,
            tags=tags,
            run_tags=run_tags,
            executor_def=executor_def,
            partitions_def=partitions_def,
            asset_layer=asset_layer,
            _asset_selection_data=_asset_selection_data,
            metadata=original_job.metadata,
            logger_defs=original_job.loggers,
            hooks=original_job.hook_defs,
            op_retry_policy=original_job.op_retry_policy,
        )
    return graph.to_job(
        resource_defs=all_resource_defs,
        config=config,
        tags=tags,
        run_tags=run_tags,
        metadata=metadata,
        executor_def=executor_def,
        partitions_def=partitions_def,
        asset_layer=asset_layer,
        hooks=hooks,
        op_retry_policy=op_retry_policy,
        _asset_selection_data=_asset_selection_data,
    )


class JobScopedAssetGraph(AssetGraph):
    """An AssetGraph that is scoped to a particular job."""

    def __init__(
        self,
        asset_nodes_by_key: Mapping[AssetKey, AssetNode],
        assets_defs_by_check_key: Mapping[AssetCheckKey, AssetsDefinition],
        source_asset_graph: AssetGraph,
    ):
        super().__init__(asset_nodes_by_key, assets_defs_by_check_key)
        self._source_asset_graph = source_asset_graph

    @property
    def source_asset_graph(self) -> AssetGraph:
        """The source AssetGraph from which this job-scoped graph was created."""
        return self._source_asset_graph


def get_asset_graph_for_job(
    parent_asset_graph: AssetGraph,
    selection: AssetSelection,
    allow_different_partitions_defs: bool = False,
) -> AssetGraph:
    """Subset an AssetGraph to create an AssetGraph representing an asset job.

    The provided selection must satisfy certain constraints to comprise a valid asset job:

    - The selected keys must be a subset of the existing executable asset keys.
    - The selected keys must have at most one non-null partitions definition.

    The returned AssetGraph will contain only the selected keys within executable AssetsDefinitions.
    Any unselected dependencies will be included as unexecutable AssetsDefinitions.
    """
    from dagster._core.definitions.external_asset import (
        create_unexecutable_external_asset_from_assets_def,
    )

    selected_keys = selection.resolve(parent_asset_graph)
    invalid_keys = selected_keys - parent_asset_graph.executable_asset_keys
    if invalid_keys:
        raise DagsterInvalidDefinitionError(
            "Selected keys must be a subset of existing executable asset keys."
            f" Invalid selected keys: {invalid_keys}",
        )

    _infer_and_validate_common_partitions_def(
        parent_asset_graph,
        selected_keys,
        allow_different_partitions_defs=allow_different_partitions_defs,
    )

    selected_check_keys = selection.resolve_checks(parent_asset_graph)

    # _subset_assets_defs returns two lists of Assetsfinitions-- those included and those
    # excluded by the selection. These collections retain their original execution type. We need
    # to convert the excluded assets to unexecutable external assets.
    executable_assets_defs, excluded_assets_defs = _subset_assets_defs(
        parent_asset_graph.assets_defs, selected_keys, selected_check_keys
    )

    # Ideally we would include only the logical dependencies of our executable asset keys in our job
    # asset graph. These could be obtained by calling `AssetsDefinition.dependency_keys` for each
    # executable assets def.
    #
    # However, this is insufficient due to the way multi-asset subsetting works. Our execution
    # machinery needs the AssetNodes for any input or output asset of a multi-asset that is touched
    # by our selection, regardless of whether these assets are in our selection or their
    # dependencies. Thus for now we retrieve all of these keys with `node_keys_by_{input,output}_name`.
    # This is something we should probably fix in the future by appropriately adjusting multi-asset
    # subsets.
    other_keys = {
        *(k for ad in executable_assets_defs for k in ad.node_keys_by_input_name.values()),
        *(k for ad in executable_assets_defs for k in ad.node_keys_by_output_name.values()),
    } - selected_keys
    other_assets_defs, _ = _subset_assets_defs(
        excluded_assets_defs, other_keys, None, allow_extraneous_asset_keys=True
    )
    unexecutable_assets_defs = [
        create_unexecutable_external_asset_from_assets_def(ad) for ad in other_assets_defs
    ]

    asset_nodes_by_key, assets_defs_by_check_key = JobScopedAssetGraph.key_mappings_from_assets(
        [*executable_assets_defs, *unexecutable_assets_defs]
    )
    return JobScopedAssetGraph(asset_nodes_by_key, assets_defs_by_check_key, parent_asset_graph)


def _subset_assets_defs(
    assets: Iterable["AssetsDefinition"],
    selected_asset_keys: AbstractSet[AssetKey],
    selected_asset_check_keys: Optional[AbstractSet[AssetCheckKey]],
    allow_extraneous_asset_keys: bool = False,
) -> tuple[
    Sequence["AssetsDefinition"],
    Sequence["AssetsDefinition"],
]:
    """Given a list of asset key selection queries, generate a set of AssetsDefinition objects
    representing the included/excluded definitions.
    """
    included_assets: set[AssetsDefinition] = set()
    excluded_assets: set[AssetsDefinition] = set()

    # Do not match any assets with no keys
    for asset in set(a for a in assets if a.has_keys or a.has_check_keys):
        # intersection
        selected_subset = selected_asset_keys & asset.keys

        # if specific checks were selected, only include those
        if selected_asset_check_keys is not None:
            selected_check_subset = selected_asset_check_keys & asset.check_keys
        # if no checks were selected, filter to checks that target selected assets
        else:
            selected_check_subset = {
                key for key in asset.check_keys if key.asset_key in selected_asset_keys
            }

        # all assets in this def are selected
        if selected_subset == asset.keys and selected_check_subset == asset.check_keys:
            included_assets.add(asset)
        # no assets in this def are selected
        elif len(selected_subset) == 0 and len(selected_check_subset) == 0:
            excluded_assets.add(asset)
        elif asset.can_subset:
            # subset of the asset that we want
            subset_asset = asset.subset_for(selected_asset_keys, selected_check_subset)
            included_assets.add(subset_asset)
            # subset of the asset that we don't want
            excluded_assets.add(
                asset.subset_for(
                    selected_asset_keys=asset.keys - subset_asset.keys,
                    selected_asset_check_keys=(asset.check_keys - subset_asset.check_keys),
                )
            )
        # If the AssetsDefinition is not subsettable, include the whole definition without
        # subsetting, even though some keys are not present in our selection.
        elif allow_extraneous_asset_keys:
            included_assets.add(asset)
        else:
            raise DagsterInvalidSubsetError(
                f"When building job, the AssetsDefinition '{asset.node_def.name}' "
                f"contains asset keys {sorted(list(asset.keys))} and check keys "
                f"{sorted(list(asset.check_keys))}, but "
                f"attempted to select only assets {sorted(list(selected_subset))} and checks "
                f"{sorted(list(selected_check_subset))}. "
                "This AssetsDefinition does not support subsetting. Please select all "
                "asset and check keys produced by this asset.\n\nIf using an AssetSelection, you may "
                "use required_multi_asset_neighbors() to select any remaining assets, for "
                "example:\nAssetSelection.assets('my_asset').required_multi_asset_neighbors()"
            )

    return (
        list(included_assets),
        list(excluded_assets),
    )


def _infer_and_validate_common_partitions_def(
    asset_graph: AssetGraph,
    asset_keys: Iterable[AssetKey],
    allow_different_partitions_defs: bool,
    required_partitions_def: Optional[PartitionsDefinition] = None,
) -> Optional[PartitionsDefinition]:
    keys_by_partitions_def = defaultdict(set)
    for key in asset_keys:
        partitions_def = asset_graph.get(key).partitions_def
        if partitions_def is not None:
            if required_partitions_def is not None and partitions_def != required_partitions_def:
                raise DagsterInvalidDefinitionError(
                    f"Executable asset {key} has a different partitions definition than"
                    f" the one specified for the job. Specifed partitions definition: {required_partitions_def}."
                    f" Asset partitions definition: {partitions_def}."
                )
            keys_by_partitions_def[partitions_def].add(key)

    if len(keys_by_partitions_def) == 1:
        return next(iter(keys_by_partitions_def.keys()))
    else:
        if len(keys_by_partitions_def) > 1 and not allow_different_partitions_defs:
            keys_by_partitions_def_str = "\n".join(
                f"{partitions_def}: {asset_keys}"
                for partitions_def, asset_keys in keys_by_partitions_def.items()
            )
            raise DagsterInvalidDefinitionError(
                f"Selected assets must have the same partitions definitions, but the"
                f" selected assets have different partitions definitions: \n{keys_by_partitions_def_str}"
            )

        return None


def _get_blocking_asset_check_output_handles_by_asset_key(
    assets_defs_by_node_handle: Mapping[NodeHandle, AssetsDefinition],
) -> Mapping[AssetKey, Sequence[NodeOutputHandle]]:
    """For each asset key, returns the set of node output handles that correspond to asset check
    specs that should block the execution of downstream assets if they fail.
    """
    check_specs_by_node_output_handle: Mapping[NodeOutputHandle, AssetCheckSpec] = {}

    for node_handle, assets_def in assets_defs_by_node_handle.items():
        for output_name, check_spec in assets_def.check_specs_by_output_name.items():
            check_specs_by_node_output_handle[
                NodeOutputHandle(node_handle=node_handle, output_name=output_name)
            ] = check_spec

    blocking_asset_check_output_handles_by_asset_key: dict[AssetKey, set[NodeOutputHandle]] = (
        defaultdict(set)
    )
    for node_output_handle, check_spec in check_specs_by_node_output_handle.items():
        if check_spec.blocking:
            blocking_asset_check_output_handles_by_asset_key[check_spec.asset_key].add(
                node_output_handle
            )

    return {
        asset_key: sorted(
            blocking_asset_check_output_handles_by_asset_key[asset_key],
            key=lambda node_output_handle: node_output_handle.output_name,
        )
        for asset_key in blocking_asset_check_output_handles_by_asset_key
    }


def build_node_deps(
    asset_graph: AssetGraph,
) -> tuple[
    DependencyMapping[NodeInvocation],
    Mapping[NodeHandle, AssetsDefinition],
]:
    # sort so that nodes get a consistent name
    assets_defs = sorted(asset_graph.assets_defs, key=lambda ad: (sorted(ak for ak in ad.keys)))

    # if the same graph/op is used in multiple assets_definitions, their invocations must have
    # different names. we keep track of definitions that share a name and add a suffix to their
    # invocations to solve this issue
    collisions: dict[str, int] = {}
    assets_defs_by_node_handle: dict[NodeHandle, AssetsDefinition] = {}
    node_alias_and_output_by_asset_key: dict[AssetKey, tuple[str, str]] = {}
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

    deps: dict[NodeInvocation, dict[str, IDependencyDefinition]] = {}
    for node_handle, assets_def in assets_defs_by_node_handle.items():
        # the key that we'll use to reference the node inside this AssetsDefinition
        node_def_name = assets_def.node_def.name
        alias = node_handle.name if node_handle.name != node_def_name else None
        node_key = NodeInvocation(node_def_name, alias=alias)
        deps[node_key] = {}

        # For check-only nodes, we treat additional_deps as execution dependencies regardless
        # of if these checks are blocking or not. For other nodes, we do not treat additional_deps
        # on checks as execution dependencies.
        #
        # The precise reason for this is unknown, but this behavior must be preserved for
        # backwards compatibility for now.
        execution_dep_keys: set[AssetKey] = {
            # include the deps of all assets in this assets def
            *(
                dep.asset_key
                for key in assets_def.keys
                for dep in assets_def.get_asset_spec(key).deps
            ),
            # include the primary dep of all checks in this assets def
            # if they are not targeting a key in this assets def
            *(
                spec.asset_key
                for spec in assets_def.check_specs
                if spec.asset_key not in assets_def.keys
            ),
        }
        if has_only_asset_checks(assets_def):
            # include the additional deps of all checks in this assets def
            execution_dep_keys |= {
                dep.asset_key
                for spec in assets_def.check_specs
                for dep in spec.additional_deps
                if dep.asset_key not in assets_def.keys
            }

        inputs_map = {
            input_name: node_key
            for input_name, node_key in assets_def.node_keys_by_input_name.items()
            if node_key in execution_dep_keys
        }

        # connect each input of this AssetsDefinition to the proper upstream node
        for input_name, upstream_asset_key in inputs_map.items():
            # ignore self-deps
            if upstream_asset_key in assets_def.keys:
                continue

            # if this assets def itself performs checks on an upstream key, exempt it from being
            # blocked on other checks
            if upstream_asset_key not in {ck.asset_key for ck in assets_def.check_keys}:
                blocking_asset_check_output_handles = (
                    blocking_asset_check_output_handles_by_asset_key.get(upstream_asset_key, [])
                )
                asset_check_deps = [
                    DependencyDefinition(
                        node_output_handle.node_handle.name,
                        node_output_handle.output_name,
                    )
                    for node_output_handle in blocking_asset_check_output_handles or []
                ]
            else:
                blocking_asset_check_output_handles = []
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
        node_deps: dict[str, set[str]] = {}
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
    colors: dict[AssetKey, int] = {}

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

    color_mapping_by_assets_defs: dict[AssetsDefinition, Any] = defaultdict(
        lambda: defaultdict(set)
    )
    for key, color in colors.items():
        node = asset_graph.get(key)
        color_mapping_by_assets_defs[node.assets_def][color].add(key)

    subsetted_assets_defs: list[AssetsDefinition] = []
    for assets_def, color_mapping in color_mapping_by_assets_defs.items():
        if assets_def.is_external or len(color_mapping) == 1 or not assets_def.can_subset:
            subsetted_assets_defs.append(assets_def)
        else:
            for asset_keys in color_mapping.values():
                subsetted_assets_defs.append(
                    assets_def.subset_for(asset_keys, selected_asset_check_keys=None)
                )

    # We didn't color asset checks, so add any that are in their own node.
    assets_defs_with_only_checks = [
        ad for ad in asset_graph.assets_defs if has_only_asset_checks(ad)
    ]

    asset_nodes_by_key, assets_defs_by_check_key = JobScopedAssetGraph.key_mappings_from_assets(
        subsetted_assets_defs + assets_defs_with_only_checks
    )
    return JobScopedAssetGraph(asset_nodes_by_key, assets_defs_by_check_key, asset_graph)


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
