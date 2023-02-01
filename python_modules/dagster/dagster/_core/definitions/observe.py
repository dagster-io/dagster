import warnings
from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence

import dagster._check as check
from dagster._core.definitions.assets_job import build_source_asset_observation_job
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.backcompat import ExperimentalWarning
from dagster._utils.merger import merge_dicts

from ..instance import DagsterInstance
from .job_definition import default_job_io_manager_with_fs_io_manager_schema
from .source_asset import SourceAsset
from .utils import DEFAULT_IO_MANAGER_KEY

if TYPE_CHECKING:
    from ..execution.execute_in_process_result import ExecuteInProcessResult


def observe(
    source_assets: Sequence[SourceAsset],
    run_config: Any = None,
    instance: Optional[DagsterInstance] = None,
    resources: Optional[Mapping[str, object]] = None,
    partition_key: Optional[str] = None,
    raise_on_error: bool = True,
    tags: Optional[Mapping[str, str]] = None,
) -> "ExecuteInProcessResult":
    """
    Executes a single-threaded, in-process run which observes provided source assets.

    By default, will materialize assets to the local filesystem.

    Args:
        source_assets (Sequence[SourceAsset]):
            The source assets to materialize.
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

    source_assets = check.sequence_param(source_assets, "assets", of_type=(SourceAsset))
    instance = check.opt_inst_param(instance, "instance", DagsterInstance)
    partition_key = check.opt_str_param(partition_key, "partition_key")
    resources = check.opt_mapping_param(resources, "resources", key_type=str)
    resource_defs = wrap_resources_for_execution(resources)
    resource_defs = merge_dicts(
        {DEFAULT_IO_MANAGER_KEY: default_job_io_manager_with_fs_io_manager_schema}, resource_defs
    )

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", category=ExperimentalWarning, message=".*build_source_asset_observation_job.*"
        )

        observation_job = build_source_asset_observation_job(
            "in_process_observation_job", source_assets
        )
        defs = Definitions(
            assets=source_assets,
            jobs=[observation_job],
            resources=resource_defs,
        )

        return defs.get_job_def("in_process_observation_job").execute_in_process(
            run_config=run_config,
            instance=instance,
            partition_key=partition_key,
            raise_on_error=raise_on_error,
            tags=tags,
        )
