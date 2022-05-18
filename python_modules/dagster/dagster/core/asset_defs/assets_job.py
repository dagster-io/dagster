import itertools
import warnings
from typing import (
    AbstractSet,
    Any,
    Dict,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

import dagster._check as check
from dagster.config import Shape
from dagster.core.definitions.asset_layer import AssetLayer
from dagster.core.definitions.config import ConfigMapping
from dagster.core.definitions.decorators.op_decorator import op
from dagster.core.definitions.dependency import (
    DependencyDefinition,
    IDependencyDefinition,
    NodeHandle,
    NodeInvocation,
)
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.executor_definition import ExecutorDefinition
from dagster.core.definitions.graph_definition import GraphDefinition
from dagster.core.definitions.job_definition import JobDefinition
from dagster.core.definitions.node_definition import NodeDefinition
from dagster.core.definitions.output import Out, OutputDefinition
from dagster.core.definitions.partition import PartitionedConfig, PartitionsDefinition
from dagster.core.definitions.partition_key_range import PartitionKeyRange
from dagster.core.definitions.resource_definition import ResourceDefinition
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.execution.context.input import InputContext, build_input_context
from dagster.core.execution.context.output import build_output_context
from dagster.core.selector.subset_selector import AssetSelectionData
from dagster.core.storage.fs_asset_io_manager import fs_asset_io_manager
from dagster.core.storage.root_input_manager import RootInputManagerDefinition, root_input_manager
from dagster.utils.backcompat import ExperimentalWarning, experimental
from dagster.utils.merger import merge_dicts

from .asset_partitions import get_upstream_partitions_for_partition_range
from .assets import AssetsDefinition
from .source_asset import SourceAsset


@experimental
def build_assets_job(
    name: str,
    assets: Sequence[AssetsDefinition],
    source_assets: Optional[Sequence[Union[SourceAsset, AssetsDefinition]]] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    description: Optional[str] = None,
    config: Optional[Union[ConfigMapping, Dict[str, Any], PartitionedConfig]] = None,
    tags: Optional[Dict[str, Any]] = None,
    executor_def: Optional[ExecutorDefinition] = None,
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
    check.sequence_param(assets, "assets", of_type=AssetsDefinition)
    check.opt_sequence_param(
        source_assets, "source_assets", of_type=(SourceAsset, AssetsDefinition)
    )
    check.opt_str_param(description, "description")
    check.opt_inst_param(_asset_selection_data, "_asset_selection_data", AssetSelectionData)
    source_assets_by_key = build_source_assets_by_key(source_assets)

    deps, assets_defs_by_node_handle = build_deps(assets, source_assets_by_key.keys())
    root_manager = build_root_manager(source_assets_by_key)
    partitioned_config = build_job_partitions_from_assets(assets, source_assets or [])

    graph = GraphDefinition(
        name=name,
        node_defs=[asset.node_def for asset in assets],
        dependencies=deps,
        description=description,
        input_mappings=None,
        output_mappings=None,
        config=None,
    )

    return graph.to_job(
        resource_defs=merge_dicts(
            {"io_manager": fs_asset_io_manager}, resource_defs or {}, {"root_manager": root_manager}
        ),
        config=config or partitioned_config,
        tags=tags,
        executor_def=executor_def,
        asset_layer=AssetLayer.from_graph_and_assets_node_mapping(
            graph,
            assets_defs_by_node_handle,
        ),
        _asset_selection_data=_asset_selection_data,
    )


def build_job_partitions_from_assets(
    assets: Sequence[AssetsDefinition],
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
    assets_defs: Sequence[AssetsDefinition], source_paths: AbstractSet[AssetKey]
) -> Tuple[
    Dict[Union[str, NodeInvocation], Dict[str, IDependencyDefinition]],
    Mapping[NodeHandle, AssetsDefinition],
]:
    node_outputs_by_asset: Dict[AssetKey, Tuple[NodeDefinition, str]] = {}
    assets_defs_by_node_handle: Dict[NodeHandle, AssetsDefinition] = {}

    for assets_def in assets_defs:
        for output_name, asset_key in assets_def.asset_keys_by_output_name.items():
            if asset_key in node_outputs_by_asset:
                raise DagsterInvalidDefinitionError(
                    f"The same asset key was included for two definitions: '{asset_key.to_string()}'"
                )

            node_outputs_by_asset[asset_key] = (assets_def.node_def, output_name)

    deps: Dict[Union[str, NodeInvocation], Dict[str, IDependencyDefinition]] = {}
    # if the same graph/op is used in multiple assets_definitions, their invocations much have
    # different names. we keep track of definitions that share a name and add a suffix to their
    # invocations to solve this issue
    collisions: Dict[str, int] = {}
    for assets_def in assets_defs:
        node_name = assets_def.node_def.name
        if collisions.get(node_name):
            collisions[node_name] += 1
            alias = f"{node_name}_{collisions[node_name]}"
            node_key = NodeInvocation(node_name, alias)
        else:
            collisions[node_name] = 1
            alias = node_name
            node_key = node_name
        deps[node_key] = {}
        assets_defs_by_node_handle[NodeHandle(alias, parent=None)] = assets_def
        for input_name, asset_key in sorted(
            assets_def.asset_keys_by_input_name.items(), key=lambda input: input[0]
        ):  # sort so that input definition order is deterministic
            if asset_key in node_outputs_by_asset:
                node_def, output_name = node_outputs_by_asset[asset_key]
                deps[node_key][input_name] = DependencyDefinition(node_def.name, output_name)
            elif asset_key not in source_paths:
                input_def = assets_def.node_def.input_def_named(input_name)
                if not input_def.dagster_type.is_nothing:
                    raise DagsterInvalidDefinitionError(
                        f"Input asset '{asset_key.to_string()}' for asset "
                        f"'{next(iter(assets_def.asset_keys)).to_string()}' is not "
                        "produced by any of the provided asset ops and is not one of the provided "
                        "sources"
                    )

    return deps, assets_defs_by_node_handle


def build_root_manager(
    source_assets_by_key: Mapping[AssetKey, Union[SourceAsset, OutputDefinition]]
) -> RootInputManagerDefinition:
    source_asset_io_manager_keys = {
        source_asset.io_manager_key for source_asset in source_assets_by_key.values()
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=ExperimentalWarning)

        @root_input_manager(required_resource_keys=source_asset_io_manager_keys)
        def _root_manager(input_context: InputContext) -> Any:
            source_asset_key = cast(AssetKey, input_context.asset_key)
            source_asset = source_assets_by_key.get(source_asset_key)
            if not source_asset:
                return None
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=ExperimentalWarning)

                @op(out={source_asset_key.path[-1]: Out(asset_key=source_asset_key)})
                def _op():
                    pass

            step_context = input_context.step_context
            resource_config = step_context.resolved_run_config.resources[
                source_asset.io_manager_key
            ].config
            io_manager_def = (
                step_context.pipeline.get_definition()
                .mode_definitions[0]
                .resource_defs[source_asset.io_manager_key]
            )
            resources = step_context.scoped_resources_builder.build(
                io_manager_def.required_resource_keys
            )

            output_context = build_output_context(
                name=source_asset_key.path[-1],
                step_key="none",
                solid_def=_op,
                metadata=cast(Dict[str, Any], source_asset.metadata),
                resource_config=resource_config,
                resources=cast(NamedTuple, resources)._asdict(),
                asset_key=source_asset_key,
            )
            input_context_with_upstream = build_input_context(
                name=input_context.name,
                metadata=input_context.metadata,
                config=input_context.config,
                dagster_type=input_context.dagster_type,
                upstream_output=output_context,
                op_def=input_context.op_def,
                step_context=input_context.step_context,
                resource_config=resource_config,
                resources=cast(NamedTuple, resources)._asdict(),
            )

            io_manager = getattr(cast(Any, input_context.resources), source_asset.io_manager_key)
            return io_manager.load_input(input_context_with_upstream)

    return _root_manager
