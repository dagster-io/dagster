import re

import pytest

from dagster import (
    DagsterInvariantViolationError,
    DagsterTypeCheckDidNotPass,
    DependencyDefinition,
    GraphDefinition,
    In,
    MetadataEntry,
    OpDefinition,
    Out,
    Output,
)
from dagster import _check as check
from dagster import job, op
from dagster._utils.test import execute_op_for_test


def did_op_succeed(op_name, result):
    return (
        len(result.filter_events(lambda evt: evt.step_key == op_name and evt.is_step_success)) == 1
    )


def did_op_fail(op_name, result):
    return (
        len(result.filter_events(lambda evt: evt.step_key == op_name and evt.is_step_failure)) == 1
    )


def did_op_skip(op_name, error_log):
    return (
        f"Dependencies for step {op_name} failed" in error_log
        or f"Dependencies for step {op_name} were not executed" in error_log
    )


def create_root_success_op(name):
    @op(name=name)
    def root_op(_context):
        passed_rows = []
        passed_rows.append({name: "compute_called"})
        return passed_rows

    return root_op


def create_root_fn_failure_op(name):
    @op(name=name)
    def failed_op(_):
        raise Exception("Compute failed")

    return failed_op


def test_compute_failure_pipeline():
    job_def = GraphDefinition(
        node_defs=[create_root_fn_failure_op("failing")],
        name="test",
    ).to_job()
    result = job_def.execute_in_process(raise_on_error=False)

    assert not result.success

    assert len(result.filter_events(lambda evt: evt.is_step_success)) == 0
    assert len(result.filter_events(lambda evt: evt.is_step_failure)) == 1


def test_failure_midstream(capsys):
    """
    A
     \\
       C (fails) = D (skipped)
     //
    B
    """

    op_a = create_root_success_op("op_a")
    op_b = create_root_success_op("op_b")

    @op
    def op_c(_, a, b):
        check.failed("user error")
        return [a, b, {"C": "compute_called"}]

    @op
    def op_d(_, c):
        return [c, {"D": "compute_called"}]

    @job
    def job_def():
        op_d(op_c(op_a(), op_b()))

    result = job_def.execute_in_process(raise_on_error=False)

    assert not result.success
    assert (
        len(result.filter_events(lambda evt: evt.step_key == "op_a" and evt.is_step_success)) == 1
    )
    assert (
        len(result.filter_events(lambda evt: evt.step_key == "op_b" and evt.is_step_success)) == 1
    )
    failure_events = result.filter_events(
        lambda evt: evt.step_key == "op_c" and evt.is_step_failure
    )
    assert len(failure_events) == 1

    failure_event = failure_events.pop()

    assert failure_event.step_failure_data.error.cls_name == "DagsterExecutionStepExecutionError"

    assert failure_event.step_failure_data.error.cause.cls_name == "CheckError"
    assert (
        len(
            result.filter_events(
                lambda evt: evt.step_key == "op_d" and (evt.is_step_failure or evt.is_step_success)
            )
        )
        == 0
    )
    assert did_op_skip("op_d", capsys.readouterr().err)

    # Demonstrate that no step-skip event is launched off for op d
    assert (
        len(result.filter_events(lambda evt: evt.step_key == "op_d" and evt.is_step_skipped)) == 0
    )


def test_failure_propagation(capsys):
    """
      B =========== C
     //             \\
    A                F (skipped)
     \\             //
      D (fails) == E (skipped)
    """

    op_a = create_root_success_op("op_a")

    @op
    def op_b(_, in_):
        return in_

    @op
    def op_c(_, in_):
        return in_

    @op
    def op_d(_, _in):
        check.failed("user error")

    @op
    def op_e(_, in_):
        return in_

    @op
    def op_f(_, in_, _in2):
        return in_

    @job
    def job_def():
        a_result = op_a()
        op_f(op_c(op_b(a_result)), op_e(op_d(a_result)))

    result = job_def.execute_in_process(raise_on_error=False)

    assert did_op_succeed("op_a", result)
    assert did_op_succeed("op_b", result)
    assert did_op_succeed("op_c", result)
    assert did_op_fail("op_d", result)

    failure_events = result.filter_events(
        lambda evt: evt.step_key == "op_d" and evt.is_step_failure
    )
    assert len(failure_events) == 1

    failure_event = failure_events.pop()

    assert failure_event.step_failure_data.error.cause.cls_name == "CheckError"

    err_logs = capsys.readouterr().err
    assert did_op_skip("op_e", err_logs)
    assert did_op_skip("op_f", err_logs)

    # Demonstrate that no step-skip event is launched off for op e
    assert (
        len(result.filter_events(lambda evt: evt.step_key == "op_e" and evt.is_step_skipped)) == 0
    )

    # Demonstrate that no step-skip event is launched off for op f
    assert (
        len(result.filter_events(lambda evt: evt.step_key == "op_f" and evt.is_step_skipped)) == 0
    )


def test_do_not_yield_result():

    op_inst = OpDefinition(
        name="do_not_yield_result",
        ins={},
        outs={"result": Out()},
        compute_fn=lambda *_args, **_kwargs: Output("foo"),
    )

    with pytest.raises(
        DagsterInvariantViolationError,
        match='Compute function for op "do_not_yield_result" returned an Output',
    ):
        execute_op_for_test(op_inst)


def test_yield_non_result():
    @op
    def yield_wrong_thing(_):
        yield "foo"

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape('Compute function for op "yield_wrong_thing" yielded a value of type <')
        + r"(class|type)"
        + re.escape(
            " 'str'> rather than an instance of Output, AssetMaterialization, or ExpectationResult."
        ),
    ):
        execute_op_for_test(yield_wrong_thing)


def test_single_compute_fn_returning_result():
    test_return_result = OpDefinition(
        name="test_return_result",
        ins={},
        compute_fn=lambda *args, **kwargs: Output(None),
    )

    with pytest.raises(DagsterInvariantViolationError):
        execute_op_for_test(test_return_result)


def test_user_error_propogation():
    err_msg = "the user has errored"

    class UserError(Exception):
        pass

    @op
    def throws_user_error():
        raise UserError(err_msg)

    @op
    def return_one():
        return 1

    @op(ins={"num": In()})
    def add_one(num):
        return num + 1

    job_def = GraphDefinition(
        name="test_user_error_propogation",
        node_defs=[throws_user_error, return_one, add_one],
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
    ).to_job()

    with pytest.raises(UserError) as e_info:
        job_def.execute_in_process()

    assert isinstance(e_info.value, UserError)


def test_explicit_failure():
    @op
    def throws_failure():
        raise DagsterTypeCheckDidNotPass(
            description="Always fails.",
            metadata_entries=[MetadataEntry("always_fails", value="why")],
        )

    @job
    def pipe():
        throws_failure()

    with pytest.raises(DagsterTypeCheckDidNotPass) as exc_info:
        pipe.execute_in_process()

    assert exc_info.value.description == "Always fails."
    assert exc_info.value.metadata_entries == [MetadataEntry("always_fails", value="why")]
