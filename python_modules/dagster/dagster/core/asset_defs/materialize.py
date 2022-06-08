from typing import Any, List, Mapping, Optional, Sequence

import dagster._check as check

from ..definitions import ResourceDefinition
from ..execution.execute_in_process_result import ExecuteInProcessResult
from ..execution.with_resources import with_resources
from ..instance import DagsterInstance
from ..storage.fs_io_manager import fs_io_manager
from .assets import AssetsDefinition
from .assets_job import build_assets_job
from .source_asset import SourceAsset


def materialize(
    assets: Sequence[AssetsDefinition],
    source_assets: Optional[Sequence[SourceAsset]] = None,
    run_config: Any = None,
    instance: Optional[DagsterInstance] = None,
) -> ExecuteInProcessResult:
    """
    Executes an in-process run which materializes assets that fulfill selection.

    Args:
        assets (Sequence[AssetsDefinition]): The assets from which to choose what to materialize.
        source_assets (Optional[Sequence[SourceAsset]]):
            Assets that will not be materialized by this call, but that the assets in this call depend upon.
        run_config (Optional[Any]): The run config to use for the run that materializes the assets.

    Returns:
        ExecuteInProcessResult: The result of the execution.
    """

    assets = check.sequence_param(assets, "assets")
    source_assets = check.opt_sequence_param(source_assets, "source_assets")
    instance = check.opt_inst_param(instance, "instance", DagsterInstance)
    assets = with_resources(assets, {"io_manager": fs_io_manager})
    source_assets = with_resources(source_assets, {"io_manager": fs_io_manager})

    return build_assets_job(
        "in_process_materialization_job",
        assets=assets,
        source_assets=source_assets,
    ).execute_in_process(run_config=run_config, instance=instance)
