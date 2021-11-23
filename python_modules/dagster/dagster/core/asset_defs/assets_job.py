from typing import AbstractSet, Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union, cast

from dagster import check
from dagster.core.definitions.config import ConfigMapping
from dagster.core.definitions.decorators.op import op
from dagster.core.definitions.dependency import (
    DependencyDefinition,
    IDependencyDefinition,
    NodeInvocation,
)
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.executor_definition import ExecutorDefinition
from dagster.core.definitions.graph_definition import GraphDefinition
from dagster.core.definitions.job_definition import JobDefinition
from dagster.core.definitions.op_definition import OpDefinition
from dagster.core.definitions.output import Out, OutputDefinition
from dagster.core.definitions.partition import PartitionedConfig
from dagster.core.definitions.resource_definition import ResourceDefinition
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.execution.context.input import InputContext, build_input_context
from dagster.core.execution.context.output import build_output_context
from dagster.core.storage.root_input_manager import RootInputManagerDefinition, root_input_manager
from dagster.utils.backcompat import experimental
from dagster.utils.merger import merge_dicts

from .asset import AssetsDefinition
from .foreign_asset import ForeignAsset


@experimental
def build_assets_job(
    name: str,
    assets: List[AssetsDefinition],
    source_assets: Optional[Sequence[Union[ForeignAsset, AssetsDefinition]]] = None,
    resource_defs: Optional[Dict[str, ResourceDefinition]] = None,
    description: Optional[str] = None,
    config: Union[ConfigMapping, Dict[str, Any], PartitionedConfig] = None,
    tags: Optional[Dict[str, Any]] = None,
    executor_def: Optional[ExecutorDefinition] = None,
) -> JobDefinition:
    """Builds a job that materializes the given assets.

    The dependencies between the ops in the job are determined by the asset dependencies defined
    in the metadata on the provided asset nodes.

    Args:
        name (str): The name of the job.
        assets (List[AssetsDefinition]): A list of assets or
            multi-assets - usually constructed using the :py:func:`@asset` or :py:func:`@multi_asset`
            decorator.
        source_assets (Optional[Sequence[Union[ForeignAsset, AssetsDefinition]]]): A list of
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
    check.list_param(assets, "assets", of_type=AssetsDefinition)
    check.opt_list_param(source_assets, "source_assets", of_type=(ForeignAsset, AssetsDefinition))
    check.opt_str_param(description, "description")
    source_assets_by_key = build_source_assets_by_key(source_assets)

    op_defs = build_op_deps(assets, source_assets_by_key.keys())
    root_manager = build_root_manager(source_assets_by_key)

    return GraphDefinition(
        name=name,
        node_defs=[asset.op for asset in assets],
        dependencies=op_defs,
        description=description,
        input_mappings=None,
        output_mappings=None,
        config=None,
    ).to_job(
        resource_defs=merge_dicts(resource_defs or {}, {"root_manager": root_manager}),
        config=config,
        tags=tags,
        executor_def=executor_def,
    )


def build_source_assets_by_key(
    source_assets: Optional[Sequence[Union[ForeignAsset, AssetsDefinition]]]
) -> Mapping[AssetKey, Union[ForeignAsset, OutputDefinition]]:
    source_assets_by_key: Dict[AssetKey, Union[ForeignAsset, OutputDefinition]] = {}
    for asset_source in source_assets or []:
        if isinstance(asset_source, ForeignAsset):
            source_assets_by_key[asset_source.key] = asset_source
        elif isinstance(asset_source, AssetsDefinition):
            for asset_key, output_def in asset_source.output_defs_by_asset_key.items():
                if asset_key:
                    source_assets_by_key[asset_key] = output_def

    return source_assets_by_key


def build_op_deps(
    multi_asset_defs: List[AssetsDefinition], source_paths: AbstractSet[AssetKey]
) -> Dict[Union[str, NodeInvocation], Dict[str, IDependencyDefinition]]:
    op_outputs_by_asset: Dict[AssetKey, Tuple[OpDefinition, str]] = {}
    for multi_asset_def in multi_asset_defs:
        for asset_key, output_def in multi_asset_def.output_defs_by_asset_key.items():
            if asset_key in op_outputs_by_asset:
                raise DagsterInvalidDefinitionError(
                    f"The same asset key was included for two definitions: '{asset_key.to_string()}'"
                )

            op_outputs_by_asset[asset_key] = (multi_asset_def.op, output_def.name)

    op_deps: Dict[Union[str, NodeInvocation], Dict[str, IDependencyDefinition]] = {}
    for multi_asset_def in multi_asset_defs:
        op_name = multi_asset_def.op.name
        op_deps[op_name] = {}
        for asset_key, input_def in multi_asset_def.input_defs_by_asset_key.items():
            if asset_key in op_outputs_by_asset:
                op_def, output_name = op_outputs_by_asset[asset_key]
                op_deps[op_name][input_def.name] = DependencyDefinition(op_def.name, output_name)
            elif asset_key not in source_paths and not input_def.dagster_type.is_nothing:
                raise DagsterInvalidDefinitionError(
                    f"Input asset '{asset_key.to_string()}' for asset '{op_name}' is not "
                    "produced by any of the provided asset ops and is not one of the provided "
                    "sources"
                )

    return op_deps


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

        @op(out={source_asset_key.path[-1]: Out(asset_key=source_asset_key)})
        def _op():
            pass

        output_context = build_output_context(
            name=source_asset_key.path[-1],
            step_key="none",
            solid_def=_op,
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
            op_def=input_context.op_def,
        )

        io_manager = getattr(cast(Any, input_context.resources), source_asset.io_manager_key)
        return io_manager.load_input(input_context_with_upstream)

    return _root_manager
