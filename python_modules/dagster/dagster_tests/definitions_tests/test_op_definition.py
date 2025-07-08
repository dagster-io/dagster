import sys

import dagster as dg
import pytest


def test_op_def_direct():
    def the_op_fn(_, inputs):
        assert inputs["x"] == 5
        yield dg.Output(inputs["x"] + 1, output_name="the_output")

    op_def = dg.OpDefinition(
        the_op_fn, "the_op", ins={"x": dg.In(dagster_type=int)}, outs={"the_output": dg.Out(int)}
    )

    @dg.job
    def the_job(x):
        op_def(x)

    result = the_job.execute_in_process(input_values={"x": 5})
    assert result.success


def test_multi_out_implicit_none():
    #
    # non-optional Nothing
    #
    @dg.op(out={"a": dg.Out(dg.Nothing), "b": dg.Out(dg.Nothing)})
    def implicit():
        pass

    implicit()

    @dg.job
    def implicit_job():
        implicit()

    result = implicit_job.execute_in_process()
    assert result.success

    #
    # optional (fails)
    #
    @dg.op(out={"a": dg.Out(dg.Nothing), "b": dg.Out(dg.Nothing, is_required=False)})
    def optional():
        pass

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        optional()

    @dg.job
    def optional_job():
        optional()

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        optional_job.execute_in_process()

    #
    # untyped (fails)
    #
    @dg.op(out={"a": dg.Out(), "b": dg.Out()})
    def untyped():
        pass

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        untyped()

    @dg.job
    def untyped_job():
        untyped()

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        untyped_job.execute_in_process()


@pytest.mark.skipif(sys.version_info < (3, 10), reason="| operator Python 3.10 or higher")
def test_pipe_union_optional():
    # union is not yet supported, but you can express optional as union of T and None
    @dg.op
    def pipe_union(thing: str | None) -> str | None:  # type: ignore
        return thing

    assert pipe_union
