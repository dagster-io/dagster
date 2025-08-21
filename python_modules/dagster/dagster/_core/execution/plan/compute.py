import inspect
from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from typing import Any, TypeVar, Union

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._core.definitions import (
    AssetCheckEvaluation,
    AssetCheckResult,
    AssetMaterialization,
    AssetObservation,
    DynamicOutput,
    ExpectationResult,
    Node,
    NodeHandle,
    Output,
)
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.assets.job.asset_layer import AssetLayer
from dagster._core.definitions.op_definition import OpComputeFunction
from dagster._core.definitions.result import AssetResult, MaterializeResult, ObserveResult
from dagster._core.errors import DagsterExecutionStepExecutionError, DagsterInvariantViolationError
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.compute import ExecutionContextTypes
from dagster._core.execution.context.system import StepExecutionContext
from dagster._core.execution.plan.outputs import StepOutput, StepOutputProperties
from dagster._core.execution.plan.utils import op_execution_error_boundary
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._utils import iterate_with_context

T = TypeVar("T")

OpOutputUnion: TypeAlias = Union[
    DynamicOutput[Any],
    Output[Any],
    AssetMaterialization,
    ExpectationResult,
    AssetObservation,
    DagsterEvent,
    AssetCheckEvaluation,
    AssetCheckResult,
    MaterializeResult,
    ObserveResult,
]


def create_step_outputs(
    node: Node,
    handle: NodeHandle,
    resolved_run_config: ResolvedRunConfig,
    asset_layer: AssetLayer,
) -> Sequence[StepOutput]:
    check.inst_param(node, "node", Node)
    check.inst_param(handle, "handle", NodeHandle)

    # the run config has the node output name configured
    config_output_names: set[str] = set()
    current_handle = handle
    while current_handle:
        op_config = resolved_run_config.ops[str(current_handle)]
        current_handle = current_handle.parent
        config_output_names = config_output_names.union(op_config.outputs.output_names)

    step_outputs: list[StepOutput] = []
    for name, output_def in node.definition.output_dict.items():
        asset_key = asset_layer.get_asset_key_for_node_output(handle, name)
        asset_check_key = asset_layer.get_asset_check_key_for_node_output(handle, name)

        selected_entity_keys = asset_layer.get_selected_entity_keys_for_node(handle)
        asset_node = asset_layer.asset_graph.get(asset_key) if asset_key else None

        step_outputs.append(
            StepOutput(
                node_handle=handle,
                name=output_def.name,
                dagster_type_key=output_def.dagster_type.key,
                properties=StepOutputProperties(
                    is_required=output_def.is_required,
                    is_dynamic=output_def.is_dynamic,
                    is_asset=asset_key is not None,
                    should_materialize_DEPRECATED=output_def.name in config_output_names,
                    asset_key=asset_key if asset_key in selected_entity_keys else None,
                    is_asset_partitioned=bool(asset_node.partitions_def) if asset_node else False,
                    asset_check_key=asset_check_key
                    if asset_check_key in selected_entity_keys
                    else None,
                    asset_execution_type=asset_node.execution_type if asset_node else None,
                ),
            )
        )
    return step_outputs


def _validate_event(event: Any, step_context: StepExecutionContext) -> OpOutputUnion:
    if not isinstance(
        event,
        (
            DynamicOutput,
            Output,
            AssetMaterialization,
            ExpectationResult,
            AssetObservation,
            DagsterEvent,
            AssetCheckResult,
            AssetCheckEvaluation,
            MaterializeResult,
            ObserveResult,
        ),
    ):
        raise DagsterInvariantViolationError(
            f"Compute function for {step_context.describe_op()} yielded a value of type {type(event)} "
            "rather than an instance of Output, AssetMaterialization, or ExpectationResult."
            f" Values yielded by {step_context.op_def.node_type_str}s must be wrapped in one of these types. If your "
            f"{step_context.op_def.node_type_str} has a single output and yields no other events, you may want to use "
            f"`return` instead of `yield` in the body of your {step_context.op_def.node_type_str} compute function. If "
            "you are already using `return`, and you expected to return a value of type "
            f"{type(event)}, you may be inadvertently returning a generator rather than the value "
            # f"you expected. Value is {str(event[0])}"
        )

    return event


