import dagster as dg
from dagster import _check as check


def define_pass_value_op(name, description=None):
    check.str_param(name, "name")
    check.opt_str_param(description, "description")

    @dg.op(
        name=name,
        description=description,
        out=dg.Out(dg.String),
        config_schema={"value": dg.Field(dg.String)},
    )
    def pass_value_op(context):
        yield dg.Output(context.op_config["value"])

    return pass_value_op


def test_execute_op_with_input_same_name():
    @dg.op
    def a_thing(_, a_thing):
        return a_thing + a_thing

    @dg.job
    def pipe():
        pass_value = define_pass_value_op("pass_value")
        a_thing(pass_value())

    result = pipe.execute_in_process(
        run_config={"ops": {"pass_value": {"config": {"value": "foo"}}}}
    )

    assert result.output_for_node("a_thing") == "foofoo"


def test_execute_two_ops_with_same_input_name():
    @dg.op
    def op_one(_, a_thing):
        return a_thing + a_thing

    @dg.op
    def op_two(_, a_thing):
        return a_thing + a_thing

    @dg.job
    def pipe():
        op_one(define_pass_value_op("pass_to_one")())
        op_two(define_pass_value_op("pass_to_two")())

    result = pipe.execute_in_process(
        run_config={
            "ops": {
                "pass_to_one": {"config": {"value": "foo"}},
                "pass_to_two": {"config": {"value": "bar"}},
            }
        },
    )

    assert result.success
    assert result.output_for_node("op_one") == "foofoo"
    assert result.output_for_node("op_two") == "barbar"


def test_execute_dep_op_different_input_name():
    pass_to_first = define_pass_value_op("pass_to_first")

    @dg.op
    def first_op(_, a_thing):
        return a_thing + a_thing

    @dg.op
    def second_op(_, an_input):
        return an_input + an_input

    @dg.job
    def foo_job():
        second_op(first_op(pass_to_first()))

    result = foo_job.execute_in_process(
        run_config={"ops": {"pass_to_first": {"config": {"value": "bar"}}}}
    )

    assert result.success
    assert len(result.filter_events(lambda evt: evt.is_step_success)) == 3
    assert result.output_for_node("pass_to_first") == "bar"
    assert result.output_for_node("first_op") == "barbar"
    assert result.output_for_node("second_op") == "barbarbarbar"
