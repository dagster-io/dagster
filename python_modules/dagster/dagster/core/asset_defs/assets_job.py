from typing import AbstractSet, Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union, cast

from dagster import check
from dagster.core.definitions.decorators.solid import solid
from dagster.core.definitions.dependency import (
    DependencyDefinition,
    IDependencyDefinition,
    SolidInvocation,
)
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.graph import GraphDefinition
from dagster.core.definitions.i_solid_definition import NodeDefinition
from dagster.core.definitions.input import InputDefinition
from dagster.core.definitions.output import OutputDefinition
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.definitions.resource import ResourceDefinition
from dagster.core.definitions.solid import SolidDefinition
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.execution.context.input import InputContext, build_input_context
from dagster.core.execution.context.output import build_output_context
from dagster.core.storage.root_input_manager import RootInputManagerDefinition, root_input_manager
from dagster.utils.merger import merge_dicts

from .foreign_asset import ForeignAsset


def build_assets_job(
    name: str,
    assets: List[NodeDefinition],
    source_assets: Optional[Sequence[Union[ForeignAsset, SolidDefinition]]] = None,
    resource_defs: Optional[Dict[str, ResourceDefinition]] = None,
    description: Optional[str] = None,
) -> PipelineDefinition:
    """Builds a job that materializes the given assets.

    The dependencies between the nodes in the job are determined by the asset dependencies defined
    in the metadata on the provided asset nodes.

    Args:
        name (str): The name of the job.
        assets (List[NodeDefinition]): A list of ops or graphs that are assets.
        source_assets (Optional[Sequence[Union[ForeignAsset, SolidDefinition]]]): A list of assets
            that are not materialized by this job, but that assets in this job depend on.
        resource_defs (Optional[Dict[str, ResourceDefinition]]): Resource defs to be included in
            this job.
        description (Optional[str]): A description of the job.

    Returns:
        PipelineDefinition: A job that materializes the given assets.
    """
    check.str_param(name, "name")
    check.list_param(assets, "assets", of_type=NodeDefinition)
    check.opt_list_param(source_assets, "source_assets", of_type=(ForeignAsset, SolidDefinition))
    check.opt_str_param(description, "description")
    source_assets_by_key = build_source_assets_by_key(source_assets)

    solid_deps = build_solid_deps(assets, source_assets_by_key.keys())
    root_manager = build_root_manager(source_assets_by_key)

    return GraphDefinition(
        name=name,
        node_defs=assets,
        dependencies=solid_deps,
        description=description,
        input_mappings=None,
        output_mappings=None,
        config_mapping=None,
    ).to_job(resource_defs=merge_dicts(resource_defs or {}, {"root_manager": root_manager}))


def build_source_assets_by_key(
    source_assets: Optional[Sequence[Union[ForeignAsset, SolidDefinition]]]
) -> Mapping[AssetKey, Union[ForeignAsset, OutputDefinition]]:
    source_assets_by_key: Dict[AssetKey, Union[ForeignAsset, OutputDefinition]] = {}
    for asset_source in source_assets or []:
        if isinstance(asset_source, ForeignAsset):
            source_assets_by_key[asset_source.key] = asset_source
        elif isinstance(asset_source, SolidDefinition):
            for output_def in asset_source.output_defs:
                if output_def.get_asset_key(None):
                    source_assets_by_key[output_def.get_asset_key(None)] = output_def

    return source_assets_by_key


def build_solid_deps(
    assets: List[NodeDefinition], source_paths: AbstractSet[Tuple[str]]
) -> Dict[Union[str, SolidInvocation], Dict[str, IDependencyDefinition]]:
    solids_by_logical_asset: Dict[AssetKey, NodeDefinition] = {}
    for solid in assets:
        n_outputs = len(solid.output_defs)
        if len(solid.output_defs) != 1:
            raise DagsterInvalidDefinitionError(
                f"Assets must have exactly one output, but '{solid.name}' has {n_outputs}"
            )

        output_def = solid.output_defs[0]
        logical_asset = get_asset_key(output_def, f"Output of asset '{solid.name}'")

        if logical_asset in solids_by_logical_asset:
            prev_solid = solids_by_logical_asset[logical_asset].name
            raise DagsterInvalidDefinitionError(
                f"Two solids produce the same logical asset: '{solid.name}' and '{prev_solid.name}"
            )

        solids_by_logical_asset[logical_asset] = solid

    solid_deps: Dict[Union[str, SolidInvocation], Dict[str, IDependencyDefinition]] = {}
    for solid in assets:
        solid_deps[solid.name] = {}
        for input_def in solid.input_defs:
            logical_asset = get_asset_key(
                input_def, f"Input '{input_def.name}' of asset '{solid.name}'"
            )

            if logical_asset in solids_by_logical_asset:
                solid_deps[solid.name][input_def.name] = DependencyDefinition(
                    solids_by_logical_asset[logical_asset].name, "result"
                )
            elif logical_asset not in source_paths:
                raise DagsterInvalidDefinitionError(
                    f"Logical input asset '{logical_asset}' for asset '{solid.name}' is not "
                    "produced by any of the provided asset solids and is not one of the provided "
                    "sources"
                )

    return solid_deps


def build_root_manager(
    source_assets_by_key: Mapping[AssetKey, Union[ForeignAsset, OutputDefinition]]
) -> RootInputManagerDefinition:
    source_asset_io_manager_keys = {
        source_asset.io_manager_key for source_asset in source_assets_by_key.values()
    }

    @root_input_manager(required_resource_keys=source_asset_io_manager_keys)
    def _root_manager(input_context: InputContext) -> Any:
        source_asset_key = cast(AssetKey, input_context.asset_key)
        source_asset = source_assets_by_key[source_asset_key]

        @solid(
            output_defs=[
                OutputDefinition(name=source_asset_key.path[-1], asset_key=source_asset_key)
            ]
        )
        def _solid():
            pass

        output_context = build_output_context(
            name=source_asset_key.path[-1],
            step_key="none",
            solid_def=_solid,
            metadata=merge_dicts(
                source_asset.metadata or {}, {"logical_asset_key": source_asset_key}
            ),
        )
        input_context_with_upstream = build_input_context(
            name=input_context.name,
            metadata=input_context.metadata,
            config=input_context.config,
            dagster_type=input_context.dagster_type,
            upstream_output=output_context,
        )

        io_manager = getattr(cast(Any, input_context.resources), source_asset.io_manager_key)
        return io_manager.load_input(input_context_with_upstream)

    return _root_manager


def get_asset_key(
    input_or_output: Union[InputDefinition, OutputDefinition], error_prefix: str
) -> AssetKey:
    asset_key = input_or_output.get_asset_key(None)
    if asset_key is None:
        raise DagsterInvalidDefinitionError(f"{error_prefix}' is missing asset_key")
    else:
        return asset_key
