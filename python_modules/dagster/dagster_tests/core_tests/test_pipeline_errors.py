import re

import pytest
from dagster import (
    DagsterInvariantViolationError,
    DagsterTypeCheckDidNotPass,
    DependencyDefinition,
    EventMetadataEntry,
    InputDefinition,
    Output,
    OutputDefinition,
    PipelineDefinition,
    SolidDefinition,
    check,
    execute_pipeline,
    execute_solid,
    lambda_solid,
    pipeline,
    solid,
)


def create_root_success_solid(name):
    @solid(name=name)
    def root_solid(_context):
        passed_rows = []
        passed_rows.append({name: "compute_called"})
        return passed_rows

    return root_solid


def create_root_fn_failure_solid(name):
    @solid(name=name)
    def failed_solid(_):
        raise Exception("Compute failed")

    return failed_solid


def test_compute_failure_pipeline():
    pipeline_def = PipelineDefinition(solid_defs=[create_root_fn_failure_solid("failing")])
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
    solid_b = create_root_success_solid("solid_b")

    @solid
    def solid_c(_, a, b):
        check.failed("user error")
        return [a, b, {"C": "compute_called"}]

    @solid
    def solid_d(_, c):
        return [c, {"D": "compute_called"}]

    @pipeline
    def pipeline_def():
        solid_d(solid_c(solid_a(), solid_b()))

    pipeline_result = execute_pipeline(pipeline_def, raise_on_error=False)

    assert pipeline_result.result_for_solid("solid_a").success
    assert pipeline_result.result_for_solid("solid_b").success
    assert not pipeline_result.result_for_solid("solid_c").success
    assert pipeline_result.result_for_solid("solid_c").failure_data.error.cls_name == "CheckError"
    assert not pipeline_result.result_for_solid("solid_d").success
    assert pipeline_result.result_for_solid("solid_d").skipped


def test_failure_propagation():
    """
      B =========== C
     //             \\
    A                F (skipped)
     \\             //
      D (fails) == E (skipped)
    """

    solid_a = create_root_success_solid("solid_a")

    @solid
    def solid_b(_, in_):
        return in_

    @solid
    def solid_c(_, in_):
        return in_

    @solid
    def solid_d(_, _in):
        check.failed("user error")

    @solid
    def solid_e(_, in_):
        return in_

    @solid
    def solid_f(_, in_, _in2):
        return in_

    @pipeline
    def pipeline_def():
        a_result = solid_a()
        solid_f(solid_c(solid_b(a_result)), solid_e(solid_d(a_result)))

    pipeline_result = execute_pipeline(pipeline_def, raise_on_error=False)

    assert pipeline_result.result_for_solid("solid_a").success
    assert pipeline_result.result_for_solid("solid_b").success
    assert pipeline_result.result_for_solid("solid_c").success
    assert not pipeline_result.result_for_solid("solid_d").success
    assert pipeline_result.result_for_solid("solid_d").failure_data.error.cls_name == "CheckError"
    assert not pipeline_result.result_for_solid("solid_e").success
    assert pipeline_result.result_for_solid("solid_e").skipped
    assert not pipeline_result.result_for_solid("solid_f").success
    assert pipeline_result.result_for_solid("solid_f").skipped


def test_do_not_yield_result():
    solid_inst = SolidDefinition(
        name="do_not_yield_result",
        input_defs=[],
        output_defs=[OutputDefinition()],
        compute_fn=lambda *_args, **_kwargs: Output("foo"),
    )

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Compute function for solid do_not_yield_result returned a Output",
    ):
        execute_solid(solid_inst)


def test_yield_non_result():
    @solid
    def yield_wrong_thing(_):
        yield "foo"

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape("Compute function for solid yield_wrong_thing yielded a value of type <")
        + r"(class|type)"
        + re.escape(
            " 'str'> rather than an instance of Output, AssetMaterialization, or ExpectationResult."
        ),
    ):
        execute_solid(yield_wrong_thing)


def test_single_compute_fn_returning_result():
    test_return_result = SolidDefinition(
        name="test_return_result",
        input_defs=[],
        compute_fn=lambda *args, **kwargs: Output(None),
        output_defs=[OutputDefinition()],
    )

    with pytest.raises(DagsterInvariantViolationError):
        execute_solid(test_return_result)


def test_user_error_propogation():
    err_msg = "the user has errored"

    class UserError(Exception):
        pass

    @lambda_solid
    def throws_user_error():
        raise UserError(err_msg)

    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(input_defs=[InputDefinition("num")])
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
    @lambda_solid
    def throws_failure():
        raise DagsterTypeCheckDidNotPass(
            description="Always fails.",
            metadata_entries=[EventMetadataEntry.text("why", label="always_fails")],
        )

    @pipeline
    def pipe():
        throws_failure()

    with pytest.raises(DagsterTypeCheckDidNotPass) as exc_info:
        execute_pipeline(pipe)

    assert exc_info.value.description == "Always fails."
    assert exc_info.value.metadata_entries == [EventMetadataEntry.text("why", label="always_fails")]
