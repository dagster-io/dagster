from collections.abc import Iterator
from contextlib import contextmanager

import dagster as dg
import pytest
from dagster import OpExecutionContext
from dagster._utils.test import wrap_op_in_graph_and_execute

EXTRA_ERROR_MESSAGE = "Hello"


@contextmanager
def raises_missing_output_error() -> Iterator[None]:
    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=f"did not yield or return expected outputs.*{EXTRA_ERROR_MESSAGE}$",
    ):
        yield


@contextmanager
def raises_missing_check_output_error() -> Iterator[None]:
    with pytest.raises(
        dg.DagsterStepOutputNotFoundError,
        match="did not return an output for non-optional output",
    ):
        yield


def test_requires_typed_event_stream_op():
    @dg.op
    def op_fails(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)

    with raises_missing_output_error():
        wrap_op_in_graph_and_execute(op_fails)

    @dg.op(out={"a": dg.Out(int), "b": dg.Out(int)})
    def op_fails_partial_yield(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield dg.Output(1, output_name="a")

    with raises_missing_output_error():
        wrap_op_in_graph_and_execute(op_fails_partial_yield)

    @dg.op(out={"a": dg.Out(int), "b": dg.Out(int)})
    def op_fails_partial_return(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield dg.Output(1, output_name="a")

    with raises_missing_output_error():
        wrap_op_in_graph_and_execute(op_fails_partial_return)

    @dg.op(out={"a": dg.Out(int), "b": dg.Out(int)})
    def op_succeeds_yield(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield dg.Output(1, output_name="a")
        yield dg.Output(2, output_name="b")

    assert wrap_op_in_graph_and_execute(op_succeeds_yield)

    @dg.op(out={"a": dg.Out(int), "b": dg.Out(int)})
    def op_succeeds_return(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        return dg.Output(1, output_name="a"), dg.Output(2, output_name="b")

    assert wrap_op_in_graph_and_execute(op_succeeds_return)


def test_requires_typed_event_stream_asset():
    @dg.asset
    def asset_fails(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)

    with raises_missing_output_error():
        dg.materialize([asset_fails])

    @dg.asset
    def asset_succeeds_output_yield(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield dg.Output(1)

    assert dg.materialize([asset_succeeds_output_yield])

    @dg.asset
    def asset_succeeds_output_return(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        return dg.Output(1)

    assert dg.materialize([asset_succeeds_output_return])

    @dg.asset
    def asset_succeeds_materialize_result_yield(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield dg.MaterializeResult()

    assert dg.materialize([asset_succeeds_materialize_result_yield])

    @dg.asset
    def asset_succeeds_materialize_result_return(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        return dg.MaterializeResult()

    assert dg.materialize([asset_succeeds_materialize_result_return])

    @dg.asset(
        check_specs=[
            dg.AssetCheckSpec(
                name="foo", asset=dg.AssetKey(["asset_succeeds_check_separate_yield"])
            )
        ]
    )
    def asset_succeeds_check_separate_yield(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield dg.MaterializeResult()
        yield dg.AssetCheckResult(passed=True)

    assert dg.materialize([asset_succeeds_check_separate_yield])

    @dg.asset(
        check_specs=[
            dg.AssetCheckSpec(
                name="foo", asset=dg.AssetKey(["asset_succeeds_check_separate_return"])
            )
        ]
    )
    def asset_succeeds_check_separate_return(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        return dg.MaterializeResult(), dg.AssetCheckResult(passed=True)

    assert dg.materialize([asset_succeeds_check_separate_return])

    @dg.asset(
        check_specs=[
            dg.AssetCheckSpec(
                name="foo", asset=dg.AssetKey(["asset_succeeds_check_embedded_yield"])
            )
        ]
    )
    def asset_succeeds_check_embedded_yield(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield dg.MaterializeResult(check_results=[dg.AssetCheckResult(passed=True)])

    assert dg.materialize([asset_succeeds_check_embedded_yield])

    @dg.asset(
        check_specs=[
            dg.AssetCheckSpec(
                name="foo", asset=dg.AssetKey(["asset_succeeds_check_embedded_return"])
            )
        ]
    )
    def asset_succeeds_check_embedded_return(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        return dg.MaterializeResult(check_results=[dg.AssetCheckResult(passed=True)])

    assert dg.materialize([asset_succeeds_check_embedded_return])

    @dg.asset(
        check_specs=[
            dg.AssetCheckSpec(name="foo", asset=dg.AssetKey(["asset_fails_missing_check_yield"]))
        ]
    )
    def asset_fails_missing_check_yield(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield dg.MaterializeResult()

    # with raises_missing_check_output_error():
    with raises_missing_output_error():
        dg.materialize([asset_fails_missing_check_yield])

    @dg.asset(
        check_specs=[
            dg.AssetCheckSpec(name="foo", asset=dg.AssetKey(["asset_fails_missing_check_return"]))
        ]
    )
    def asset_fails_missing_check_return(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        return dg.MaterializeResult()

    # with raises_missing_check_output_error():
    with raises_missing_output_error():
        dg.materialize([asset_fails_missing_check_return])


def test_requires_typed_event_stream_multi_asset():
    @dg.multi_asset(specs=[dg.AssetSpec("foo"), dg.AssetSpec("bar")])
    def asset_fails_multi_asset(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield dg.Output(None, output_name="foo")

    with raises_missing_output_error():
        dg.materialize([asset_fails_multi_asset])

    @dg.multi_asset(specs=[dg.AssetSpec("foo"), dg.AssetSpec("bar")])
    def asset_succeeds_multi_asset_yield(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield dg.Output(None, output_name="foo")
        yield dg.Output(None, output_name="bar")

    assert dg.materialize([asset_succeeds_multi_asset_yield])

    @dg.multi_asset(specs=[dg.AssetSpec("foo"), dg.AssetSpec("bar")])
    def asset_succeeds_multi_asset_return(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        return dg.Output(None, output_name="foo"), dg.Output(None, output_name="bar")

    assert dg.materialize([asset_succeeds_multi_asset_return])


def test_requires_typed_event_stream_subsettable_multi_asset():
    @dg.multi_asset(
        specs=[dg.AssetSpec("foo", skippable=True), dg.AssetSpec("bar", skippable=True)],
        can_subset=True,
    )
    def asset_subsettable_single(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield dg.Output(None, output_name="foo")

    dg.materialize([asset_subsettable_single], selection=["foo"])

    @dg.multi_asset(
        specs=[dg.AssetSpec("foo", skippable=True), dg.AssetSpec("bar", skippable=True)],
        can_subset=True,
    )
    def asset_subsettable_none(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)

    with raises_missing_output_error():
        dg.materialize([asset_subsettable_none], selection=["bar"])
