from .source_asset import SourceAsset
from .assets import AssetsDefinition
from ..definitions.asset_layer import build_asset_selection_job
from typing import List, Optional, Any, Mapping, Sequence
from ..execution.execute_in_process_result import ExecuteInProcessResult
from ..definitions import ResourceDefinition


def materialize(
    assets: Sequence[AssetsDefinition],
    source_assets: Optional[Sequence[SourceAsset]],
    selection: Optional[Union[str, List[str]]] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    run_config: Any = None,
) -> ExecuteInProcessResult:
    """
    Executes an in-process run which materializes assets that fulfill selection.

    Args:
        assets (Sequence[AssetsDefinition]): The assets from which to choose what to materialize.
        source_assets (Optional[Sequence[SourceAsset]]):
            Assets that will not be materialized by this call, but that the assets in this call depend upon.
        selection (Optional[Union[str, List[str]]]):
            A single selection query or list of selection queries
            to for assets in the provided list. If no selection is provided,
            every asset in the list will be materialized. For example:

                - ``['some_asset_key']`` select ``some_asset_key`` itself.
                - ``['*some_asset_key']`` select ``some_asset_key`` and all its ancestors (upstream dependencies).
                - ``['*some_asset_key+++']`` select ``some_asset_key``, all its ancestors, and its descendants (downstream dependencies) within 3 levels down.
                - ``['*some_asset_key', 'other_asset_key_a', 'other_asset_key_b+']`` select ``some_asset_key`` and all its ancestors, ``other_asset_key_a`` itself, and ``other_asset_key_b`` and its direct child asset keys. When subselecting into a multi-asset, all of the asset keys in that multi-asset must be selected.
        run_config (Optional[Any]): The run config to use for the run that materializes the assets.
        resource_defs (Optional[Mapping[str, ResourceDefinition]]):
            Resource definitions that satisfy resource requirements of each
            provided asset or source asset. If a key is present on both an
            asset and the provided resource_defs dictionary, the resource on
            the asset will take precedent.

    Returns:
        ExecuteInProcessResult: The result of the execution.
    """

    return build_assets_job(
        "in_process_materialization_job",
        assets=assets,
        source_assets=source_assets,
        resource_defs=resource_defs,
        selection=selection,
    ).execute_in_process(run_config=run_config)
