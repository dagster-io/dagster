import pytest
from dagster import (
    DagsterInvalidDefinitionError,
    InputDefinition,
    Nothing,
    Optional,
    composite_solid,
    execute_pipeline,
    execute_solid,
    lambda_solid,
    pipeline,
)


def test_none():
    @lambda_solid(input_defs=[InputDefinition("x", Optional[int], default_value=None)])
    def none_x(x):
        return x

    result = execute_solid(none_x)
    assert result.output_value() == None


def test_none_infer():
    @lambda_solid
    def none_x(x=None):
        return x

    result = execute_solid(none_x)
    assert result.output_value() == None


def test_int():
    @lambda_solid(input_defs=[InputDefinition("x", Optional[int], default_value=1337)])
    def int_x(x):
        return x

    result = execute_solid(int_x)
    assert result.output_value() == 1337


def test_int_infer():
    @lambda_solid
    def int_x(x=1337):
        return x

    result = execute_solid(int_x)
    assert result.output_value() == 1337


def test_early_fail():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Type check failed for the default_value of InputDefinition x of type Int",
    ):

        @lambda_solid(input_defs=[InputDefinition("x", int, default_value="foo")])
        def _int_x(x):
            return x

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Type check failed for the default_value of InputDefinition x of type String",
    ):

        @lambda_solid(input_defs=[InputDefinition("x", str, default_value=1337)])
        def _int_x(x):
            return x


# we can't catch bad default_values except for scalars until runtime since the type_check function depends on
# a context that has access to resources etc.
@lambda_solid(input_defs=[InputDefinition("x", Optional[int], default_value="number")])
def bad_default(x):
    return x


def test_mismatch():
    result = execute_solid(bad_default, raise_on_error=False)
    assert result.success == False
    assert result.input_events_during_compute[0].step_input_data.type_check_data.success == False


def test_env_precedence():
    result = execute_solid(
        bad_default,
        run_config={"solids": {"bad_default": {"inputs": {"x": 1}}}},
        raise_on_error=False,
    )
    assert result.success == True
    assert result.output_value() == 1


def test_input_precedence():
    @lambda_solid
    def emit_one():
        return 1

    @pipeline
    def pipe():
        bad_default(emit_one())

    result = execute_pipeline(pipe)
    assert result.success
    assert result.output_for_solid("bad_default") == 1


def test_nothing():
    with pytest.raises(DagsterInvalidDefinitionError):

        @lambda_solid(input_defs=[InputDefinition("x", Nothing, default_value=None)])
        def _nothing():
            pass


def test_composite_outer_default():
    @lambda_solid(input_defs=[InputDefinition("x", Optional[int])])
    def int_x(x):
        return x

    @composite_solid(input_defs=[InputDefinition("y", Optional[int], default_value=42)])
    def wrap(y):
        return int_x(y)

    result = execute_solid(wrap)
    assert result.success
    assert result.output_value() == 42


def test_composite_inner_default():
    @lambda_solid(input_defs=[InputDefinition("x", Optional[int], default_value=1337)])
    def int_x(x):
        return x

    @composite_solid(input_defs=[InputDefinition("y", Optional[int])])
    def wrap(y):
        return int_x(y)

    result = execute_solid(wrap)
    assert result.success
    assert result.output_value() == 1337


def test_composite_precedence_default():
    @lambda_solid(input_defs=[InputDefinition("x", Optional[int], default_value=1337)])
    def int_x(x):
        return x

    @composite_solid(input_defs=[InputDefinition("y", Optional[int], default_value=42)])
    def wrap(y):
        return int_x(y)

    result = execute_solid(wrap)
    assert result.success
    assert result.output_value() == 42


def test_composite_mid_default():
    @lambda_solid(input_defs=[InputDefinition("x", Optional[int])])
    def int_x(x):
        return x

    @composite_solid(input_defs=[InputDefinition("y", Optional[int], default_value=42)])
    def wrap(y):
        return int_x(y)

    @composite_solid(input_defs=[InputDefinition("z", Optional[int])])
    def outter_wrap(z):
        return wrap(z)

    result = execute_solid(outter_wrap)
    assert result.success
    assert result.output_value() == 42
