import itertools
from collections import defaultdict
from typing import (
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
    cast,
)

from toposort import CircularDependencyError, toposort

import dagster._check as check
from dagster.config import Shape
from dagster.core.definitions.asset_layer import AssetLayer
from dagster.core.definitions.config import ConfigMapping
from dagster.core.definitions.dependency import (
    DependencyDefinition,
    IDependencyDefinition,
    NodeHandle,
    NodeInvocation,
)
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.executor_definition import ExecutorDefinition
from dagster.core.definitions.graph_definition import GraphDefinition, default_job_io_manager
from dagster.core.definitions.job_definition import JobDefinition
from dagster.core.definitions.output import OutputDefinition
from dagster.core.definitions.partition import PartitionedConfig, PartitionsDefinition
from dagster.core.definitions.partition_key_range import PartitionKeyRange
from dagster.core.definitions.resource_definition import ResourceDefinition
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.execution.with_resources import with_resources
from dagster.core.selector.subset_selector import AssetSelectionData
from dagster.utils import merge_dicts
from dagster.utils.backcompat import experimental

from .asset_partitions import get_upstream_partitions_for_partition_range
from .assets import AssetsDefinition
from .source_asset import SourceAsset


@experimental
def build_assets_job(
    name: str,
    assets: Iterable[AssetsDefinition],
    source_assets: Optional[Sequence[Union[SourceAsset, AssetsDefinition]]] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    description: Optional[str] = None,
    config: Optional[Union[ConfigMapping, Dict[str, Any], PartitionedConfig]] = None,
    tags: Optional[Dict[str, Any]] = None,
    executor_def: Optional[ExecutorDefinition] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    _asset_selection_data: Optional[AssetSelectionData] = None,
) -> JobDefinition:
    """Builds a job that materializes the given assets.

    The dependencies between the ops in the job are determined by the asset dependencies defined
    in the metadata on the provided asset nodes.

    Args:
        name (str): The name of the job.
        assets (List[AssetsDefinition]): A list of assets or
            multi-assets - usually constructed using the :py:func:`@asset` or :py:func:`@multi_asset`
            decorator.
        source_assets (Optional[Sequence[Union[SourceAsset, AssetsDefinition]]]): A list of
            assets that are not materialized by this job, but that assets in this job depend on.
        resource_defs (Optional[Dict[str, ResourceDefinition]]): Resource defs to be included in
            this job.
        description (Optional[str]): A description of the job.

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

    check.str_param(name, "name")
    check.iterable_param(assets, "assets", of_type=AssetsDefinition)
    source_assets = check.opt_sequence_param(
        source_assets, "source_assets", of_type=(SourceAsset, AssetsDefinition)
    )
    check.opt_str_param(description, "description")
    check.opt_inst_param(_asset_selection_data, "_asset_selection_data", AssetSelectionData)
    resource_defs = check.opt_mapping_param(resource_defs, "resource_defs")
    resource_defs = merge_dicts({"io_manager": default_job_io_manager}, resource_defs)

    assets = with_resources(assets, resource_defs)
    source_assets = with_resources(source_assets, resource_defs)

    source_assets_by_key = build_source_assets_by_key(source_assets)

    partitioned_config = build_job_partitions_from_assets(assets, source_assets or [])

    deps, assets_defs_by_node_handle = build_deps(assets, source_assets_by_key.keys())
    # attempt to resolve cycles using multi-asset subsetting
    if _has_cycles(deps):
        assets = _attempt_resolve_cycles(assets)
        deps, assets_defs_by_node_handle = build_deps(assets, source_assets_by_key.keys())

    graph = GraphDefinition(
        name=name,
        node_defs=[asset.node_def for asset in assets],
        dependencies=deps,
        description=description,
        input_mappings=None,
        output_mappings=None,
        config=None,
    )

    # turn any AssetsDefinitions into SourceAssets
    resolved_source_assets: List[SourceAsset] = []
    for asset in source_assets or []:
        if isinstance(asset, AssetsDefinition):
            resolved_source_assets += asset.to_source_assets()
        elif isinstance(asset, SourceAsset):
            resolved_source_assets.append(asset)

    asset_layer = AssetLayer.from_graph_and_assets_node_mapping(
        graph, assets_defs_by_node_handle, resolved_source_assets
    )

    all_resource_defs = get_all_resource_defs(assets, resolved_source_assets)

    return graph.to_job(
        resource_defs=all_resource_defs,
        config=config,
        tags=tags,
        executor_def=executor_def,
        partitions_def=partitions_def,
        asset_layer=asset_layer,
        _asset_selection_data=_asset_selection_data,
    )


def build_job_partitions_from_assets(
    assets: Iterable[AssetsDefinition],
    source_assets: Sequence[Union[SourceAsset, AssetsDefinition]],
) -> Optional[PartitionedConfig]:
    assets_with_partitions_defs = [assets_def for assets_def in assets if assets_def.partitions_def]

    if len(assets_with_partitions_defs) == 0:
        return None

    first_assets_with_partitions_def: AssetsDefinition = assets_with_partitions_defs[0]
    for assets_def in assets_with_partitions_defs:
        if assets_def.partitions_def != first_assets_with_partitions_def.partitions_def:
            first_asset_key = next(iter(assets_def.asset_keys)).to_string()
            second_asset_key = next(iter(first_assets_with_partitions_def.asset_keys)).to_string()
            raise DagsterInvalidDefinitionError(
                "When an assets job contains multiple partitions assets, they must have the "
                f"same partitions definitions, but asset '{first_asset_key}' and asset "
                f"'{second_asset_key}' have different partitions definitions. "
            )

    partitions_defs_by_asset_key: Dict[AssetKey, PartitionsDefinition] = {}
    asset: Union[AssetsDefinition, SourceAsset]
    for asset in itertools.chain.from_iterable([assets, source_assets]):
        if isinstance(asset, AssetsDefinition) and asset.partitions_def is not None:
            for asset_key in asset.asset_keys:
                partitions_defs_by_asset_key[asset_key] = asset.partitions_def
        elif isinstance(asset, SourceAsset) and asset.partitions_def is not None:
            partitions_defs_by_asset_key[asset.key] = asset.partitions_def

    def asset_partitions_for_job_partition(
        job_partition_key: str,
    ) -> Mapping[AssetKey, PartitionKeyRange]:
        return {
            asset_key: PartitionKeyRange(job_partition_key, job_partition_key)
            for assets_def in assets
            for asset_key in assets_def.asset_keys
            if assets_def.partitions_def
        }

    def run_config_for_partition_fn(partition_key: str) -> Dict[str, Any]:
        ops_config: Dict[str, Any] = {}
        asset_partitions_by_asset_key = asset_partitions_for_job_partition(partition_key)

        for assets_def in assets:
            outputs_dict: Dict[str, Dict[str, Any]] = {}
            if assets_def.partitions_def is not None:
                for output_name, asset_key in assets_def.asset_keys_by_output_name.items():
                    asset_partition_key_range = asset_partitions_by_asset_key[asset_key]
                    outputs_dict[output_name] = {
                        "start": asset_partition_key_range.start,
                        "end": asset_partition_key_range.end,
                    }

            inputs_dict: Dict[str, Dict[str, Any]] = {}
            for input_name, in_asset_key in assets_def.asset_keys_by_input_name.items():
                upstream_partitions_def = partitions_defs_by_asset_key.get(in_asset_key)
                if assets_def.partitions_def is not None and upstream_partitions_def is not None:
                    upstream_partition_key_range = get_upstream_partitions_for_partition_range(
                        assets_def, upstream_partitions_def, in_asset_key, asset_partition_key_range
                    )
                    inputs_dict[input_name] = {
                        "start": upstream_partition_key_range.start,
                        "end": upstream_partition_key_range.end,
                    }

            config_schema = assets_def.node_def.config_schema
            if (
                config_schema
                and isinstance(config_schema.config_type, Shape)
                and "assets" in config_schema.config_type.fields
            ):
                ops_config[assets_def.node_def.name] = {
                    "config": {
                        "assets": {
                            "input_partitions": inputs_dict,
                            "output_partitions": outputs_dict,
                        }
                    }
                }

        return {"ops": ops_config}

    return PartitionedConfig(
        partitions_def=cast(PartitionsDefinition, first_assets_with_partitions_def.partitions_def),
        run_config_for_partition_fn=lambda p: run_config_for_partition_fn(p.name),
    )


def build_source_assets_by_key(
    source_assets: Optional[Sequence[Union[SourceAsset, AssetsDefinition]]]
) -> Mapping[AssetKey, Union[SourceAsset, OutputDefinition]]:
    source_assets_by_key: Dict[AssetKey, Union[SourceAsset, OutputDefinition]] = {}
    for asset_source in source_assets or []:
        if isinstance(asset_source, SourceAsset):
            source_assets_by_key[asset_source.key] = asset_source
        elif isinstance(asset_source, AssetsDefinition):
            for output_name, asset_key in asset_source.asset_keys_by_output_name.items():
                if asset_key:
                    source_assets_by_key[asset_key] = asset_source.node_def.output_def_named(
                        output_name
                    )

    return source_assets_by_key


def build_deps(
    assets_defs: Iterable[AssetsDefinition], source_paths: AbstractSet[AssetKey]
) -> Tuple[
    Dict[Union[str, NodeInvocation], Dict[str, IDependencyDefinition]],
    Mapping[NodeHandle, AssetsDefinition],
]:
    # sort so that nodes get a consistent name
    assets_defs = sorted(assets_defs, key=lambda ad: (sorted((ak for ak in ad.asset_keys))))

    # if the same graph/op is used in multiple assets_definitions, their invocations must have
    # different names. we keep track of definitions that share a name and add a suffix to their
    # invocations to solve this issue
    collisions: Dict[str, int] = {}
    assets_defs_by_node_handle: Dict[NodeHandle, AssetsDefinition] = {}
    node_alias_and_output_by_asset_key: Dict[AssetKey, Tuple[str, str]] = {}
    for assets_def in assets_defs:
        node_name = assets_def.node_def.name
        if collisions.get(node_name):
            collisions[node_name] += 1
            node_alias = f"{node_name}_{collisions[node_name]}"
        else:
            collisions[node_name] = 1
            node_alias = node_name

        # unique handle for each AssetsDefinition
        assets_defs_by_node_handle[NodeHandle(node_alias, parent=None)] = assets_def
        for output_name, key in assets_def.asset_keys_by_output_name.items():
            node_alias_and_output_by_asset_key[key] = (node_alias, output_name)

    deps: Dict[Union[str, NodeInvocation], Dict[str, IDependencyDefinition]] = {}
    for node_handle, assets_def in assets_defs_by_node_handle.items():
        # the key that we'll use to reference the node inside this AssetsDefinition
        node_def_name = assets_def.node_def.name
        if node_handle.name != node_def_name:
            node_key = NodeInvocation(node_def_name, alias=node_handle.name)
        else:
            node_key = node_def_name
        deps[node_key] = {}

        # connect each input of this AssetsDefinition to the proper upstream node
        for input_name, upstream_asset_key in assets_def.asset_keys_by_input_name.items():
            if upstream_asset_key in node_alias_and_output_by_asset_key:
                upstream_node_alias, upstream_output_name = node_alias_and_output_by_asset_key[
                    upstream_asset_key
                ]
                deps[node_key][input_name] = DependencyDefinition(
                    upstream_node_alias, upstream_output_name
                )
            elif upstream_asset_key not in source_paths:
                input_def = assets_def.node_def.input_def_named(input_name)
                if not input_def.dagster_type.is_nothing:
                    raise DagsterInvalidDefinitionError(
                        f"Input asset '{upstream_asset_key.to_string()}' for asset "
                        f"'{next(iter(assets_def.asset_keys)).to_string()}' is not "
                        "produced by any of the provided asset ops and is not one of the provided "
                        "sources"
                    )

    return deps, assets_defs_by_node_handle


def _has_cycles(deps: Dict[Union[str, NodeInvocation], Dict[str, IDependencyDefinition]]) -> bool:
    """Detect if there are cycles in a dependency dictionary."""
    try:
        node_deps: Dict[Union[str, NodeInvocation], Set[str]] = {}
        for upstream_node, downstream_deps in deps.items():
            node_deps[upstream_node] = set()
            for dep in downstream_deps.values():
                if isinstance(dep, DependencyDefinition):
                    node_deps[upstream_node].add(dep.node)
                else:
                    check.failed(f"Unexpected dependency type {type(dep)}.")
        # make sure that there is a valid topological sorting of these node dependencies
        list(toposort(node_deps))
        return False
    # only try to resolve cycles if we have a cycle
    except CircularDependencyError:
        return True


def _attempt_resolve_cycles(
    assets_defs: Iterable["AssetsDefinition"],
) -> Sequence["AssetsDefinition"]:
    """
    DFS starting at root nodes to color the asset dependency graph. Each time you leave your
    current AssetsDefinition, the color increments.

    At the end of this process, we'll have a coloring for the asset graph such that any asset which
    is downstream of another asset via a different AssetsDefinition will be guaranteed to have
    a different (greater) color.

    Once we have our coloring, if any AssetsDefinition contains assets with different colors,
    we split that AssetsDefinition into a subset for each individual color.

    This ensures that no asset that shares a node with another asset will be downstream of
    that asset via a different node (i.e. there will be no cycles).
    """
    from dagster.core.selector.subset_selector import generate_asset_dep_graph

    # get asset dependencies
    asset_deps = generate_asset_dep_graph(assets_defs)

    # index AssetsDefinitions by their asset names
    assets_defs_by_asset_name = {}
    for assets_def in assets_defs:
        for asset_key in assets_def.asset_keys:
            assets_defs_by_asset_name[asset_key.to_user_string()] = assets_def

    # color for each asset
    colors = {}

    # recursively color an asset and all of its downstream assets
    def _dfs(name, cur_color):
        colors[name] = cur_color
        if name in assets_defs_by_asset_name:
            cur_node_asset_keys = assets_defs_by_asset_name[name].asset_keys
        else:
            # in a SourceAsset, treat all downstream as if they're in the same node
            cur_node_asset_keys = asset_deps["downstream"][name]

        for downstream_name in asset_deps["downstream"][name]:
            # if the downstream asset is in the current node,keep the same color
            if AssetKey.from_user_string(downstream_name) in cur_node_asset_keys:
                new_color = cur_color
            else:
                new_color = cur_color + 1

            # if current color of the downstream asset is less than the new color, re-do dfs
            if colors.get(downstream_name, -1) < new_color:
                _dfs(downstream_name, new_color)

    # validate that there are no cycles in the overall asset graph
    toposorted = list(toposort(asset_deps["upstream"]))

    # dfs for each root node
    for root_name in toposorted[0]:
        _dfs(root_name, 0)

    color_mapping_by_assets_defs: Dict[AssetsDefinition, Any] = defaultdict(
        lambda: defaultdict(set)
    )
    for name, color in colors.items():
        asset_key = AssetKey.from_user_string(name)
        # ignore source assets
        if name not in assets_defs_by_asset_name:
            continue
        color_mapping_by_assets_defs[assets_defs_by_asset_name[name]][color].add(
            AssetKey.from_user_string(name)
        )

    ret = []
    for assets_def, color_mapping in color_mapping_by_assets_defs.items():
        if len(color_mapping) == 1 or not assets_def.can_subset:
            ret.append(assets_def)
        else:
            for asset_keys in color_mapping.values():
                ret.append(assets_def.subset_for(asset_keys))

    return ret


def get_all_resource_defs(
    assets: Sequence[AssetsDefinition], source_assets: Sequence[SourceAsset]
) -> Dict[str, ResourceDefinition]:
    all_resource_defs = {}
    all_assets: Sequence[Union[AssetsDefinition, SourceAsset]] = [*assets, *source_assets]
    for asset in all_assets:
        for resource_key, resource_def in asset.resource_defs.items():
            if resource_key not in all_resource_defs:
                all_resource_defs[resource_key] = resource_def
            if all_resource_defs[resource_key] != resource_def:
                raise DagsterInvalidDefinitionError(
                    f"Conflicting versions of resource with key '{resource_key}' "
                    "were provided to different assets. When constructing a "
                    "job, all resource definitions provided to assets must "
                    "match by reference equality for a given key."
                )
    return all_resource_defs
