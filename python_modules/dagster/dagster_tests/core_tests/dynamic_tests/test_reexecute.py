import pytest
from dagster import execute_pipeline, pipeline, reexecute_pipeline, solid
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.test_utils import instance_for_test
from dagster.experimental import DynamicOutput, DynamicOutputDefinition


@solid
def multiply_by_two(context, y):
    context.log.info("multiply_by_two is returning " + str(y * 2))
    return y * 2


@solid
def multiply_inputs(context, y, ten):
    # current_run = context.instance.get_run_by_id(context.run_id)
    # if y == 2 and current_run.parent_run_id is None:
    #     raise Exception()
    context.log.info("multiply_inputs is returning " + str(y * ten))
    return y * ten


@solid
def emit_ten(_):
    return 10


@solid(output_defs=[DynamicOutputDefinition()])
def emit(_):
    for i in range(3):
        yield DynamicOutput(value=i, mapping_key=str(i))


@pipeline
def dynamic_pipeline():
    # pylint: disable=no-member
    emit().map(lambda n: multiply_by_two(multiply_inputs(n, emit_ten())))


def test_map():
    result = execute_pipeline(
        dynamic_pipeline,
    )
    assert result.success


def test_reexec_from_parent_basic():
    with instance_for_test() as instance:
        parent_result = execute_pipeline(
            dynamic_pipeline, run_config={"storage": {"filesystem": {}}}, instance=instance
        )
        parent_run_id = parent_result.run_id

        reexec_result = reexecute_pipeline(
            pipeline=dynamic_pipeline,
            parent_run_id=parent_run_id,
            run_config={
                "storage": {"filesystem": {}},
            },
            step_selection=["emit"],
            instance=instance,
        )
        assert reexec_result.success
        assert reexec_result.result_for_solid("emit").output_value() == {
            "0": 0,
            "1": 1,
            "2": 2,
        }


def test_reexec_from_parent_1():
    with instance_for_test() as instance:
        parent_result = execute_pipeline(
            dynamic_pipeline, run_config={"storage": {"filesystem": {}}}, instance=instance
        )
        parent_run_id = parent_result.run_id

        reexec_result = reexecute_pipeline(
            pipeline=dynamic_pipeline,
            parent_run_id=parent_run_id,
            run_config={
                "storage": {"filesystem": {}},
            },
            step_selection=["multiply_inputs[0]"],
            instance=instance,
        )
        assert reexec_result.success
        assert reexec_result.result_for_solid("multiply_inputs").output_value() == {
            "0": 0,
        }


def test_reexec_from_parent_dynamic_fails():
    with instance_for_test() as instance:
        parent_result = execute_pipeline(
            dynamic_pipeline, run_config={"storage": {"filesystem": {}}}, instance=instance
        )
        parent_run_id = parent_result.run_id

        # not currently supported, this needs to know all fan outs of previous step, should just run previous step
        with pytest.raises(
            DagsterInvariantViolationError,
            match=r'UnresolvedExecutionStep "multiply_inputs\[\?\]" is resolved by "emit" which is not part of the current step selection',
        ):
            reexecute_pipeline(
                pipeline=dynamic_pipeline,
                parent_run_id=parent_run_id,
                run_config={
                    "storage": {"filesystem": {}},
                },
                step_selection=["multiply_inputs[?]"],
                instance=instance,
            )


def test_reexec_from_parent_2():
    with instance_for_test() as instance:
        parent_result = execute_pipeline(
            dynamic_pipeline, run_config={"storage": {"filesystem": {}}}, instance=instance
        )
        parent_run_id = parent_result.run_id

        reexec_result = reexecute_pipeline(
            pipeline=dynamic_pipeline,
            parent_run_id=parent_run_id,
            run_config={
                "storage": {"filesystem": {}},
            },
            step_selection=["multiply_by_two[1]"],
            instance=instance,
        )
        assert reexec_result.success
        assert reexec_result.result_for_solid("multiply_by_two").output_value() == {
            "1": 20,
        }


def test_reexec_from_parent_3():
    with instance_for_test() as instance:
        parent_result = execute_pipeline(
            dynamic_pipeline, run_config={"storage": {"filesystem": {}}}, instance=instance
        )
        parent_run_id = parent_result.run_id

        reexec_result = reexecute_pipeline(
            pipeline=dynamic_pipeline,
            parent_run_id=parent_run_id,
            run_config={
                "storage": {"filesystem": {}},
            },
            step_selection=["multiply_inputs[1]", "multiply_by_two[2]"],
            instance=instance,
        )
        assert reexec_result.success
        assert reexec_result.result_for_solid("multiply_inputs").output_value() == {
            "1": 10,
        }
        assert reexec_result.result_for_solid("multiply_by_two").output_value() == {
            "2": 40,
        }
