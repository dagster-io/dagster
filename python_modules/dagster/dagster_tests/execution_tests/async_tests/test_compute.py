from collections.abc import Iterator

import dagster as dg
import pytest
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.execution.context.compute import ExecutionContextTypes
from dagster._core.execution.context.system import StepExecutionContext
from dagster._core.execution.plan.aio.compute import _yield_compute_results, execute_core_compute
from dagster._core.execution.plan.aio.compute_generator import create_op_compute_wrapper

from dagster_tests.execution_tests.async_tests.helpers import StepContextFactory


@pytest.mark.anyio
async def test_yield_compute_results_rejects_returned_output(
    simple_step_context: StepExecutionContext,
    simple_compute_context: ExecutionContextTypes,
) -> None:
    def compute_fn(_context, _inputs):
        return dg.Output(1)

    with pytest.raises(DagsterInvariantViolationError, match="returned an Output rather than"):
        async for result in _yield_compute_results(
            simple_step_context, {}, compute_fn, simple_compute_context
        ):
            pass


@pytest.mark.anyio
async def test_yield_compute_results_emits_logged_events_then_outputs(
    simple_step_context: StepExecutionContext,
    simple_compute_context: ExecutionContextTypes,
) -> None:
    def compute_fn(context, _inputs):
        context.log_event(dg.AssetMaterialization("logged"))
        yield dg.Output(1)

    events = _yield_compute_results(simple_step_context, {}, compute_fn, simple_compute_context)

    event = await anext(events)
    assert isinstance(event, DagsterEvent)
    assert event.event_type == DagsterEventType.ASSET_MATERIALIZATION
    event = await anext(events)
    assert isinstance(event, dg.Output)
    assert event.value == 1


@pytest.mark.anyio
async def test_yield_compute_results_handles_async_compute_fn(
    simple_step_context: StepExecutionContext,
    simple_compute_context: ExecutionContextTypes,
) -> None:
    async def compute_fn(context, _inputs):
        context.log_event(dg.AssetMaterialization("logged"))
        yield dg.Output(2)

    events = _yield_compute_results(simple_step_context, {}, compute_fn, simple_compute_context)

    event = await anext(events)
    assert isinstance(event, DagsterEvent)
    assert event.event_type == DagsterEventType.ASSET_MATERIALIZATION
    event = await anext(events)
    assert isinstance(event, dg.Output)
    assert event.value == 2


@pytest.mark.anyio
async def test_execute_core_compute_missing_output_with_typed_event_stream_raises(
    simple_step_context: StepExecutionContext,
    simple_compute_context: ExecutionContextTypes,
) -> None:
    simple_step_context.set_requires_typed_event_stream(error_message="extra info")

    def compute_fn(_context, _inputs):
        return iter([])

    with pytest.raises(
        DagsterInvariantViolationError,
        match="did not yield or return expected outputs",
    ) as excinfo:
        async for event in execute_core_compute(
            simple_step_context, {}, compute_fn, simple_compute_context
        ):
            pass

    assert "extra info" in str(excinfo.value)


@pytest.mark.anyio
async def test_execute_core_compute_counts_asset_and_check_outputs(
    asset_step_context: StepExecutionContext,
    asset_compute_context: ExecutionContextTypes,
) -> None:
    asset_step_context.set_requires_typed_event_stream()
    asset_key = asset_step_context.job_def.asset_layer.get_asset_key_for_node(
        asset_step_context.node_handle
    )
    check_result = dg.AssetCheckResult(
        asset_key=asset_key,
        check_name="asset_check",
        passed=True,
    )
    materialize_result = dg.MaterializeResult(
        asset_key=asset_key,
        check_results=[check_result],
    )

    def compute_fn(_context, _inputs):
        yield materialize_result

    results = execute_core_compute(asset_step_context, {}, compute_fn, asset_compute_context)

    assert await anext(results) == materialize_result


@pytest.mark.anyio
async def test_execute_core_compute_async_op_with_input(
    step_context_factory: StepContextFactory,
) -> None:
    @dg.op
    async def add_one() -> int:
        return 3

    @dg.job
    def async_job():
        add_one()

    from contextlib import contextmanager

    @contextmanager
    def _job_context(
        job_def: dg.JobDefinition, step_key: str
    ) -> Iterator[tuple[StepExecutionContext, ExecutionContextTypes]]:
        from dagster._core.execution.context.compute import enter_execution_context

        with step_context_factory(job_def, step_key=step_key) as step_context:
            with enter_execution_context(step_context) as compute_context:
                yield step_context, compute_context

    with _job_context(async_job, "add_one") as (step_context, compute_context):
        core_gen = await create_op_compute_wrapper(step_context.op_def)
        events = [
            event
            async for event in execute_core_compute(step_context, {}, core_gen, compute_context)
        ]

    values = [e.value for e in events if isinstance(e, dg.Output)]
    assert values == [3]
