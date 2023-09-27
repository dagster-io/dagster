from contextlib import contextmanager
from typing import Iterator

import pytest
from dagster import OpExecutionContext, Out, asset, multi_asset, op
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.events import AssetKey, Output
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.result import MaterializeResult
from dagster._core.errors import DagsterInvariantViolationError, DagsterStepOutputNotFoundError
from dagster._utils.test import wrap_op_in_graph_and_execute

EXTRA_ERROR_MESSAGE = "Hello"


@contextmanager
def raises_missing_output_error() -> Iterator[None]:
    with pytest.raises(
        DagsterInvariantViolationError,
        match=f"did not yield or return expected outputs.*{EXTRA_ERROR_MESSAGE}$",
    ):
        yield


@contextmanager
def raises_missing_check_output_error() -> Iterator[None]:
    with pytest.raises(
        DagsterStepOutputNotFoundError,
        match="did not return an output for non-optional output",
    ):
        yield


def test_requires_typed_event_stream_op():
    @op
    def op_fails(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)

    with raises_missing_output_error():
        wrap_op_in_graph_and_execute(op_fails)

    @op(out={"a": Out(int), "b": Out(int)})
    def op_fails_partial_yield(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield Output(1, output_name="a")

    with raises_missing_output_error():
        wrap_op_in_graph_and_execute(op_fails_partial_yield)

    @op(out={"a": Out(int), "b": Out(int)})
    def op_fails_partial_return(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield Output(1, output_name="a")

    with raises_missing_output_error():
        wrap_op_in_graph_and_execute(op_fails_partial_return)

    @op(out={"a": Out(int), "b": Out(int)})
    def op_succeeds_yield(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield Output(1, output_name="a")
        yield Output(2, output_name="b")

    assert wrap_op_in_graph_and_execute(op_succeeds_yield)

    @op(out={"a": Out(int), "b": Out(int)})
    def op_succeeds_return(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        return Output(1, output_name="a"), Output(2, output_name="b")

    assert wrap_op_in_graph_and_execute(op_succeeds_return)


def test_requires_typed_event_stream_asset():
    @asset
    def asset_fails(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)

    with raises_missing_output_error():
        materialize([asset_fails])

    @asset
    def asset_succeeds_output_yield(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield Output(1)

    assert materialize([asset_succeeds_output_yield])

    @asset
    def asset_succeeds_output_return(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        return Output(1)

    assert materialize([asset_succeeds_output_return])

    @asset
    def asset_succeeds_materialize_result_yield(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield MaterializeResult()

    assert materialize([asset_succeeds_materialize_result_yield])

    @asset
    def asset_succeeds_materialize_result_return(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        return MaterializeResult()

    assert materialize([asset_succeeds_materialize_result_return])

    @asset(
        check_specs=[
            AssetCheckSpec(name="foo", asset=AssetKey(["asset_succeeds_check_separate_yield"]))
        ]
    )
    def asset_succeeds_check_separate_yield(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield MaterializeResult()
        yield AssetCheckResult(passed=True)

    assert materialize([asset_succeeds_check_separate_yield])

    @asset(
        check_specs=[
            AssetCheckSpec(name="foo", asset=AssetKey(["asset_succeeds_check_separate_return"]))
        ]
    )
    def asset_succeeds_check_separate_return(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        return MaterializeResult(), AssetCheckResult(passed=True)

    assert materialize([asset_succeeds_check_separate_return])

    @asset(
        check_specs=[
            AssetCheckSpec(name="foo", asset=AssetKey(["asset_succeeds_check_embedded_yield"]))
        ]
    )
    def asset_succeeds_check_embedded_yield(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield MaterializeResult(check_results=[AssetCheckResult(passed=True)])

    assert materialize([asset_succeeds_check_embedded_yield])

    @asset(
        check_specs=[
            AssetCheckSpec(name="foo", asset=AssetKey(["asset_succeeds_check_embedded_return"]))
        ]
    )
    def asset_succeeds_check_embedded_return(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        return MaterializeResult(check_results=[AssetCheckResult(passed=True)])

    assert materialize([asset_succeeds_check_embedded_return])

    @asset(
        check_specs=[
            AssetCheckSpec(name="foo", asset=AssetKey(["asset_fails_missing_check_yield"]))
        ]
    )
    def asset_fails_missing_check_yield(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield MaterializeResult()

    # with raises_missing_check_output_error():
    with raises_missing_output_error():
        materialize([asset_fails_missing_check_yield])

    @asset(
        check_specs=[
            AssetCheckSpec(name="foo", asset=AssetKey(["asset_fails_missing_check_return"]))
        ]
    )
    def asset_fails_missing_check_return(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        return MaterializeResult()

    # with raises_missing_check_output_error():
    with raises_missing_output_error():
        materialize([asset_fails_missing_check_return])


def test_requires_typed_event_stream_multi_asset():
    @multi_asset(specs=[AssetSpec("foo"), AssetSpec("bar")])
    def asset_fails_multi_asset(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield Output(None, output_name="foo")

    with raises_missing_output_error():
        materialize([asset_fails_multi_asset])

    @multi_asset(specs=[AssetSpec("foo"), AssetSpec("bar")])
    def asset_succeeds_multi_asset_yield(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        yield Output(None, output_name="foo")
        yield Output(None, output_name="bar")

    assert materialize([asset_succeeds_multi_asset_yield])

    @multi_asset(specs=[AssetSpec("foo"), AssetSpec("bar")])
    def asset_succeeds_multi_asset_return(context: OpExecutionContext):
        context.set_requires_typed_event_stream(error_message=EXTRA_ERROR_MESSAGE)
        return Output(None, output_name="foo"), Output(None, output_name="bar")

    assert materialize([asset_succeeds_multi_asset_return])
