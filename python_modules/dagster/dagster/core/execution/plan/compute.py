import asyncio
import inspect
from typing import Any, AsyncGenerator, Callable, Dict, Iterator, List, Set, Union

from dagster import check
from dagster.core.definitions import (
    AssetMaterialization,
    DynamicOutput,
    ExpectationResult,
    Materialization,
    Node,
    NodeHandle,
    Output,
)
from dagster.core.errors import DagsterExecutionStepExecutionError, DagsterInvariantViolationError
from dagster.core.execution.context.compute import SolidExecutionContext
from dagster.core.execution.context.system import StepExecutionContext
from dagster.core.system_config.objects import ResolvedRunConfig
from dagster.utils import iterate_with_context

from .outputs import StepOutput, StepOutputProperties
from .utils import solid_execution_error_boundary

SolidOutputUnion = Union[
    DynamicOutput, Output, AssetMaterialization, Materialization, ExpectationResult
]


def create_step_outputs(
    solid: Node, handle: NodeHandle, resolved_run_config: ResolvedRunConfig
) -> List[StepOutput]:
    check.inst_param(solid, "solid", Node)
    check.inst_param(handle, "handle", NodeHandle)

    # the run config has the solid output name configured
    config_output_names: Set[str] = set()
    current_handle = handle
    while current_handle:
        solid_config = resolved_run_config.solids[current_handle.to_string()]
        current_handle = current_handle.parent
        config_output_names = config_output_names.union(solid_config.outputs.output_names)

    return [
        StepOutput(
            solid_handle=handle,
            name=output_def.name,
            dagster_type_key=output_def.dagster_type.key,
            properties=StepOutputProperties(
                is_required=output_def.is_required,
                is_dynamic=output_def.is_dynamic,
                is_asset=output_def.is_asset,
                should_materialize=output_def.name in config_output_names,
            ),
        )
        for name, output_def in solid.definition.output_dict.items()
    ]


def _validate_event(event: Any, solid_handle: NodeHandle) -> SolidOutputUnion:
    if not isinstance(
        event,
        (DynamicOutput, Output, AssetMaterialization, Materialization, ExpectationResult),
    ):
        raise DagsterInvariantViolationError(
            (
                "Compute function for solid {solid_name} yielded a value of type {type_} "
                "rather than an instance of Output, AssetMaterialization, or ExpectationResult."
                " Values yielded by solids must be wrapped in one of these types. If your "
                "solid has a single output and yields no other events, you may want to use "
                "`return` instead of `yield` in the body of your solid compute function. If "
                "you are already using `return`, and you expected to return a value of type "
                "{type_}, you may be inadvertently returning a generator rather than the value "
                "you expected."
            ).format(solid_name=str(solid_handle), type_=type(event))
        )

    return event


def gen_from_async_gen(async_gen: AsyncGenerator) -> Iterator:
    loop = asyncio.get_event_loop()
    while True:
        try:
            yield loop.run_until_complete(async_gen.__anext__())
        except StopAsyncIteration:
            return


def _yield_compute_results(
    step_context: StepExecutionContext, inputs: Dict[str, Any], compute_fn: Callable
) -> Iterator[SolidOutputUnion]:
    check.inst_param(step_context, "step_context", StepExecutionContext)

    user_event_generator = compute_fn(SolidExecutionContext(step_context), inputs)

    if isinstance(user_event_generator, Output):
        raise DagsterInvariantViolationError(
            (
                "Compute function for solid {solid_name} returned a Output rather than "
                "yielding it. The compute_fn of the core SolidDefinition must yield "
                "its results"
            ).format(solid_name=str(step_context.step.solid_handle))
        )

    if user_event_generator is None:
        return

    if inspect.isasyncgen(user_event_generator):
        user_event_generator = gen_from_async_gen(user_event_generator)

    for event in iterate_with_context(
        lambda: solid_execution_error_boundary(
            DagsterExecutionStepExecutionError,
            msg_fn=lambda: f'Error occurred while executing solid "{step_context.solid.name}":',
            step_context=step_context,
            step_key=step_context.step.key,
            solid_def_name=step_context.solid_def.name,
            solid_name=step_context.solid.name,
        ),
        user_event_generator,
    ):
        yield _validate_event(event, step_context.step.solid_handle)


def execute_core_compute(
    step_context: StepExecutionContext, inputs: Dict[str, Any], compute_fn
) -> Iterator[SolidOutputUnion]:
    """
    Execute the user-specified compute for the solid. Wrap in an error boundary and do
    all relevant logging and metrics tracking
    """
    check.inst_param(step_context, "step_context", StepExecutionContext)
    check.dict_param(inputs, "inputs", key_type=str)

    step = step_context.step

    all_results = []
    for step_output in _yield_compute_results(step_context, inputs, compute_fn):
        yield step_output
        if isinstance(step_output, (DynamicOutput, Output)):
            all_results.append(step_output)

    emitted_result_names = {r.output_name for r in all_results}
    solid_output_names = {output.name for output in step.step_outputs}
    omitted_outputs = solid_output_names.difference(emitted_result_names)
    if omitted_outputs:
        step_context.log.info(
            "Solid {solid} did not fire outputs {outputs}".format(
                solid=str(step.solid_handle), outputs=repr(omitted_outputs)
            )
        )