def gen_from_async_gen(
    context: StepExecutionContext,
    async_gen: AsyncIterator[T],
) -> Iterator[T]:
    while True:
        try:
            yield context.event_loop.run_until_complete(async_gen.__anext__())
        except StopAsyncIteration:
            return


def _yield_compute_results(
    step_context: StepExecutionContext,
    inputs: Mapping[str, Any],
    compute_fn: OpComputeFunction,
    compute_context: ExecutionContextTypes,
) -> Iterator[OpOutputUnion]:
    user_event_generator = compute_fn(compute_context, inputs)

    if isinstance(user_event_generator, Output):
        raise DagsterInvariantViolationError(
            f"Compute function for {step_context.describe_op()} returned an Output rather than "
            f"yielding it. The compute_fn of the {step_context.op_def.node_type_str} must yield "
            "its results"
        )

    if user_event_generator is None:
        return

    if inspect.isasyncgen(user_event_generator):
        user_event_generator = gen_from_async_gen(step_context, user_event_generator)

    op_label = step_context.describe_op()

    for event in iterate_with_context(
        lambda: op_execution_error_boundary(
            DagsterExecutionStepExecutionError,
            msg_fn=lambda: f"Error occurred while executing {op_label}:",
            step_context=step_context,
            step_key=step_context.step.key,
            op_def_name=step_context.op_def.name,
            op_name=step_context.op.name,
        ),
        user_event_generator,
    ):
        if compute_context.op_execution_context.has_events():
            yield from compute_context.op_execution_context.consume_events()
        yield _validate_event(event, step_context)

    if compute_context.op_execution_context.has_events():
        yield from compute_context.op_execution_context.consume_events()


def execute_core_compute(
    step_context: StepExecutionContext,
    inputs: Mapping[str, Any],
    compute_fn: OpComputeFunction,
    compute_context: ExecutionContextTypes,
) -> Iterator[OpOutputUnion]:
    """Execute the user-specified compute for the op. Wrap in an error boundary and do
    all relevant logging and metrics tracking.
    """
    step = step_context.step

    emitted_result_names = set()
    for step_output in _yield_compute_results(step_context, inputs, compute_fn, compute_context):
        yield step_output
        if isinstance(step_output, (DynamicOutput, Output)):
            emitted_result_names.add(step_output.output_name)
        elif isinstance(step_output, AssetResult):
            asset_key = (
                step_output.asset_key
                or step_context.job_def.asset_layer.get_asset_key_for_node(step_context.node_handle)
            )
            emitted_result_names.add(
                step_context.job_def.asset_layer.asset_graph.get(
                    asset_key
                ).assets_def.get_output_name_for_asset_key(asset_key)
            )
            # Check results embedded in MaterializeResult are counted
            for check_result in step_output.check_results or []:
                key = check_result.to_asset_check_evaluation(step_context).asset_check_key
                output_name = step_context.job_def.asset_layer.get_op_output_name(key)
                emitted_result_names.add(output_name)
        elif isinstance(step_output, AssetCheckResult):
            if step_output.asset_key and step_output.check_name:
                key = AssetCheckKey(step_output.asset_key, step_output.check_name)
            else:
                key = step_output.to_asset_check_evaluation(step_context).asset_check_key
            output_name = step_context.job_def.asset_layer.get_op_output_name(key)
            if output_name:
                emitted_result_names.add(output_name)

    expected_op_output_names = {
        output.name
        for output in step.step_outputs
        # checks are required if we're in requires_typed_event_stream mode
        if step_context.requires_typed_event_stream or output.properties.asset_check_key
    }
    omitted_outputs = expected_op_output_names.intersection(
        step_context.selected_output_names
    ).difference(emitted_result_names)
    if omitted_outputs:
        message = (
            f"{step_context.op_def.node_type_str} '{step.node_handle}' did not yield or return "
            f"expected outputs {omitted_outputs!r}."
        )

        if step_context.requires_typed_event_stream:
            if step_context.typed_event_stream_error_message:
                message += " " + step_context.typed_event_stream_error_message
            raise DagsterInvariantViolationError(message)
        else:
            step_context.log.info(message)
