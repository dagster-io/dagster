import re

import pytest

from dagster import (
    DagsterInvariantViolationError,
    DagsterTypeCheckDidNotPass,
    DependencyDefinition,
    In,
    MetadataEntry,
    OpDefinition,
    Out,
    Output,
)
from dagster import _check as check
from dagster import op
from dagster._legacy import PipelineDefinition, execute_pipeline, execute_solid, pipeline


def create_root_success_solid(name):
    @op(name=name)
    def root_op(_context):
        passed_rows = []
        passed_rows.append({name: "compute_called"})
        return passed_rows

    return root_op


def create_root_fn_failure_solid(name):
    @op(name=name)
    def failed_op(_):
        raise Exception("Compute failed")

    return failed_op


def test_compute_failure_pipeline():
    pipeline_def = PipelineDefinition(
        solid_defs=[create_root_fn_failure_solid("failing")],
        name="test",
    )
    pipeline_result = execute_pipeline(pipeline_def, raise_on_error=False)

    assert not pipeline_result.success

    result_list = pipeline_result.solid_result_list

    assert len(result_list) == 1
    assert not result_list[0].success
    assert result_list[0].failure_data


def test_failure_midstream():
    """
    A
     \\
       C (fails) = D (skipped)
     //
    B
    """

    solid_a = create_root_success_solid("solid_a")
    op_b = create_root_success_solid("op_b")

    @op
    def op_c(_, a, b):
        check.failed("user error")
        return [a, b, {"C": "compute_called"}]

    @op
    def op_d(_, c):
        return [c, {"D": "compute_called"}]

    @pipeline
    def pipeline_def():
        op_d(op_c(solid_a(), op_b()))

    pipeline_result = execute_pipeline(pipeline_def, raise_on_error=False)

    assert pipeline_result.result_for_solid("solid_a").success
    assert pipeline_result.result_for_solid("op_b").success
    assert not pipeline_result.result_for_solid("op_c").success
    assert (
        pipeline_result.result_for_solid("op_c").failure_data.error.cls_name
        == "DagsterExecutionStepExecutionError"
    )
    assert (
        pipeline_result.result_for_solid("op_c").failure_data.error.cause.cls_name == "CheckError"
    )
    assert not pipeline_result.result_for_solid("op_d").success
    assert pipeline_result.result_for_solid("op_d").skipped


def test_failure_propagation():
    """
      B =========== C
     //             \\
    A                F (skipped)
     \\             //
      D (fails) == E (skipped)
    """

    solid_a = create_root_success_solid("solid_a")

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

    @pipeline
    def pipeline_def():
        a_result = solid_a()
        op_f(op_c(op_b(a_result)), op_e(op_d(a_result)))

    pipeline_result = execute_pipeline(pipeline_def, raise_on_error=False)

    assert pipeline_result.result_for_solid("solid_a").success
    assert pipeline_result.result_for_solid("op_b").success
    assert pipeline_result.result_for_solid("op_c").success
    assert not pipeline_result.result_for_solid("op_d").success
    assert (
        pipeline_result.result_for_solid("op_d").failure_data.error.cause.cls_name == "CheckError"
    )
    assert not pipeline_result.result_for_solid("op_e").success
    assert pipeline_result.result_for_solid("op_e").skipped
    assert not pipeline_result.result_for_solid("op_f").success
    assert pipeline_result.result_for_solid("op_f").skipped


def test_do_not_yield_result():
    solid_inst = OpDefinition(
        name="do_not_yield_result",
        ins={},
        outs={"result": Out()},
        compute_fn=lambda *_args, **_kwargs: Output("foo"),
    )

    with pytest.raises(
        DagsterInvariantViolationError,
        match='Compute function for op "do_not_yield_result" returned an Output',
    ):
        execute_solid(solid_inst)


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
        execute_solid(yield_wrong_thing)


def test_single_compute_fn_returning_result():
    test_return_result = OpDefinition(
        name="test_return_result",
        ins={},
        compute_fn=lambda *args, **kwargs: Output(None),
        outs={"result": Out()},
    )

    with pytest.raises(DagsterInvariantViolationError):
        execute_solid(test_return_result)


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

    pipeline_def = PipelineDefinition(
        name="test_user_error_propogation",
        solid_defs=[throws_user_error, return_one, add_one],
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
    )

    with pytest.raises(UserError) as e_info:
        execute_pipeline(pipeline_def)

    assert isinstance(e_info.value, UserError)


def test_explicit_failure():
    @op
    def throws_failure():
        raise DagsterTypeCheckDidNotPass(
            description="Always fails.",
            metadata_entries=[MetadataEntry("always_fails", value="why")],
        )

    @pipeline
    def pipe():
        throws_failure()

    with pytest.raises(DagsterTypeCheckDidNotPass) as exc_info:
        execute_pipeline(pipe)

    assert exc_info.value.description == "Always fails."
    assert exc_info.value.metadata_entries == [MetadataEntry("always_fails", value="why")]
