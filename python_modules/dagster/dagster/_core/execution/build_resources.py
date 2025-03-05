from asyncio import AbstractEventLoop
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from typing import Any, Optional, cast

import dagster._check as check
from dagster._config import process_config
from dagster._core.definitions.resource_definition import (
    ResourceDefinition,
    Resources,
    ScopedResourcesBuilder,
)
from dagster._core.definitions.run_config import define_resource_dictionary_cls
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.execution.api import ephemeral_instance_if_missing
from dagster._core.execution.context_creation_job import initialize_console_manager
from dagster._core.execution.resources_init import resource_initialization_manager
from dagster._core.instance import DagsterInstance
from dagster._core.log_manager import DagsterLogManager
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.io_manager import IOManager, IOManagerDefinition
from dagster._core.system_config.objects import ResourceConfig, config_map_resources


def get_mapped_resource_config(
    resource_defs: Mapping[str, ResourceDefinition], resource_config: Mapping[str, Any]
) -> Mapping[str, ResourceConfig]:
    resource_config_schema = define_resource_dictionary_cls(
        resource_defs, set(resource_defs.keys())
    )
    config_evr = process_config(resource_config_schema, resource_config)
    if not config_evr.success:
        raise DagsterInvalidConfigError(
            "Error in config for resources ",
            config_evr.errors,
            resource_config,
        )
    config_value = cast(dict[str, Any], config_evr.value)
    return config_map_resources(resource_defs, config_value)


@contextmanager
def build_resources(
    resources: Mapping[str, Any],
    instance: Optional[DagsterInstance] = None,
    resource_config: Optional[Mapping[str, Any]] = None,
    dagster_run: Optional[DagsterRun] = None,
    log_manager: Optional[DagsterLogManager] = None,
    event_loop: Optional[AbstractEventLoop] = None,
) -> Generator[Resources, None, None]:
    """Context manager that yields resources using provided resource definitions and run config.

    This API allows for using resources in an independent context. Resources will be initialized
    with the provided run config, and optionally, dagster_run. The resulting resources will be
    yielded on a dictionary keyed identically to that provided for `resource_defs`. Upon exiting the
    context, resources will also be torn down safely.

    Args:
        resources (Mapping[str, Any]): Resource instances or definitions to build. All
            required resource dependencies to a given resource must be contained within this
            dictionary, or the resource build will fail.
        instance (Optional[DagsterInstance]): The dagster instance configured to instantiate
            resources on.
        resource_config (Optional[Mapping[str, Any]]): A dict representing the config to be
            provided to each resource during initialization and teardown.
        dagster_run (Optional[PipelineRun]): The pipeline run to provide during resource
            initialization and teardown. If the provided resources require either the `dagster_run`
            or `run_id` attributes of the provided context during resource initialization and/or
            teardown, this must be provided, or initialization will fail.
        log_manager (Optional[DagsterLogManager]): Log Manager to use during resource
            initialization. Defaults to system log manager.
        event_loop (Optional[AbstractEventLoop]): An event loop for handling resources
            with async context managers.

    Examples:
        .. code-block:: python

            from dagster import resource, build_resources

            @resource
            def the_resource():
                return "foo"

            with build_resources(resources={"from_def": the_resource, "from_val": "bar"}) as resources:
                assert resources.from_def == "foo"
                assert resources.from_val == "bar"

    """
    resources = check.mapping_param(resources, "resource_defs", key_type=str)
    instance = check.opt_inst_param(instance, "instance", DagsterInstance)
    resource_config = check.opt_mapping_param(resource_config, "resource_config", key_type=str)
    log_manager = check.opt_inst_param(log_manager, "log_manager", DagsterLogManager)
    resource_defs = wrap_resources_for_execution(resources)
    mapped_resource_config = get_mapped_resource_config(resource_defs, resource_config)

    with ephemeral_instance_if_missing(instance) as dagster_instance:
        resources_manager = resource_initialization_manager(
            resource_defs=resource_defs,
            resource_configs=mapped_resource_config,
            log_manager=log_manager if log_manager else initialize_console_manager(dagster_run),
            execution_plan=None,
            dagster_run=dagster_run,
            resource_keys_to_init=set(resource_defs.keys()),
            instance=dagster_instance,
            emit_persistent_events=False,
            event_loop=event_loop,
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


def wrap_resources_for_execution(
    resources: Optional[Mapping[str, Any]] = None,
) -> dict[str, ResourceDefinition]:
    return (
        {
            resource_key: wrap_resource_for_execution(resource)
            for resource_key, resource in resources.items()
        }
        if resources
        else {}
    )


def wrap_resource_for_execution(resource: Any) -> ResourceDefinition:
    from dagster._config.pythonic_config import ConfigurableResourceFactory, PartialResource

    # Wrap instantiated resource values in a resource definition.
    # If an instantiated IO manager is provided, wrap it in an IO manager definition.
    if isinstance(resource, (ConfigurableResourceFactory, PartialResource)):
        return resource.get_resource_definition()
    elif isinstance(resource, ResourceDefinition):
        return resource
    elif isinstance(resource, IOManager):
        return IOManagerDefinition.hardcoded_io_manager(resource)
    else:
        return ResourceDefinition.hardcoded_resource(resource)
