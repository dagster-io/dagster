from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence, Union

import dagster._check as check
from dagster._annotations import deprecated_param
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.assets_job import build_assets_job
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.warnings import disable_dagster_warnings, normalize_renamed_param

from ..instance import DagsterInstance
from .source_asset import SourceAsset

if TYPE_CHECKING:
    from ..execution.execute_in_process_result import ExecuteInProcessResult


@deprecated_param(
    param="source_assets", breaking_version="2.0", additional_warn_text="Use `assets` instead."
)
def observe(
    assets: Optional[Sequence[Union[SourceAsset, AssetsDefinition]]] = None,
    run_config: Any = None,
    instance: Optional[DagsterInstance] = None,
    resources: Optional[Mapping[str, object]] = None,
    partition_key: Optional[str] = None,
    raise_on_error: bool = True,
    tags: Optional[Mapping[str, str]] = None,
    *,
    source_assets: Optional[Sequence[SourceAsset]] = None,
) -> "ExecuteInProcessResult":
    """Executes a single-threaded, in-process run which observes provided observable assets.

    By default, will materialize assets to the local filesystem.

    Args:
        assets (Sequence[Union[SourceAsset, AssetsDefinition]]):
            The assets to observe. Assets must be observable.
        resources (Optional[Mapping[str, object]]):
            The resources needed for execution. Can provide resource instances
            directly, or resource definitions. Note that if provided resources
            conflict with resources directly on assets, an error will be thrown.
        run_config (Optional[Any]): The run config to use for the run that materializes the assets.
        partition_key: (Optional[str])
            The string partition key that specifies the run config to execute. Can only be used
            to select run config for assets with partitioned config.
        tags (Optional[Mapping[str, str]]): Tags for the run.
        source_assets (Sequence[Union[SourceAsset, AssetsDefinition]]):
            The assets to observe.

    Returns:
        ExecuteInProcessResult: The result of the execution.
    """
    assets = check.not_none(
        normalize_renamed_param(
            assets,
            "assets",
            source_assets,
            "source_assets",
        )
    )
    assets = check.sequence_param(assets, "assets", of_type=(AssetsDefinition, SourceAsset))
    instance = check.opt_inst_param(instance, "instance", DagsterInstance)
    partition_key = check.opt_str_param(partition_key, "partition_key")
    resources = check.opt_mapping_param(resources, "resources", key_type=str)

    with disable_dagster_warnings():
        observation_job = build_assets_job("in_process_observation_job", assets)
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
