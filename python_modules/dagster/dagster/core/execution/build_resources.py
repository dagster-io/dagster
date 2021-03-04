from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

from dagster import check
from dagster.config.validate import process_config
from dagster.core.definitions.environment_configs import define_resource_dictionary_cls
from dagster.core.definitions.resource import ResourceDefinition, ScopedResourcesBuilder
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.execution.context.logger import InitLoggerContext
from dagster.core.execution.resources_init import resource_initialization_manager
from dagster.core.log_manager import DagsterLogManager
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.system_config.objects import ResourceConfig, config_map_resources
from dagster.loggers import default_system_loggers


def _initialize_console_manager(pipeline_run: Optional[PipelineRun]) -> DagsterLogManager:
    # initialize default colored console logger
    loggers = []
    for logger_def, logger_config in default_system_loggers():
        loggers.append(
            logger_def.logger_fn(
                InitLoggerContext(
                    logger_config, logger_def, run_id=pipeline_run.run_id if pipeline_run else None
                )
            )
        )
    return DagsterLogManager(
        None, pipeline_run.tags if pipeline_run and pipeline_run.tags else {}, loggers
    )


def _get_mapped_resource_config(
    resource_defs: Dict[str, ResourceDefinition], run_config: Dict[str, Any]
) -> Dict[str, ResourceConfig]:
    resource_config_schema = define_resource_dictionary_cls(resource_defs)
    config_evr = process_config(resource_config_schema, run_config)
    if not config_evr.success:
        raise DagsterInvalidConfigError(
            "Error in config for resources ",
            config_evr.errors,
            run_config,
        )
    config_value = config_evr.value
    return config_map_resources(resource_defs, config_value)


@contextmanager
def build_resources(
    resource_defs: Dict[str, ResourceDefinition],
    run_config: Optional[Dict[str, Any]] = None,
    pipeline_run: Optional[PipelineRun] = None,
) -> Generator[ScopedResourcesBuilder, None, None]:
    """Context manager that yields resources using provided resource definitions and run config.

    This API allows for using resources in an independent context. Resources will be initialized
    with the provided run config, and optionally, pipeline_run. The resulting resources will be
    yielded on a dictionary keyed identically to that provided for `resource_defs`. Upon exiting the
    context, resources will also be torn down safely.

    Args:
        resource_defs (Dict[str, ResourceDefinition]): Resource definitions to build. All
            required resource dependencies to a given resource must be contained within this
            dictionary, or the resource build will fail.
        run_config (Optional[Dict[str, Any]]): A dict representing the configuration to be provided
            to each resource during initialization and teardown.
        pipeline_run (Optional[PipelineRun]): The pipeline run to provide during resource
            initialization and teardown. If the provided resources require either the `pipeline_run`
            or `run_id` attributes of the provided context during resource initialization and/or
            teardown, this must be provided, or initialization will fail.
    """
    resource_defs = check.dict_param(
        resource_defs, "resource_defs", key_type=str, value_type=ResourceDefinition
    )
    run_config = check.opt_dict_param(run_config, "run_config", key_type=str)
    mapped_resource_config = _get_mapped_resource_config(resource_defs, run_config)
    resources_manager = resource_initialization_manager(
        resource_defs=resource_defs,
        resource_configs=mapped_resource_config,
        log_manager=_initialize_console_manager(pipeline_run),
        execution_plan=None,
        pipeline_run=pipeline_run,
        resource_keys_to_init=set(resource_defs.keys()),
        instance=None,
        resource_instances_to_override=None,
        emit_persistent_events=False,
    )
    try:
        list(resources_manager.generate_setup_events())
        resources = check.inst(resources_manager.get_object(), ScopedResourcesBuilder)
        yield resources
    finally:
        list(resources_manager.generate_teardown_events())
