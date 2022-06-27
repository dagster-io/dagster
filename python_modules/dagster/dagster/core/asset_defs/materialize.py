from typing import Any, Mapping, Optional, Sequence, Union

import dagster._check as check

from ..definitions.utils import DEFAULT_IO_MANAGER_KEY
from dagster.utils import merge_dicts
from ..execution.build_resources import wrap_resources_for_execution
from ..execution.execute_in_process_result import ExecuteInProcessResult
from ..execution.with_resources import with_resources
from ..instance import DagsterInstance
from ..storage.fs_io_manager import fs_io_manager
from .assets import AssetsDefinition
from .assets_job import build_assets_job
from ..errors import DagsterInvalidInvocationError
from .source_asset import SourceAsset
from ..storage.io_manager import IOManagerDefinition, IOManager
from ..storage.mem_io_manager import mem_io_manager


def materialize(
    assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    run_config: Any = None,
    instance: Optional[DagsterInstance] = None,
    partition_key: Optional[str] = None,
) -> ExecuteInProcessResult:
    """
    Executes a single-threaded, in-process run which materializes provided assets.

    By default, will materialize assets to the local filesystem.

    Args:
        assets (Sequence[Union[AssetsDefinition, SourceAsset]]):
            The assets to materialize. Can also provide :py:class:`SourceAsset` objects to fill dependencies for asset defs.
        run_config (Optional[Any]): The run config to use for the run that materializes the assets.
        partition_key: (Optional[str])
            The string partition key that specifies the run config to execute. Can only be used
            to select run config for assets with partitioned config.

    Returns:
        ExecuteInProcessResult: The result of the execution.
    """

    assets = check.sequence_param(assets, "assets", of_type=(AssetsDefinition, SourceAsset))
    assets = with_resources(assets, {DEFAULT_IO_MANAGER_KEY: fs_io_manager})
    assets_defs = [the_def for the_def in assets if isinstance(the_def, AssetsDefinition)]
    source_assets = [the_def for the_def in assets if isinstance(the_def, SourceAsset)]
    instance = check.opt_inst_param(instance, "instance", DagsterInstance)
    partition_key = check.opt_str_param(partition_key, "partition_key")

    return build_assets_job(
        "in_process_materialization_job",
        assets=assets_defs,
        source_assets=source_assets,
    ).execute_in_process(run_config=run_config, instance=instance, partition_key=partition_key)


def materialize_to_memory(
    assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    run_config: Any = None,
    instance: Optional[DagsterInstance] = None,
    resources: Optional[Mapping[str, object]] = None,
    partition_key: Optional[str] = None,
) -> ExecuteInProcessResult:
    """
    Executes a single-threaded, in-process run which materializes provided assets.

    Assets will be materialized to memory, meaning results will not be
    persisted.

    Args:
        assets (Sequence[Union[AssetsDefinition, SourceAsset]]):
            The assets to materialize. Can also provide :py:class:`SourceAsset` objects to fill dependencies for asset defs. Note that assets cannot have resources on them. Resources can be removed using :py:func:`without_resources`.
        run_config (Optional[Any]): The run config to use for the run that materializes the assets.
        resources (Optional[Mapping[str, object]]):
            The resources needed for execution. Can provide resource instances
            directly, or resource definitions.
        partition_key: (Optional[str])
            The string partition key that specifies the run config to execute. Can only be used
            to select run config for assets with partitioned config.
    Returns:
        ExecuteInProcessResult: The result of the execution.
    """

    assets = check.sequence_param(assets, "assets", of_type=(AssetsDefinition, SourceAsset))
    resources = check.opt_mapping_param(resources, "resources")
    for asset in assets:
        if asset.resource_defs:
            raise DagsterInvalidInvocationError(
                f"Attempted to call `materialize_to_memory` for {str(asset)}, which has provided resources. All resources must be removed prior to invoking, which can be done using ``without_resources``."
            )
    required_io_manager_keys = _get_required_io_manager_keys_from_assets(assets)
    for resource_key, resource in resources.items():
        if isinstance(resource, IOManagerDefinition) or isinstance(resource, IOManager):
            raise DagsterInvalidInvocationError(
                f"When invoking ``materialize_to_memory``, provided IOManager for resource key {resource_key}. Please remove the IOManager from the resource dictionary, as ``materialize_to_memory`` overrides all io managers."
            )
        elif resource_key in required_io_manager_keys:
            raise DagsterInvalidInvocationError(
                f"Provided non-IOManager resource to key {resource_key}, which is required as an IOManager. Remove this resource from the provided resources dictionary."
            )

    resources = merge_dicts(resources, {key: mem_io_manager for key in required_io_manager_keys})

    assets_defs = [the_def for the_def in assets if isinstance(the_def, AssetsDefinition)]
    source_assets = [the_def for the_def in assets if isinstance(the_def, SourceAsset)]
    resource_defs = wrap_resources_for_execution(resources)
    instance = check.opt_inst_param(instance, "instance", DagsterInstance)
    partition_key = check.opt_str_param(partition_key, "partition_key")

    return build_assets_job(
        "in_process_materialization_job",
        assets=assets_defs,
        source_assets=source_assets,
        resource_defs=resource_defs,
    ).execute_in_process(run_config=run_config, instance=instance, partition_key=partition_key)


def _get_required_io_manager_keys_from_assets(
    assets: Sequence[Union[AssetsDefinition, SourceAsset]]
):
    required_io_manager_keys = set()
    for asset in assets:
        for requirement in asset.get_resource_requirements():
            if requirement.expected_type == IOManagerDefinition:
                required_io_manager_keys.add(requirement.key)
    return required_io_manager_keys
