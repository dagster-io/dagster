from contextlib import contextmanager
from typing import Any, Dict, Generator, NamedTuple, Optional

from dagster import check
from dagster.config.validate import process_config
from dagster.core.definitions.environment_configs import define_resource_dictionary_cls
from dagster.core.definitions.resource import ResourceDefinition, ScopedResourcesBuilder
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.execution.resources_init import resource_initialization_manager
from dagster.core.instance import DagsterInstance
from dagster.core.log_manager import DagsterLogManager
from dagster.core.storage.io_manager import IOManager, IOManagerDefinition
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.system_config.objects import ResourceConfig, config_map_resources

from .api import ephemeral_instance_if_missing
from .context_creation_pipeline import initialize_console_manager


def _get_mapped_resource_config(
    resource_defs: Dict[str, ResourceDefinition], run_config: Dict[str, Any]
) -> Dict[str, ResourceConfig]:
    resource_config_schema = define_resource_dictionary_cls(
        resource_defs, set(resource_defs.keys())
    )
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
    resources: Dict[str, Any],
    instance: Optional[DagsterInstance] = None,
    run_config: Optional[Dict[str, Any]] = None,
    pipeline_run: Optional[PipelineRun] = None,
    log_manager: Optional[DagsterLogManager] = None,
) -> Generator[NamedTuple, None, None]:
    """Context manager that yields resources using provided resource definitions and run config.

    This API allows for using resources in an independent context. Resources will be initialized
    with the provided run config, and optionally, pipeline_run. The resulting resources will be
    yielded on a dictionary keyed identically to that provided for `resource_defs`. Upon exiting the
    context, resources will also be torn down safely.

    Args:
        resources (Dict[str, Any]): Resource instances or definitions to build. All
            required resource dependencies to a given resource must be contained within this
            dictionary, or the resource build will fail.
        instance (Optional[DagsterInstance]): The dagster instance configured to instantiate resources on.
        run_config (Optional[Dict[str, Any]]): A dict representing the configuration to be provided
            to each resource during initialization and teardown.
        pipeline_run (Optional[PipelineRun]): The pipeline run to provide during resource
            initialization and teardown. If the provided resources require either the `pipeline_run`
            or `run_id` attributes of the provided context during resource initialization and/or
            teardown, this must be provided, or initialization will fail.
        log_manager (Optional[DagsterLogManager]): Log Manager to use during resource
            initialization. Defaults to system log manager.
    """
    resources = check.dict_param(resources, "resource_defs", key_type=str)
    resource_defs = {}
    # Wrap instantiated resource values in a resource definition.
    # If an instantiated IO manager is provided, wrap it in an IO manager definition.
    for resource_key, resource in resources.items():
        if isinstance(resource, ResourceDefinition):
            resource_defs[resource_key] = resource
        elif isinstance(resource, IOManager):
            resource_defs[resource_key] = IOManagerDefinition.hardcoded_io_manager(resource)
        else:
            resource_defs[resource_key] = ResourceDefinition.hardcoded_resource(resource)
    instance = check.opt_inst_param(instance, "instance", DagsterInstance)
    run_config = check.opt_dict_param(run_config, "run_config", key_type=str)
    log_manager = check.opt_inst_param(log_manager, "log_manager", DagsterLogManager)
    mapped_resource_config = _get_mapped_resource_config(resource_defs, run_config)
    with ephemeral_instance_if_missing(instance) as dagster_instance:
        resources_manager = resource_initialization_manager(
            resource_defs=resource_defs,
            resource_configs=mapped_resource_config,
            log_manager=log_manager if log_manager else initialize_console_manager(pipeline_run),
            execution_plan=None,
            pipeline_run=pipeline_run,
            resource_keys_to_init=set(resource_defs.keys()),
            instance=dagster_instance,
            emit_persistent_events=False,
            pipeline_def_for_backwards_compat=None,
        )
        try:
            list(resources_manager.generate_setup_events())
            instantiated_resources = check.inst(
                resources_manager.get_object(), ScopedResourcesBuilder
            )
            yield instantiated_resources.build(
                set(instantiated_resources.resource_instance_dict.keys())
            )
        finally:
            list(resources_manager.generate_teardown_events())
