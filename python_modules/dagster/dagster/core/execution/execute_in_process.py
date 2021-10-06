from typing import Any, Dict, List, Optional

from dagster.core.definitions import NodeDefinition, PipelineDefinition
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.instance import DagsterInstance
from dagster.core.selector.subset_selector import (
    UnresolvedOpSelection,
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
from .execute_in_process_result import ExecuteInProcessResult


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

    full_execution_plan = create_execution_plan(
        pipeline,
        run_config=run_config,
        mode=mode_def.name,
    )

    if unresolved_op_selection:
        step_keys_to_execute = None

        # something if wrong here
        scoped_execution_plan = None
        if unresolved_op_selection.selection_scope:
            step_keys_to_execute = resolve_op_selection_to_step_keys_to_execute(
                full_execution_plan, unresolved_op_selection.selection_scope
            )
        if unresolved_op_selection.selection:
            # this is a laziest/easies way but not ideal - it generates execution plan twice
            # in order to resolve two layers of selection
            scoped_execution_plan = (
                create_execution_plan(
                    pipeline,
                    run_config=run_config,
                    mode=mode_def.name,
                    step_keys_to_execute=step_keys_to_execute,
                )
                if step_keys_to_execute  # if the selection scope has been defined on job def
                else None
            )
            step_keys_to_execute = resolve_op_selection_to_step_keys_to_execute(
                execution_plan=scoped_execution_plan or full_execution_plan,
                step_selection=unresolved_op_selection.selection,
            )

        final_execution_plan = create_execution_plan(
            pipeline,
            run_config=run_config,
            mode=mode_def.name,
            step_keys_to_execute=list(step_keys_to_execute) if step_keys_to_execute else None,
        )
    else:
        final_execution_plan = full_execution_plan

    output_capture: Dict[StepOutputHandle, Any] = {}

    with ephemeral_instance_if_missing(instance) as execute_instance:
        pipeline_run = execute_instance.create_run_for_pipeline(
            pipeline_def=pipeline_def,
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
                output_capture=output_capture if output_capturing_enabled else None,
                raise_on_error=raise_on_error,
            ),
        )
        event_list = list(_execute_run_iterable)

    return ExecuteInProcessResult(node, event_list, pipeline_run.run_id, output_capture)
