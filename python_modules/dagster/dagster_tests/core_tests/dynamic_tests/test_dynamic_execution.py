from dagster import (
    InputDefinition,
    OutputDefinition,
    composite_solid,
    execute_pipeline,
    pipeline,
    reconstructable,
    solid,
)
from dagster.core.test_utils import instance_for_test
from dagster.experimental import DynamicOutput, DynamicOutputDefinition


@solid
def multiply_by_two(context, y):
    context.log.info("multiply_by_two is returning " + str(y * 2))
    return y * 2


@solid
def multiply_inputs(context, y, ten):
    context.log.info("multiply_inputs is returning " + str(y * ten))
    return y * ten


@solid
def emit_ten(_):
    return 10


@solid
def echo(_, x: int) -> int:
    return x


@solid(output_defs=[DynamicOutputDefinition()])
def emit(_):
    for i in range(3):
        yield DynamicOutput(value=i, mapping_key=str(i))


@pipeline
def dynamic_pipeline():
    numbers = emit()
    numbers.map(lambda num: multiply_by_two(multiply_inputs(num, emit_ten())))


def test_map():
    result = execute_pipeline(dynamic_pipeline)
    assert result.success
    assert result.result_for_solid("multiply_inputs").output_value() == {"0": 0, "1": 10, "2": 20}
    assert result.result_for_solid("multiply_by_two").output_value() == {"0": 0, "1": 20, "2": 40}


def test_map_basic():
    with instance_for_test() as instance:
        result = execute_pipeline(reconstructable(dynamic_pipeline), instance=instance)
        assert result.success
        keys = result.events_by_step_key.keys()
        assert "multiply_inputs[0]" in keys
        assert "multiply_inputs[1]" in keys
        assert "multiply_inputs[2]" in keys
        assert result.result_for_solid("multiply_inputs").output_value() == {
            "0": 0,
            "1": 10,
            "2": 20,
        }
        assert result.result_for_solid("multiply_by_two").output_value() == {
            "0": 0,
            "1": 20,
            "2": 40,
        }


def test_map_multi():
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(dynamic_pipeline),
            run_config={
                "storage": {"filesystem": {}},
                "execution": {"multiprocess": {}},
            },
            instance=instance,
        )
        assert result.success
        keys = result.events_by_step_key.keys()
        assert "multiply_inputs[0]" in keys
        assert "multiply_inputs[1]" in keys
        assert "multiply_inputs[2]" in keys
        assert result.result_for_solid("multiply_inputs").output_value() == {
            "0": 0,
            "1": 10,
            "2": 20,
        }
        assert result.result_for_solid("multiply_by_two").output_value() == {
            "0": 0,
            "1": 20,
            "2": 40,
        }


def test_composite_wrapping():
    # regression test from user report

    @composite_solid(input_defs=[InputDefinition("z", int)], output_defs=[OutputDefinition(int)])
    def do_multiple_steps(z):
        output = echo(z)
        return echo(output)

    @pipeline
    def shallow():
        emit().map(do_multiple_steps)

    result = execute_pipeline(shallow)
    assert result.success
    assert result.result_for_solid("do_multiple_steps").output_value() == {"0": 0, "1": 1, "2": 2}

    @composite_solid(input_defs=[InputDefinition("x", int)], output_defs=[OutputDefinition(int)])
    def inner(x):
        return echo(x)

    @composite_solid(input_defs=[InputDefinition("y", int)], output_defs=[OutputDefinition(int)])
    def middle(y):
        return inner(y)

    @composite_solid(input_defs=[InputDefinition("z", int)], output_defs=[OutputDefinition(int)])
    def outer(z):
        return middle(z)

    @pipeline
    def deep():
        emit().map(outer)

    result = execute_pipeline(deep)
    assert result.success
    assert result.result_for_solid("outer").output_value() == {"0": 0, "1": 1, "2": 2}
