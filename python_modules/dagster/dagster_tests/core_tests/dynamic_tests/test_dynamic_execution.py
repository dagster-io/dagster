import pytest
from dagster import (
    Field,
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    composite_solid,
    execute_pipeline,
    fs_io_manager,
    pipeline,
    reconstructable,
    solid,
)
from dagster.core.errors import DagsterExecutionStepNotFoundError
from dagster.core.execution.api import reexecute_pipeline
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


@solid(
    output_defs=[DynamicOutputDefinition()],
    config_schema={
        "range": Field(int, is_required=False, default_value=3),
        "fail": Field(bool, is_required=False, default_value=False),
    },
)
def emit(context):
    if context.solid_config["fail"]:
        raise Exception("FAILURE")

    for i in range(context.solid_config["range"]):
        yield DynamicOutput(value=i, mapping_key=str(i))


@solid
def sum_numbers(_, nums):
    return sum(nums)


@solid(output_defs=[DynamicOutputDefinition()])
def dynamic_echo(_, nums):
    for x in nums:
        yield DynamicOutput(value=x, mapping_key=str(x))


@pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": fs_io_manager})])
def dynamic_pipeline():
    numbers = emit()
    dynamic = numbers.map(lambda num: multiply_by_two(multiply_inputs(num, emit_ten())))
    n = multiply_by_two.alias("double_total")(sum_numbers(dynamic.collect()))
    echo(n)  # test transitive downstream of collect


@pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": fs_io_manager})])
def fan_repeat():
    one = emit().map(multiply_by_two)
    two = dynamic_echo(one.collect()).map(multiply_by_two)
    three = dynamic_echo(two.collect()).map(multiply_by_two)
    sum_numbers(three.collect())


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
        assert result.result_for_solid("sum_numbers").output_value() == 60
        assert result.result_for_solid("double_total").output_value() == 120
        assert result.result_for_solid("echo").output_value() == 120


def test_map_empty():
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config={"solids": {"emit": {"config": {"range": 0}}}},
        )
        assert result.success
        assert result.result_for_solid("double_total").output_value() == 0


def test_map_multi():
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(dynamic_pipeline),
            run_config={
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
        assert result.result_for_solid("sum_numbers").output_value() == 60
        assert result.result_for_solid("double_total").output_value() == 120
        assert result.result_for_solid("echo").output_value() == 120


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


def test_full_reexecute():
    with instance_for_test() as instance:
        result_1 = execute_pipeline(dynamic_pipeline, instance=instance)
        assert result_1.success

        result_2 = reexecute_pipeline(
            dynamic_pipeline, parent_run_id=result_1.run_id, instance=instance
        )
        assert result_2.success


def test_partial_reexecute():
    with instance_for_test() as instance:
        result_1 = execute_pipeline(dynamic_pipeline, instance=instance)
        assert result_1.success

        result_2 = reexecute_pipeline(
            dynamic_pipeline,
            parent_run_id=result_1.run_id,
            instance=instance,
            step_selection=["sum_numbers*"],
        )
        assert result_2.success

        result_3 = reexecute_pipeline(
            dynamic_pipeline,
            parent_run_id=result_1.run_id,
            instance=instance,
            step_selection=["multiply_by_two[1]*"],
        )
        assert result_3.success


def test_partial_reexecute_multiproc():
    with instance_for_test() as instance:
        result_1 = execute_pipeline(
            reconstructable(dynamic_pipeline),
            run_config={"execution": {"multiprocess": {}}},
            instance=instance,
        )
        assert result_1.success

        result_2 = reexecute_pipeline(
            reconstructable(dynamic_pipeline),
            parent_run_id=result_1.run_id,
            instance=instance,
            step_selection=["sum_numbers*"],
        )
        assert result_2.success

        result_3 = reexecute_pipeline(
            reconstructable(dynamic_pipeline),
            parent_run_id=result_1.run_id,
            instance=instance,
            step_selection=["multiply_by_two[1]*"],
        )
        assert result_3.success


def test_fan_out_in_out_in():
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(fan_repeat),
            instance=instance,
        )
        assert result.success
        assert (
            result.result_for_solid("sum_numbers").output_value() == 24
        )  # (0, 1, 2) x 2 x 2 x 2 = (0, 8, 16)

        empty_result = execute_pipeline(
            reconstructable(fan_repeat),
            instance=instance,
            run_config={"solids": {"emit": {"config": {"range": 0}}}},
        )
        assert empty_result.success
        assert empty_result.result_for_solid("sum_numbers").output_value() == 0


def test_bad_step_selection():
    with instance_for_test() as instance:
        result_1 = execute_pipeline(dynamic_pipeline, instance=instance)
        assert result_1.success

        # this exact error could be improved, but it should fail if you try to select
        # both the dynamic outputting step key and something resolved by it in the previous run
        with pytest.raises(DagsterExecutionStepNotFoundError):
            reexecute_pipeline(
                dynamic_pipeline,
                parent_run_id=result_1.run_id,
                instance=instance,
                step_selection=["emit", "multiply_by_two[1]"],
            )


def test_map_basic_fail():
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config={"solids": {"emit": {"config": {"fail": True}}}},
            raise_on_error=False,
        )
        assert not result.success


def test_map_multi_fail():
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config={
                "execution": {"multiprocess": {}},
                "solids": {"emit": {"config": {"fail": True}}},
            },
            raise_on_error=False,
        )
        assert not result.success


def test_map_multi_reexecute_after_fail():
    with instance_for_test() as instance:
        result_1 = execute_pipeline(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config={
                "execution": {"multiprocess": {}},
                "solids": {"emit": {"config": {"fail": True}}},
            },
            raise_on_error=False,
        )
        assert not result_1.success

        result_2 = reexecute_pipeline(
            reconstructable(dynamic_pipeline),
            parent_run_id=result_1.run_id,
            run_config={
                "execution": {"multiprocess": {}},
            },
            instance=instance,
        )
        assert result_2.success


def test_multi_collect():
    @solid
    def fan_in(_, x, y):
        return x + y

    @pipeline
    def double():
        nums_1 = emit()
        nums_2 = emit()
        fan_in(nums_1.collect(), nums_2.collect())

    result = execute_pipeline(double)
    assert result.success
    assert result.result_for_solid("fan_in").output_value() == [0, 1, 2, 0, 1, 2]
