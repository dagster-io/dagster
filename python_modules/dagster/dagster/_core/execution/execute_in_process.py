from typing import Any, Dict, FrozenSet, Mapping, Optional, cast

from dagster._core.definitions import GraphDefinition, JobDefinition, Node, NodeHandle, OpDefinition
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.pipeline_base import InMemoryPipeline
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.execution.plan.outputs import StepOutputHandle
from dagster._core.instance import DagsterInstance
from dagster._core.storage.pipeline_run import DagsterRun
from dagster._core.types.dagster_type import DagsterTypeKind

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
    run_config: Mapping[str, object],
    ephemeral_pipeline: JobDefinition,
    instance: Optional[DagsterInstance],
    output_capturing_enabled: bool,
    raise_on_error: bool,
    run_tags: Optional[Mapping[str, str]] = None,
    run_id: Optional[str] = None,
    asset_selection: Optional[FrozenSet[AssetKey]] = None,
) -> ExecuteInProcessResult:
    job_def = ephemeral_pipeline
    mode_def = job_def.get_mode_definition()
    pipeline = InMemoryPipeline(job_def)

    _check_top_level_inputs(job_def)

    execution_plan = create_execution_plan(
        pipeline,
        run_config=run_config,
        mode=mode_def.name,
        instance_ref=instance.get_ref() if instance and instance.is_persistent else None,
    )

    output_capture: Dict[StepOutputHandle, Any] = {}

    with ephemeral_instance_if_missing(instance) as execute_instance:
        pipeline_run = execute_instance.create_run_for_pipeline(
            pipeline_def=job_def,
            run_config=run_config,
            mode=mode_def.name,
            tags={**job_def.tags, **(run_tags or {})},
            run_id=run_id,
            asset_selection=asset_selection,
            execution_plan=execution_plan,
        )
        run_id = pipeline_run.run_id

        execute_run_iterable = ExecuteRunWithPlanIterable(
            execution_plan=execution_plan,
            iterator=pipeline_execution_iterator,
            execution_context_manager=PlanOrchestrationContextManager(
                context_event_generator=orchestration_context_event_generator,
                pipeline=pipeline,
                execution_plan=execution_plan,
                pipeline_run=pipeline_run,
                instance=execute_instance,
                run_config=run_config,
                executor_defs=None,
                output_capture=output_capture if output_capturing_enabled else None,
                raise_on_error=raise_on_error,
            ),
        )

        event_list = list(execute_run_iterable)

    return ExecuteInProcessResult(
        job_def=ephemeral_pipeline,
        event_list=event_list,
        dagster_run=cast(DagsterRun, execute_instance.get_run_by_id(run_id)),
        output_capture=output_capture,
    )


def _check_top_level_inputs(job_def: JobDefinition) -> None:
    for input_mapping in job_def.graph.input_mappings:
        node = job_def.graph.solid_named(input_mapping.maps_to.solid_name)
        top_level_input_name = input_mapping.graph_input_name
        input_name = input_mapping.maps_to.input_name
        _check_top_level_inputs_for_node(
            node,
            top_level_input_name,
            job_def.has_direct_input_value(top_level_input_name),
            input_name,
            job_def.name,
            None,
        )


def _check_top_level_inputs_for_node(
    node: Node,
    top_level_input_name: str,
    top_level_input_provided: bool,
    input_name: str,
    job_name: str,
    parent_handle: Optional[NodeHandle],
) -> None:
    if isinstance(node.definition, GraphDefinition):
        graph_def = cast(GraphDefinition, node.definition)
        for input_mapping in graph_def.input_mappings:
            next_node = graph_def.solid_named(input_mapping.maps_to.solid_name)
            input_name = input_mapping.maps_to.input_name
            _check_top_level_inputs_for_node(
                next_node,
                top_level_input_name,
                top_level_input_provided,
                input_name,
                job_name,
                NodeHandle(node.name, parent_handle),
            )
    else:
        cur_node_handle = NodeHandle(node.name, parent_handle)
        op_def = cast(OpDefinition, node.definition)
        input_def = op_def.input_def_named(input_name)
        if (
            not input_def.dagster_type.loader
            and not input_def.dagster_type.kind == DagsterTypeKind.NOTHING
            and not input_def.root_manager_key
            and not input_def.has_default_value
            and not top_level_input_provided
        ):
            raise DagsterInvalidInvocationError(
                f"Attempted to invoke execute_in_process for '{job_name}' without specifying an input_value for input '{top_level_input_name}', but downstream input {input_def.name} of op '{str(cur_node_handle)}' has no other way of being loaded."
            )
