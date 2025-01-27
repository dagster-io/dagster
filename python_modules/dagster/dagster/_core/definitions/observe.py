from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional, Union

import dagster._check as check
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.instance import DagsterInstance
from dagster._utils.warnings import disable_dagster_warnings

if TYPE_CHECKING:
    from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult


def observe(
    assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    run_config: Any = None,
    instance: Optional[DagsterInstance] = None,
    resources: Optional[Mapping[str, object]] = None,
    partition_key: Optional[str] = None,
    raise_on_error: bool = True,
    tags: Optional[Mapping[str, str]] = None,
) -> "ExecuteInProcessResult":
    """Executes a single-threaded, in-process run which observes provided source assets.

    By default, will materialize assets to the local filesystem.

    Args:
        assets (Sequence[Union[AssetsDefinition, SourceAsset]]):
            The assets to observe.
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
    assets = check.sequence_param(assets, "assets", of_type=(AssetsDefinition, SourceAsset))
    instance = check.opt_inst_param(instance, "instance", DagsterInstance)
    partition_key = check.opt_str_param(partition_key, "partition_key")
    resources = check.opt_mapping_param(resources, "resources", key_type=str)

    with disable_dagster_warnings():
        observation_job = define_asset_job(
            "in_process_observation_job", selection=AssetSelection.all(include_sources=True)
        )
        defs = Definitions(
            assets=assets,
            jobs=[observation_job],
            resources=resources,
        )

        return defs.get_job_def("in_process_observation_job").execute_in_process(
            run_config=run_config,
            instance=instance,
            partition_key=partition_key,
            raise_on_error=raise_on_error,
            tags=tags,
        )
