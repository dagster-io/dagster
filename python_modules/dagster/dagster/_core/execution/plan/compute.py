import asyncio
import inspect
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Iterator,
    List,
    Mapping,
    Sequence,
    Set,
    TypeVar,
    Union,
)

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
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_layer import AssetLayer
from dagster._core.definitions.op_definition import OpComputeFunction
from dagster._core.definitions.result import MaterializeResult
from dagster._core.errors import DagsterExecutionStepExecutionError, DagsterInvariantViolationError
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.compute import build_execution_context
from dagster._core.execution.context.system import StepExecutionContext
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._utils import iterate_with_context

from .outputs import StepOutput, StepOutputProperties
from .utils import op_execution_error_boundary

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
]


def create_step_outputs(
    node: Node, handle: NodeHandle, resolved_run_config: ResolvedRunConfig, asset_layer: AssetLayer
) -> Sequence[StepOutput]:
    check.inst_param(node, "node", Node)
    check.inst_param(handle, "handle", NodeHandle)

    # the run config has the node output name configured
    config_output_names: Set[str] = set()
    current_handle = handle
    while current_handle:
        op_config = resolved_run_config.ops[current_handle.to_string()]
        current_handle = current_handle.parent
        config_output_names = config_output_names.union(op_config.outputs.output_names)

    step_outputs: List[StepOutput] = []
    for name, output_def in node.definition.output_dict.items():
        asset_info = asset_layer.asset_info_for_output(handle, name)

        step_outputs.append(
            StepOutput(
                node_handle=handle,
                name=output_def.name,
                dagster_type_key=output_def.dagster_type.key,
                properties=StepOutputProperties(
                    is_required=output_def.is_required,
                    is_dynamic=output_def.is_dynamic,
                    is_asset=asset_info is not None,
                    should_materialize=output_def.name in config_output_names,
                    asset_key=asset_info.key if asset_info and asset_info.is_required else None,
                    is_asset_partitioned=bool(asset_info.partitions_def) if asset_info else False,
                    asset_check_key=asset_layer.asset_check_key_for_output(handle, name),
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
        ),
    ):
        raise DagsterInvariantViolationError(
            (
                "Compute function for {described_node} yielded a value of type {type_} "
                "rather than an instance of Output, AssetMaterialization, or ExpectationResult."
                " Values yielded by {node_type}s must be wrapped in one of these types. If your "
                "{node_type} has a single output and yields no other events, you may want to use "
                "`return` instead of `yield` in the body of your {node_type} compute function. If "
                "you are already using `return`, and you expected to return a value of type "
                "{type_}, you may be inadvertently returning a generator rather than the value "
                # f"you expected. Value is {str(event[0])}"
            ).format(
                described_node=step_context.describe_op(),
                type_=type(event),
                node_type=step_context.op_def.node_type_str,
            )
        )

    return event


def gen_from_async_gen(async_gen: AsyncIterator[T]) -> Iterator[T]:
    # prime use for asyncio.Runner, but new in 3.11 and did not find appealing backport
    loop = asyncio.new_event_loop()
    try:
        while True:
            try:
                yield loop.run_until_complete(async_gen.__anext__())
            except StopAsyncIteration:
                return
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


def _yield_compute_results(
    step_context: StepExecutionContext, inputs: Mapping[str, Any], compute_fn: Callable
) -> Iterator[OpOutputUnion]:
    check.inst_param(step_context, "step_context", StepExecutionContext)

    context = build_execution_context(step_context)
    user_event_generator = compute_fn(context, inputs)

    if isinstance(user_event_generator, Output):
        raise DagsterInvariantViolationError(
            (
                "Compute function for {described_node} returned an Output rather than "
                "yielding it. The compute_fn of the {node_type} must yield "
                "its results"
            ).format(
                described_node=step_context.describe_op(),
                node_type=step_context.op_def.node_type_str,
            )
        )

    if user_event_generator is None:
        return

    if inspect.isasyncgen(user_event_generator):
        user_event_generator = gen_from_async_gen(user_event_generator)

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
        if context.has_events():
            yield from context.consume_events()
        yield _validate_event(event, step_context)

    if context.has_events():
        yield from context.consume_events()


def execute_core_compute(
    step_context: StepExecutionContext, inputs: Mapping[str, Any], compute_fn: OpComputeFunction
) -> Iterator[OpOutputUnion]:
    """Execute the user-specified compute for the op. Wrap in an error boundary and do
    all relevant logging and metrics tracking.
    """
    check.inst_param(step_context, "step_context", StepExecutionContext)
    check.mapping_param(inputs, "inputs", key_type=str)

    step = step_context.step

    emitted_result_names = set()
    for step_output in _yield_compute_results(step_context, inputs, compute_fn):
        yield step_output
        if isinstance(step_output, (DynamicOutput, Output)):
            emitted_result_names.add(step_output.output_name)
        elif isinstance(step_output, MaterializeResult):
            asset_key = (
                step_output.asset_key
                or step_context.job_def.asset_layer.asset_key_for_node(step_context.node_handle)
            )
            emitted_result_names.add(
                step_context.job_def.asset_layer.node_output_handle_for_asset(asset_key).output_name
            )
            # Check results embedded in MaterializeResult are counted
            for check_result in step_output.check_results or []:
                handle = check_result.to_asset_check_evaluation(step_context).asset_check_key
                output_name = step_context.job_def.asset_layer.get_output_name_for_asset_check(
                    handle
                )
                emitted_result_names.add(output_name)
        elif isinstance(step_output, AssetCheckEvaluation):
            output_name = step_context.job_def.asset_layer.get_output_name_for_asset_check(
                step_output.asset_check_key
            )
            emitted_result_names.add(output_name)
        elif isinstance(step_output, AssetCheckResult):
            if step_output.asset_key and step_output.check_name:
                handle = AssetCheckKey(step_output.asset_key, step_output.check_name)
            else:
                handle = step_output.to_asset_check_evaluation(step_context).asset_check_key
            output_name = step_context.job_def.asset_layer.get_output_name_for_asset_check(handle)
            emitted_result_names.add(output_name)

    expected_op_output_names = {
        output.name
        for output in step.step_outputs
        # checks are required if we're in requires_typed_event_stream mode
        if step_context.requires_typed_event_stream or output.properties.asset_check_key
    }
    omitted_outputs = expected_op_output_names.difference(emitted_result_names)
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
