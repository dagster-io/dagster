import dagster as dg
import pytest
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.execution.plan.compute import (
    _yield_compute_results,
    execute_core_compute,
    gen_from_async_gen,
)


def test_gen_from_async_gen_yields_all_values(simple_step_context):
    async def numbers():
        for value in (1, 2, 3):
            yield value

    assert list(gen_from_async_gen(simple_step_context, numbers())) == [1, 2, 3]


def test_yield_compute_results_rejects_returned_output(simple_step_context, simple_compute_context):
    def compute_fn(_context, _inputs):
        return dg.Output(1)

    with pytest.raises(DagsterInvariantViolationError, match="returned an Output rather than"):
        list(_yield_compute_results(simple_step_context, {}, compute_fn, simple_compute_context))


def test_yield_compute_results_emits_logged_events_then_outputs(
    simple_step_context, simple_compute_context
):
    def compute_fn(context, _inputs):
        context.log_event(dg.AssetMaterialization("logged"))
        yield dg.Output(1)

    events = list(
        _yield_compute_results(simple_step_context, {}, compute_fn, simple_compute_context)
    )
    assert isinstance(events[0], DagsterEvent)
    assert events[0].event_type == DagsterEventType.ASSET_MATERIALIZATION
    assert isinstance(events[1], dg.Output)
    assert events[1].value == 1


def test_execute_core_compute_missing_output_with_typed_event_stream_raises(
    simple_step_context, simple_compute_context
):
    simple_step_context.set_requires_typed_event_stream(error_message="extra info")

    def compute_fn(_context, _inputs):
        return iter([])

    with pytest.raises(
        DagsterInvariantViolationError,
        match="did not yield or return expected outputs",
    ) as excinfo:
        list(execute_core_compute(simple_step_context, {}, compute_fn, simple_compute_context))

    assert "extra info" in str(excinfo.value)


def test_execute_core_compute_counts_asset_and_check_outputs(
    asset_step_context, asset_compute_context
):
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

    assert list(
        execute_core_compute(asset_step_context, {}, compute_fn, asset_compute_context)
    ) == [materialize_result]
