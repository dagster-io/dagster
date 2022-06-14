from typing import Any, Mapping, Optional, Sequence, Union

import dagster._check as check

from ..execution.build_resources import wrap_resources_for_execution
from ..execution.execute_in_process_result import ExecuteInProcessResult
from ..execution.with_resources import with_resources
from ..instance import DagsterInstance
from ..storage.fs_io_manager import fs_io_manager
from .assets import AssetsDefinition
from .assets_job import build_assets_job
from .source_asset import SourceAsset


def materialize(
    assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    run_config: Any = None,
    instance: Optional[DagsterInstance] = None,
) -> ExecuteInProcessResult:
    """
    Executes a single-threaded, in-process run which materializes provided assets.

    By default, will materialize assets to the local filesystem.

    Args:
        assets (Sequence[Union[AssetsDefinition, SourceAsset]]):
            The assets to materialize. Can also provide :py:class:`SourceAsset` objects to fill dependencies for asset defs.
        run_config (Optional[Any]): The run config to use for the run that materializes the assets.

    Returns:
        ExecuteInProcessResult: The result of the execution.
    """

    assets = check.sequence_param(assets, "assets", of_type=(AssetsDefinition, SourceAsset))
    assets = with_resources(assets, {"io_manager": fs_io_manager})
    assets_defs = [the_def for the_def in assets if isinstance(the_def, AssetsDefinition)]
    source_assets = [the_def for the_def in assets if isinstance(the_def, SourceAsset)]
    instance = check.opt_inst_param(instance, "instance", DagsterInstance)

    return build_assets_job(
        "in_process_materialization_job",
        assets=assets_defs,
        source_assets=source_assets,
    ).execute_in_process(run_config=run_config, instance=instance)


def materialize_to_memory(
    assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    run_config: Any = None,
    instance: Optional[DagsterInstance] = None,
    resources: Optional[Mapping[str, object]] = None,
) -> ExecuteInProcessResult:
    """
    Executes a single-threaded, in-process run which materializes provided assets.

    By default, will materialize assets to memory, meaning results will not be
    persisted. This behavior can be changed by overriding the default io
    manager key "io_manager", or providing custom io manager keys to assets.

    Args:
        assets (Sequence[Union[AssetsDefinition, SourceAsset]]):
            The assets to materialize. Can also provide :py:class:`SourceAsset` objects to fill dependencies for asset defs.
        run_config (Optional[Any]): The run config to use for the run that materializes the assets.
        resources (Optional[Mapping[str, object]]):
            The resources needed for execution. Can provide resource instances
            directly, or resource definitions. Note that if provided resources
            conflict with resources directly on assets, an error will be thrown.

    Returns:
        ExecuteInProcessResult: The result of the execution.
    """

    assets = check.sequence_param(assets, "assets", of_type=(AssetsDefinition, SourceAsset))
    assets_defs = [the_def for the_def in assets if isinstance(the_def, AssetsDefinition)]
    source_assets = [the_def for the_def in assets if isinstance(the_def, SourceAsset)]
    resource_defs = wrap_resources_for_execution(resources)
    instance = check.opt_inst_param(instance, "instance", DagsterInstance)

    return build_assets_job(
        "in_process_materialization_job",
        assets=assets_defs,
        source_assets=source_assets,
        resource_defs=resource_defs,
    ).execute_in_process(run_config=run_config, instance=instance)
