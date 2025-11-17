import inspect
from collections.abc import AsyncGenerator, AsyncIterator, Iterator, Mapping
from typing import Any, TypeAlias, TypeVar, Union

from dagster._core.definitions import (
    AssetCheckEvaluation,
    AssetCheckResult,
    AssetMaterialization,
    AssetObservation,
    DynamicOutput,
    ExpectationResult,
    Output,
)
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.op_definition import OpComputeFunction
from dagster._core.definitions.result import AssetResult, MaterializeResult, ObserveResult
from dagster._core.errors import DagsterExecutionStepExecutionError, DagsterInvariantViolationError
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.compute import ExecutionContextTypes
from dagster._core.execution.context.system import StepExecutionContext
from dagster._core.execution.plan.compute import _validate_event
from dagster._core.execution.plan.utils import op_execution_error_boundary
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


def _wrap_sync_iterator(iterator: Iterator[OpOutputUnion]) -> AsyncIterator[OpOutputUnion]:
    async def _iterate() -> AsyncGenerator[OpOutputUnion, None]:
        for item in iterator:
            yield item

    return _iterate()


def _error_boundary_factory(step_context: StepExecutionContext):
    op_label = step_context.describe_op()
    return op_execution_error_boundary(
        DagsterExecutionStepExecutionError,
        msg_fn=lambda: f"Error occurred while executing {op_label}:",
        step_context=step_context,
        step_key=step_context.step.key,
        op_def_name=step_context.op_def.name,
        op_name=step_context.op.name,
    )


def _wrap_sync_generator_with_boundary(
    step_context: StepExecutionContext,
    iterator: Iterator[OpOutputUnion],
) -> AsyncIterator[OpOutputUnion]:
    wrapped = iterate_with_context(lambda: _error_boundary_factory(step_context), iterator)
    return _wrap_sync_iterator(wrapped)


def _wrap_async_iterator_with_boundary(
    step_context: StepExecutionContext, iterator: AsyncIterator[OpOutputUnion]
) -> AsyncIterator[OpOutputUnion]:
    async def _iterate() -> AsyncGenerator[OpOutputUnion, None]:
        with _error_boundary_factory(step_context):
            async for item in iterator:
                yield item

    return _iterate()


async def _to_async_iterator(
    step_context: StepExecutionContext, user_event_generator: Any
) -> AsyncIterator[OpOutputUnion] | None:
    if isinstance(user_event_generator, Output):
        raise DagsterInvariantViolationError(
            f"Compute function for {step_context.describe_op()} returned an Output rather than "
            f"yielding it. The compute_fn of the {step_context.op_def.node_type_str} must yield "
            "its results"
        )

    if user_event_generator is None:
        return None

    if inspect.isawaitable(user_event_generator):
        awaited = await user_event_generator
        return await _to_async_iterator(step_context, awaited)

    if inspect.isasyncgen(user_event_generator) or isinstance(user_event_generator, AsyncIterator):
        return _wrap_async_iterator_with_boundary(step_context, user_event_generator)

    if inspect.isgenerator(user_event_generator) or isinstance(user_event_generator, Iterator):
        return _wrap_sync_generator_with_boundary(step_context, user_event_generator)

    return None


async def _yield_compute_results(
    step_context: StepExecutionContext,
    inputs: Mapping[str, Any],
    compute_fn: OpComputeFunction,
    compute_context: ExecutionContextTypes,
) -> AsyncIterator[OpOutputUnion]:
    user_event_generator = compute_fn(compute_context, inputs)
    async_iterator = await _to_async_iterator(step_context, user_event_generator)

    if async_iterator is None:
        return

    async for event in async_iterator:
        if compute_context.op_execution_context.has_events():
            for e in compute_context.op_execution_context.consume_events():
                yield e
        yield _validate_event(event, step_context)

    if compute_context.op_execution_context.has_events():
        for e in compute_context.op_execution_context.consume_events():
            yield e


async def execute_core_compute(
    step_context: StepExecutionContext,
    inputs: Mapping[str, Any],
    compute_fn: OpComputeFunction,
    compute_context: ExecutionContextTypes,
) -> AsyncIterator[OpOutputUnion]:
    """Execute the user-specified compute for the op. Wrap in an error boundary and do
    all relevant logging and metrics tracking.
    """
    step = step_context.step

    emitted_result_names = set()
    async for step_output in _yield_compute_results(
        step_context, inputs, compute_fn, compute_context
    ):
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
