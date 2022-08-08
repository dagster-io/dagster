from dagster import Field, Out, Output, String
from dagster import _check as check
from dagster import op
from dagster._legacy import execute_pipeline, pipeline


def define_pass_value_solid(name, description=None):
    check.str_param(name, "name")
    check.opt_str_param(description, "description")

    @op(
        name=name,
        description=description,
        ins={},
        out=Out(String),
        config_schema={"value": Field(String)},
    )
    def pass_value_op(context):
        yield Output(context.op_config["value"])

    return pass_value_op


def test_execute_solid_with_input_same_name():
    @op(out=Out())
    def a_thing(_, a_thing):
        return a_thing + a_thing

    @pipeline
    def pipe():
        pass_value = define_pass_value_solid("pass_value")
        a_thing(pass_value())

    result = execute_pipeline(
        pipe, run_config={"solids": {"pass_value": {"config": {"value": "foo"}}}}
    )

    assert result.result_for_solid("a_thing").output_value() == "foofoo"


def test_execute_two_solids_with_same_input_name():
    @op
    def op_one(_, a_thing):
        return a_thing + a_thing

    @op
    def op_two(_, a_thing):
        return a_thing + a_thing

    @pipeline
    def pipe():
        op_one(define_pass_value_solid("pass_to_one")())
        op_two(define_pass_value_solid("pass_to_two")())

    result = execute_pipeline(
        pipe,
        run_config={
            "solids": {
                "pass_to_one": {"config": {"value": "foo"}},
                "pass_to_two": {"config": {"value": "bar"}},
            }
        },
    )

    assert result.success
    assert result.result_for_solid("op_one").output_value() == "foofoo"
    assert result.result_for_solid("op_two").output_value() == "barbar"


def test_execute_dep_solid_different_input_name():
    pass_to_first = define_pass_value_solid("pass_to_first")

    @op
    def first_op(_, a_thing):
        return a_thing + a_thing

    @op
    def second_op(_, an_input):
        return an_input + an_input

    @pipeline
    def pipe():
        second_op(first_op(pass_to_first()))

    result = execute_pipeline(
        pipe, run_config={"solids": {"pass_to_first": {"config": {"value": "bar"}}}}
    )

    assert result.success
    assert len(result.solid_result_list) == 3
    assert result.result_for_solid("pass_to_first").output_value() == "bar"
    assert result.result_for_solid("first_op").output_value() == "barbar"
    assert result.result_for_solid("second_op").output_value() == "barbarbarbar"
