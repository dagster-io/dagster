from collections import defaultdict
from typing import Any, Dict, Optional

from dagster import check
from dagster.core.definitions import (
    DependencyDefinition,
    LoggerDefinition,
    ModeDefinition,
    NodeDefinition,
    OutputDefinition,
    PipelineDefinition,
    ResourceDefinition,
)
from dagster.core.definitions.decorators.solid import solid
from dagster.core.definitions.dependency import SolidHandle
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.instance import DagsterInstance
from dagster.core.storage.mem_io_manager import mem_io_manager
from dagster.utils import merge_dicts

from .api import (
    ExecuteRunWithPlanIterable,
    create_execution_plan,
    ephemeral_instance_if_missing,
    pipeline_execution_iterator,
)
from .context_creation_pipeline import PipelineExecutionContextManager
from .results import ExecutionResult

EPHEMERAL_IO_MANAGER_KEY = "system__execute_solid_ephemeral_node_io_manager"


def _create_value_solid(input_name, input_value):
    @solid(name=input_name, output_defs=[OutputDefinition(io_manager_key=EPHEMERAL_IO_MANAGER_KEY)])
    def input_solid(_):
        return input_value

    return input_solid


def execute_in_process(
    node: NodeDefinition,
    run_config: Optional[dict] = None,
    resources: Optional[Dict[str, ResourceDefinition]] = None,
    loggers: Optional[Dict[str, LoggerDefinition]] = None,
    input_values: Optional[Dict[str, Any]] = None,
    instance: DagsterInstance = None,
) -> ExecutionResult:
    node = check.inst_param(node, "node", NodeDefinition)
    resources = check.opt_dict_param(
        resources, "resources", key_type=str, value_type=ResourceDefinition
    )
    loggers = check.opt_dict_param(loggers, "logger", key_type=str, value_type=LoggerDefinition)
    run_config = check.opt_dict_param(run_config, "run_config", key_type=str)
    input_values = check.opt_dict_param(input_values, "input_values", key_type=str)

    node_defs = [node]

    dependencies: Dict[str, Dict[str, DependencyDefinition]] = defaultdict(dict)

    for input_name, input_value in input_values.items():
        dependencies[node.name][input_name] = DependencyDefinition(input_name)
        node_defs.append(_create_value_solid(input_name, input_value))

    mode_def = ModeDefinition(
        "created",
        resource_defs=merge_dicts(resources, {EPHEMERAL_IO_MANAGER_KEY: mem_io_manager}),
        logger_defs=loggers,
    )

    pipeline_def = PipelineDefinition(
        node_defs,
        name=f"ephemeral_{node.name}_node_pipeline",
        mode_defs=[mode_def],
        dependencies=dependencies,
    )

    pipeline = InMemoryPipeline(pipeline_def)

    execution_plan = create_execution_plan(pipeline, run_config=run_config, mode=mode_def.name)

    with ephemeral_instance_if_missing(instance) as execute_instance:
        pipeline_run = execute_instance.create_run_for_pipeline(
            pipeline_def=pipeline_def,
            run_config=run_config,
            mode=mode_def.name,
        )

        _execute_run_iterable = ExecuteRunWithPlanIterable(
            execution_plan=execution_plan,
            iterator=pipeline_execution_iterator,
            execution_context_manager=PipelineExecutionContextManager(
                execution_plan=execution_plan,
                pipeline_run=pipeline_run,
                instance=execute_instance,
                run_config=run_config,
            ),
        )
        event_list = list(_execute_run_iterable)

    top_level_node_handle = SolidHandle.from_string(node.name)

    event_list_for_top_lvl_node = [
        event
        for event in event_list
        if event.solid_handle and event.solid_handle.is_or_descends_from(top_level_node_handle)
    ]

    return ExecutionResult(node, event_list_for_top_lvl_node)
