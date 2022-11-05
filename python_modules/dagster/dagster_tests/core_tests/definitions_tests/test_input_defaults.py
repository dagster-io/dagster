from typing import Optional

import pytest

from dagster import (
    DagsterEventType,
    DagsterInvalidDefinitionError,
    GraphIn,
    In,
    Nothing,
    graph,
    job,
    op,
)


def execute_in_graph(an_op, raise_on_error=True, run_config=None):
    @graph
    def my_graph():
        an_op()

    result = my_graph.execute_in_process(raise_on_error=raise_on_error, run_config=run_config)
    return result


def test_none():
    @op(ins={"x": In(Optional[int], default_value=None)})
    def none_x(x):
        return x

    result = execute_in_graph(none_x)
    assert result.output_for_node("none_x") is None


def test_none_infer():
    @op
    def none_x(x=None):
        return x

    result = execute_in_graph(none_x)
    assert result.output_for_node("none_x") is None


def test_int():
    @op(ins={"x": In(Optional[int], default_value=1337)})
    def int_x(x):
        return x

    result = execute_in_graph(int_x)
    assert result.output_for_node("int_x") == 1337


def test_int_infer():
    @op
    def int_x(x=1337):
        return x

    result = execute_in_graph(int_x)
    assert result.output_for_node("int_x") == 1337


def test_early_fail():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Type check failed for the default_value of InputDefinition x of type Int",
    ):

        @op(ins={"x": In(int, default_value="foo")})
        def _int_x(x):
            return x

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Type check failed for the default_value of InputDefinition x of type String",
    ):

        @op(ins={"x": In(str, default_value=1337)})
        def _int_x(x):
            return x


# we can't catch bad default_values except for scalars until runtime since the type_check function depends on
# a context that has access to resources etc.
@op(ins={"x": In(Optional[int], default_value="number")})  # type: ignore[arg-type]
def bad_default(x):
    return x


def test_mismatch():
    result = execute_in_graph(bad_default, raise_on_error=False)
    assert result.success == False
    input_event = result.filter_events(
        lambda event: event.event_type == DagsterEventType.STEP_INPUT
    )[0]
    assert input_event.step_input_data.type_check_data.success is False


def test_env_precedence():
    result = execute_in_graph(
        bad_default,
        run_config={"ops": {"bad_default": {"inputs": {"x": 1}}}},
        raise_on_error=False,
    )
    assert result.success == True
    assert result.output_for_node("bad_default") == 1


def test_input_precedence():
    @op
    def emit_one():
        return 1

    @job
    def the_job():
        bad_default(emit_one())

    result = the_job.execute_in_process()
    assert result.success
    assert result.output_for_node("bad_default") == 1


def test_nothing():
    with pytest.raises(DagsterInvalidDefinitionError):

        @op(ins={"x": In(Nothing, default_value=None)})
        def _nothing():
            pass


def test_composite_inner_default():
    @op(ins={"x": In(Optional[int], default_value=1337)})
    def int_x(x):
        return x

    @graph(ins={"y": GraphIn()})
    def wrap(y):
        return int_x(y)

    result = execute_in_graph(wrap)
    assert result.success
    assert result.output_for_node("wrap") == 1337


def test_custom_type_default():
    class CustomType:
        pass

    @op
    def test_op(_inp: Optional[CustomType] = None):
        return 1

    @job
    def test_job():
        test_op()

    result = test_job.execute_in_process()
    assert result.output_for_node("test_op") == 1
