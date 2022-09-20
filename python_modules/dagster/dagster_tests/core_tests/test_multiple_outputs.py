import pytest

from dagster import (
    Any,
    DagsterInvariantViolationError,
    DagsterStepOutputNotFoundError,
    In,
    Out,
    Output,
    execute_job,
    job,
    op,
    reconstructable,
)
from dagster._check import CheckError
from dagster._core.test_utils import instance_for_test
from dagster._utils.test import execute_op_for_test


def test_multiple_outputs():
    @op(
        name="multiple_outputs",
        ins={},
        out={"output_one": Out(), "output_two": Out()},
    )
    def multiple_outputs(_):
        yield Output(output_name="output_one", value="foo")
        yield Output(output_name="output_two", value="bar")

    @job
    def multiple_outputs_job():
        multiple_outputs()

    result = multiple_outputs_job.execute_in_process()
    assert result.output_for_node("multiple_outputs", output_name="output_one") == "foo"
    assert result.output_for_node("multiple_outputs", output_name="output_two") == "bar"

    with pytest.raises(DagsterInvariantViolationError):
        result.output_for_node("multiple_outputs", "not_defined")


def test_wrong_multiple_output():
    @op(
        name="multiple_outputs",
        ins={},
        out={"output_one": Out()},
    )
    def multiple_outputs(_):
        yield Output(output_name="mismatch", value="foo")

    @job
    def wrong_multiple_outputs_job():
        multiple_outputs()

    with pytest.raises(DagsterInvariantViolationError):
        wrong_multiple_outputs_job.execute_in_process()


def test_multiple_outputs_of_same_name_disallowed():
    # make this illegal until it is supported

    @op(
        name="multiple_outputs",
        ins={},
        out={"output_one": Out()},
    )
    def multiple_outputs(_):
        yield Output(output_name="output_one", value="foo")
        yield Output(output_name="output_one", value="foo")

    @job
    def muptiple_outputs_job():
        multiple_outputs()

    with pytest.raises(DagsterInvariantViolationError):
        muptiple_outputs_job.execute_in_process()


def define_multi_out():
    @op(
        name="multiple_outputs",
        ins={},
        out={"output_one": Out(), "output_two": Out(is_required=False)},
    )
    def multiple_outputs(_):
        yield Output(output_name="output_one", value="foo")

    @op(
        name="downstream_one",
        ins={"some_input": In()},
        out={},
    )
    def downstream_one(_, some_input):
        del some_input

    @op
    def downstream_two(_, some_input):
        del some_input
        raise Exception("do not call me")

    @job
    def multiple_outputs_only_emit_one_job():
        output_one, output_two = multiple_outputs()
        downstream_one(output_one)
        downstream_two(output_two)

    return multiple_outputs_only_emit_one_job


def test_multiple_outputs_only_emit_one():
    result = define_multi_out().execute_in_process()
    assert result.success

    output_events = result.filter_events(
        lambda evt: evt.step_key == "multiple_outputs" and evt.is_successful_output
    )
    assert len(output_events) == 1

    assert output_events[0].event_specific_data.step_output_handle.output_name == "output_one"

    with pytest.raises(CheckError):
        result.output_for_node("not_present")

    step_skipped_events = result.filter_events(lambda evt: evt.is_step_skipped)
    assert len(step_skipped_events) == 1
    assert step_skipped_events[0].step_key == "downstream_two"


def test_multiple_outputs_only_emit_one_multiproc():
    with instance_for_test() as instance:

        result = execute_job(reconstructable(define_multi_out), instance)
        assert result.success

        output_events = result.filter_events(
            lambda evt: evt.step_key == "multiple_outputs" and evt.is_successful_output
        )
        assert len(output_events) == 1

        with pytest.raises(CheckError):
            result.output_for_node("not_present")

        assert (
            len(
                result.filter_events(
                    lambda evt: evt.step_key == "downstream_two" and evt.is_step_skipped
                )
            )
            == 1
        )


def test_missing_non_optional_output_fails():
    @op(
        name="multiple_outputs",
        ins={},
        out={"output_one": Out(), "output_two": Out()},
    )
    def multiple_outputs(_):
        yield Output(output_name="output_one", value="foo")

    @job
    def missing_non_optional_job():
        multiple_outputs()

    with pytest.raises(DagsterStepOutputNotFoundError):
        missing_non_optional_job.execute_in_process()


def test_warning_for_conditional_output(capsys):
    @op(
        config_schema={"return": bool},
        out=Out(Any, is_required=False),
    )
    def maybe(context):
        if context.op_config["return"]:
            return 3

    result = execute_op_for_test(
        maybe, run_config={"ops": {"maybe": {"config": {"return": False}}}}
    )
    assert result.success
    assert "This value will be passed to downstream ops" in capsys.readouterr().err
