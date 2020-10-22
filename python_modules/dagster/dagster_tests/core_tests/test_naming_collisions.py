from dagster import (
    Field,
    Output,
    OutputDefinition,
    String,
    check,
    execute_pipeline,
    pipeline,
    solid,
)


def define_pass_value_solid(name, description=None):
    check.str_param(name, "name")
    check.opt_str_param(description, "description")

    @solid(
        name=name,
        description=description,
        input_defs=[],
        output_defs=[OutputDefinition(String)],
        config_schema={"value": Field(String)},
    )
    def pass_value_solid(context):
        yield Output(context.solid_config["value"])

    return pass_value_solid


def test_execute_solid_with_input_same_name():
    @solid(output_defs=[OutputDefinition()])
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
    @solid
    def solid_one(_, a_thing):
        return a_thing + a_thing

    @solid
    def solid_two(_, a_thing):
        return a_thing + a_thing

    @pipeline
    def pipe():
        solid_one(define_pass_value_solid("pass_to_one")())
        solid_two(define_pass_value_solid("pass_to_two")())

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
    assert result.result_for_solid("solid_one").output_value() == "foofoo"
    assert result.result_for_solid("solid_two").output_value() == "barbar"


def test_execute_dep_solid_different_input_name():
    pass_to_first = define_pass_value_solid("pass_to_first")

    @solid
    def first_solid(_, a_thing):
        return a_thing + a_thing

    @solid
    def second_solid(_, an_input):
        return an_input + an_input

    @pipeline
    def pipe():
        second_solid(first_solid(pass_to_first()))

    result = execute_pipeline(
        pipe, run_config={"solids": {"pass_to_first": {"config": {"value": "bar"}}}}
    )

    assert result.success
    assert len(result.solid_result_list) == 3
    assert result.result_for_solid("pass_to_first").output_value() == "bar"
    assert result.result_for_solid("first_solid").output_value() == "barbar"
    assert result.result_for_solid("second_solid").output_value() == "barbarbarbar"
