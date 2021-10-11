from typing import Any, Dict, List, Optional

from dagster import check
from dagster.core.definitions import (
    GraphDefinition,
    NodeDefinition,
    PipelineDefinition,
    SolidDefinition,
    solid,
)
from dagster.core.definitions.dependency import NodeHandle
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.instance import DagsterInstance
from dagster.core.selector.subset_selector import (
    UnresolvedOpSelection,
    parse_solid_selection,
    resolve_op_selection_to_step_keys_to_execute,
)

from .api import (
    ExecuteRunWithPlanIterable,
    create_execution_plan,
    ephemeral_instance_if_missing,
    pipeline_execution_iterator,
)
from .context_creation_pipeline import (
    PlanOrchestrationContextManager,
    orchestration_context_event_generator,
)
from .execution_results import InProcessGraphResult, InProcessOpResult


def core_execute_in_process(
    node: NodeDefinition,
    run_config: Dict[str, Any],
    ephemeral_pipeline: PipelineDefinition,
    instance: Optional[DagsterInstance],
    output_capturing_enabled: bool,
    raise_on_error: bool,
    unresolved_op_selection: Optional[UnresolvedOpSelection] = None,  # TODO: not nullable
):
    pipeline_def = ephemeral_pipeline
    mode_def = pipeline_def.get_mode_definition()
    pipeline = InMemoryPipeline(pipeline_def)

    solids_to_execute = None
    if unresolved_op_selection:
        if unresolved_op_selection.selection_scope:
            solids_to_execute = parse_solid_selection(
                pipeline_def, unresolved_op_selection.selection_scope
            )
        if unresolved_op_selection.selection:
            solids_to_execute = parse_solid_selection(
                pipeline_def.get_pipeline_subset_def(solids_to_execute),
                unresolved_op_selection.selection,
            )

    # TODO: this is currently mixing solids and node handles
    # Curr: parse_solid_selection -> ["sub_graph", "my_super_op"]
    # Ideal: parse_unresolved_op_selection -> ["sub_graph.my_op", "my_super_op"]
    resolved_op_selection = list(solids_to_execute) if solids_to_execute else None
    final_execution_plan = create_execution_plan(
        pipeline,
        run_config=run_config,
        mode=mode_def.name,
        step_keys_to_execute=resolved_op_selection,
        _resolved_op_selection=resolved_op_selection,
    )

    recorder: Dict[StepOutputHandle, Any] = {}

    with ephemeral_instance_if_missing(instance) as execute_instance:
        pipeline_run = execute_instance.create_run_for_pipeline(
            pipeline_def=pipeline_def,
            execution_plan=final_execution_plan,
            run_config=run_config,
            mode=mode_def.name,
            tags=pipeline_def.tags,
        )

        _execute_run_iterable = ExecuteRunWithPlanIterable(
            execution_plan=final_execution_plan,
            iterator=pipeline_execution_iterator,
            execution_context_manager=PlanOrchestrationContextManager(
                context_event_generator=orchestration_context_event_generator,
                pipeline=pipeline,
                execution_plan=final_execution_plan,
                pipeline_run=pipeline_run,
                instance=execute_instance,
                run_config=run_config,
                executor_defs=None,
                output_capture=recorder if output_capturing_enabled else None,
                raise_on_error=raise_on_error,
            ),
        )
        event_list = list(_execute_run_iterable)

    top_level_node_handle = NodeHandle.from_string(node.name)

    if isinstance(node, GraphDefinition) and node == ephemeral_pipeline.graph:
        event_list_for_top_lvl_node = event_list
        handle = None
        return InProcessGraphResult(node, handle, event_list_for_top_lvl_node, recorder)
    else:
        event_list_for_top_lvl_node = [
            event
            for event in event_list
            if event.solid_handle and event.solid_handle.is_or_descends_from(top_level_node_handle)
        ]
        handle = NodeHandle(node.name, None)

        if isinstance(node, SolidDefinition):
            return InProcessOpResult(node, handle, event_list_for_top_lvl_node, recorder)
        elif isinstance(node, GraphDefinition):
            return InProcessGraphResult(node, handle, event_list_for_top_lvl_node, recorder)

    check.failed(f"Unexpected node type {node}")
