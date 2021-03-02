from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional

from dagster import check
from dagster.config.validate import process_config
from dagster.core.definitions.environment_configs import define_resource_dictionary_cls
from dagster.core.definitions.resource import ResourceDefinition, ScopedResourcesBuilder
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.events import DagsterEvent
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
def init_resources(
    resource_defs: Dict[str, ResourceDefinition],
    run_config: Optional[Dict[str, Any]] = None,
    pipeline_run: Optional[PipelineRun] = None,
    recorder: Optional[List[DagsterEvent]] = None,
) -> Generator[ScopedResourcesBuilder, None, None]:
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
        _setup_events = list(resources_manager.generate_setup_events())
        if recorder:
            for event in _setup_events:
                recorder.append(event)
        resources = check.inst(resources_manager.get_object(), ScopedResourcesBuilder)
        yield resources
    finally:
        _teardown_events = resources_manager.generate_teardown_events()
        if recorder:
            for event in _teardown_events:
                recorder.append(_teardown_events)
