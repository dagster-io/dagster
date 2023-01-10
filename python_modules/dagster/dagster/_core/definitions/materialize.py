import warnings
from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence, Set, Union

import dagster._check as check
from dagster._utils.backcompat import ExperimentalWarning
from dagster._utils.merger import merge_dicts

from ..errors import DagsterInvariantViolationError
from ..instance import DagsterInstance
from ..storage.io_manager import IOManagerDefinition
from ..storage.mem_io_manager import mem_io_manager
from .assets import AssetsDefinition
from .assets_job import build_assets_job
from .job_definition import default_job_io_manager_with_fs_io_manager_schema
from .source_asset import SourceAsset
from .utils import DEFAULT_IO_MANAGER_KEY

if TYPE_CHECKING:
    from ..execution.execute_in_process_result import ExecuteInProcessResult


def materialize(
    assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    run_config: Any = None,
    instance: Optional[DagsterInstance] = None,
    resources: Optional[Mapping[str, object]] = None,
    partition_key: Optional[str] = None,
    raise_on_error: bool = True,
    tags: Optional[Mapping[str, str]] = None,
) -> "ExecuteInProcessResult":
    """
    Executes a single-threaded, in-process run which materializes provided assets.

    By default, will materialize assets to the local filesystem.

    Args:
        assets (Sequence[Union[AssetsDefinition, SourceAsset]]):
            The assets to materialize. Can also provide :py:class:`SourceAsset` objects to fill dependencies for asset defs.
        resources (Optional[Mapping[str, object]]):
            The resources needed for execution. Can provide resource instances
            directly, or resource definitions. Note that if provided resources
            conflict with resources directly on assets, an error will be thrown.
        run_config (Optional[Any]): The run config to use for the run that materializes the assets.
        partition_key: (Optional[str])
            The string partition key that specifies the run config to execute. Can only be used
            to select run config for assets with partitioned config.
        tags (Optional[Mapping[str, str]]): Tags for the run.

    Returns:
        ExecuteInProcessResult: The result of the execution.
    """
    from ..execution.build_resources import wrap_resources_for_execution

    assets = check.sequence_param(assets, "assets", of_type=(AssetsDefinition, SourceAsset))
    assets_defs = [the_def for the_def in assets if isinstance(the_def, AssetsDefinition)]
    source_assets = [the_def for the_def in assets if isinstance(the_def, SourceAsset)]
    instance = check.opt_inst_param(instance, "instance", DagsterInstance)
    partition_key = check.opt_str_param(partition_key, "partition_key")
    resources = check.opt_mapping_param(resources, "resources", key_type=str)
    resource_defs = wrap_resources_for_execution(resources)
    resource_defs = merge_dicts(
        {DEFAULT_IO_MANAGER_KEY: default_job_io_manager_with_fs_io_manager_schema}, resource_defs
    )

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", category=ExperimentalWarning, message=".*build_assets_job.*"
        )

        return build_assets_job(
            "in_process_materialization_job",
            assets=assets_defs,
            source_assets=source_assets,
            resource_defs=resource_defs,
        ).execute_in_process(
            run_config=run_config,
            instance=instance,
            partition_key=partition_key,
            raise_on_error=raise_on_error,
            tags=tags,
        )


def materialize_to_memory(
    assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    run_config: Any = None,
    instance: Optional[DagsterInstance] = None,
    resources: Optional[Mapping[str, object]] = None,
    partition_key: Optional[str] = None,
    raise_on_error: bool = True,
    tags: Optional[Mapping[str, str]] = None,
) -> "ExecuteInProcessResult":
    """
    Executes a single-threaded, in-process run which materializes provided assets in memory.

    Will explicitly use :py:func:`mem_io_manager` for all required io manager
    keys. If any io managers are directly provided using the `resources`
    argument, a :py:class:`DagsterInvariantViolationError` will be thrown.

    Args:
        assets (Sequence[Union[AssetsDefinition, SourceAsset]]):
            The assets to materialize. Can also provide :py:class:`SourceAsset` objects to fill dependencies for asset defs.
        run_config (Optional[Any]): The run config to use for the run that materializes the assets.
        resources (Optional[Mapping[str, object]]):
            The resources needed for execution. Can provide resource instances
            directly, or resource definitions. If provided resources
            conflict with resources directly on assets, an error will be thrown.
        partition_key: (Optional[str])
            The string partition key that specifies the run config to execute. Can only be used
            to select run config for assets with partitioned config.
        tags (Optional[Mapping[str, str]]): Tags for the run.

    Returns:
        ExecuteInProcessResult: The result of the execution.
    """
    from dagster._core.execution.build_resources import wrap_resources_for_execution

    assets = check.sequence_param(assets, "assets", of_type=(AssetsDefinition, SourceAsset))
    resource_defs = wrap_resources_for_execution(resources)
    # Gather all resource defs for the purpose of checking io managers.
    all_resource_defs = dict(resource_defs)
    for asset in assets:
        all_resource_defs = merge_dicts(asset.resource_defs, all_resource_defs)

    io_manager_keys = _get_required_io_manager_keys(assets)
    for io_manager_key in io_manager_keys:
        if io_manager_key in all_resource_defs:
            raise DagsterInvariantViolationError(
                "Attempted to call `materialize_to_memory` with a resource "
                f"provided for io manager key '{io_manager_key}'. Do not "
                "provide resources for io manager keys when calling "
                "`materialize_to_memory`, as it will override io management "
                "behavior for all keys."
            )
    resource_defs = merge_dicts({key: mem_io_manager for key in io_manager_keys}, resource_defs)
    assets_defs = [the_def for the_def in assets if isinstance(the_def, AssetsDefinition)]
    source_assets = [the_def for the_def in assets if isinstance(the_def, SourceAsset)]

    instance = check.opt_inst_param(instance, "instance", DagsterInstance)
    partition_key = check.opt_str_param(partition_key, "partition_key")

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", category=ExperimentalWarning, message=".*build_assets_job.*"
        )

        return build_assets_job(
            "in_process_materialization_job",
            assets=assets_defs,
            source_assets=source_assets,
            resource_defs=resource_defs,
        ).execute_in_process(
            run_config=run_config,
            instance=instance,
            partition_key=partition_key,
            raise_on_error=raise_on_error,
            tags=tags,
        )


def _get_required_io_manager_keys(
    assets: Sequence[Union[AssetsDefinition, SourceAsset]]
) -> Set[str]:
    io_manager_keys = set()
    for asset in assets:
        for requirement in asset.get_resource_requirements():
            if requirement.expected_type == IOManagerDefinition:
                io_manager_keys.add(requirement.key)
    return io_manager_keys
