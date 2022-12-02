import re
from dagster._core.definitions.job_definition import JobDefinition

import pytest
from dagster import (
    DagsterInvariantViolationError,
    DagsterTypeCheckDidNotPass,
    DependencyDefinition,
    MetadataEntry,
    Output,
    _check as check,
)
from dagster._core.definitions.decorators import op
from dagster._core.definitions.input import In
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.output import Out
from dagster._legacy import (
    JobDefinition,
    execute_pipeline,
    execute_solid,
    pipeline,
)
from dagster._utils.test import wrap_op_in_graph_and_execute


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


def test_compute_failure_job():
    job_def = JobDefinition(
        graph_def=GraphDefinition(
            node_defs=[create_root_fn_failure_op("failing")],
            name="test",
        )
    )
    result = job_def.execute_in_process(raise_on_error=False)

    assert not result.success

    result_list = result.node_result_list

    assert len(result_list) == 1
    assert not result_list[0].success
    assert result_list[0].failure_data


def test_failure_midstream():
    r"""
    A
     \\
       C (fails) = D (skipped)
     //
    B.
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

    assert result.output_for_node("op_a").success
    assert result.output_for_node("op_b").success
    assert not result.output_for_node("op_c").success
    assert (
        result.output_for_node("op_c").failure_data.error.cls_name
        == "DagsterExecutionStepExecutionError"
    )
    assert (
        result.output_for_node("op_c").failure_data.error.cause.cls_name == "CheckError"
    )
    assert not result.output_for_node("op_d").success
    assert result.output_for_node("op_d").skipped


def test_failure_propagation():
    r"""
      B =========== C
     //             \\
    A                F (skipped)
     \\             //
      D (fails) == E (skipped).
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

    assert result.output_for_node("op_a").success
    assert result.output_for_node("op_b").success
    assert result.output_for_node("op_c").success
    assert not result.output_for_node("op_d").success
    assert (
        result.output_for_node("op_d").failure_data.error.cause.cls_name == "CheckError"
    )
    assert not result.output_for_node("op_e").success
    assert result.output_for_node("op_e").skipped
    assert not result.output_for_node("op_f").success
    assert result.output_for_node("op_f").skipped


def test_do_not_yield_result():
    op_inst = OpDefinition(
        name="do_not_yield_result",
        outs={"result": Out()},
        compute_fn=lambda *_args, **_kwargs: Output("foo"),
    )

    with pytest.raises(
        DagsterInvariantViolationError,
        match='Compute function for op "do_not_yield_result" returned an Output',
    ):
        wrap_op_in_graph_and_execute(op_inst)


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
        wrap_op_in_graph_and_execute(yield_wrong_thing)


def test_single_compute_fn_returning_result():
    test_return_result = OpDefinition(
        name="test_return_result",
        compute_fn=lambda *args, **kwargs: Output(None),
        outs={"result": Out()},
    )

    with pytest.raises(DagsterInvariantViolationError):
        wrap_op_in_graph_and_execute(test_return_result)


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

    job_def = JobDefinition(
        graph_def=GraphDefinition(
            name="test_user_error_propogation",
            node_defs=[throws_user_error, return_one, add_one],
            dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
        )
    )

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
