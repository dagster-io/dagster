import pytest
from dagster import DagsterInvariantViolationError, In, Nothing, OpDefinition, Out, Output, job, op


def test_op_def_direct():
    def the_op_fn(_, inputs):
        assert inputs["x"] == 5
        yield Output(inputs["x"] + 1, output_name="the_output")

    op_def = OpDefinition(
        the_op_fn, "the_op", ins={"x": In(dagster_type=int)}, outs={"the_output": Out(int)}
    )

    @job
    def the_job(x):
        op_def(x)

    result = the_job.execute_in_process(input_values={"x": 5})
    assert result.success


def test_multi_out_implicit_none():
    #
    # non-optional Nothing
    #
    @op(out={"a": Out(Nothing), "b": Out(Nothing)})
    def implicit():
        pass

    implicit()

    @job
    def implicit_job():
        implicit()

    result = implicit_job.execute_in_process()
    assert result.success

    #
    # optional (fails)
    #
    @op(out={"a": Out(Nothing), "b": Out(Nothing, is_required=False)})
    def optional():
        pass

    with pytest.raises(
        DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        optional()

    @job
    def optional_job():
        optional()

    with pytest.raises(
        DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        optional_job.execute_in_process()

    #
    # untyped (fails)
    #
    @op(out={"a": Out(), "b": Out()})
    def untyped():
        pass

    with pytest.raises(
        DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        untyped()

    @job
    def untyped_job():
        untyped()

    with pytest.raises(
        DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        untyped_job.execute_in_process()
