import os

from dagster import (
    InputDefinition,
    List,
    ModeDefinition,
    Output,
    OutputDefinition,
    fs_io_manager,
    pipeline,
    solid,
)
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.execution.api import create_execution_plan, execute_run
from dagster.core.execution.plan.inputs import (
    FromConfig,
    FromDefaultValue,
    FromDynamicCollect,
    FromMultipleSources,
    FromPendingDynamicStepOutput,
    FromRootInputManager,
    FromStepOutput,
    FromUnresolvedStepOutput,
)
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.instance import DagsterInstance
from dagster.core.instance.ref import InstanceRef
from dagster.core.snap.execution_plan_snapshot import snapshot_from_execution_plan
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.root_input_manager import root_input_manager
from dagster.experimental import DynamicOutput, DynamicOutputDefinition
from dagster.utils import file_relative_path
from dagster.utils.test import copy_directory


@solid(output_defs=[OutputDefinition(int)])
def return_one(_):
    return 1


@solid(input_defs=[InputDefinition("nums", List[int])], output_defs=[OutputDefinition(int)])
def sum_fan_in(_, nums):
    return sum(nums)


@root_input_manager
def fake_root_input_manager(_context):
    return 678


@solid(input_defs=[InputDefinition("from_manager", root_manager_key="root_input_manager")])
def input_from_root_manager(_context, from_manager):
    return from_manager


@solid
def multiply_by_two(context, y):
    context.log.info("multiply_by_two is returning " + str(y * 2))
    return y * 2


@solid
def multiply_inputs(context, y, ten):
    context.log.info("multiply_inputs is returning " + str(y * ten))
    return y * ten


@solid(
    output_defs=[
        OutputDefinition(int, "optional_output", is_required=False),
        OutputDefinition(int, "required_output", is_required=True),
    ]
)
def optional_outputs(_):
    yield Output(1234, "required_output")


@solid
def emit_ten(_):
    return 10


@solid
def echo(_, x: int) -> int:
    return x


@solid(input_defs=[InputDefinition("y", int, default_value=7)])
def echo_default(_, y: int) -> int:
    return y


@solid(
    output_defs=[DynamicOutputDefinition()],
    input_defs=[InputDefinition("range_input", int, default_value=3)],
)
def emit(_context, range_input):
    for i in range(range_input):
        yield DynamicOutput(value=i, mapping_key=str(i))


@solid
def sum_numbers(_, nums):
    return sum(nums)


@solid(output_defs=[DynamicOutputDefinition()])
def dynamic_echo(_, nums):
    for x in nums:
        yield DynamicOutput(value=x, mapping_key=str(x))


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={
                "io_manager": fs_io_manager,
                "root_input_manager": fake_root_input_manager,
            }
        )
    ]
)
def dynamic_pipeline():
    input_from_root_manager()
    optional_outputs()
    numbers = emit()
    dynamic = numbers.map(lambda num: multiply_by_two(multiply_inputs(num, emit_ten())))
    n = multiply_by_two.alias("double_total")(sum_numbers(dynamic.collect()))
    echo(n)
    echo_default()
    fan_outs = []
    for i in range(0, 10):
        fan_outs.append(return_one.alias("return_one_{}".format(i))())
    sum_fan_in(fan_outs)


def _validate_execution_plan(plan):
    echo_step = plan.get_step_by_key("echo")
    assert echo_step

    echo_input_source = echo_step.step_input_named("x").source
    assert isinstance(echo_input_source, FromStepOutput)

    echo_default_step = plan.get_step_by_key("echo_default")
    assert echo_default_step

    echo_default_input_source = echo_default_step.step_input_named("y").source
    assert isinstance(echo_default_input_source, FromDefaultValue)

    sum_numbers_input_source = plan.get_step_by_key("sum_numbers").step_input_named("nums").source
    assert isinstance(sum_numbers_input_source, FromDynamicCollect)

    emit_input_source = plan.get_step_by_key("emit").step_input_named("range_input").source
    assert isinstance(emit_input_source, FromConfig)

    input_from_root_manager_source = (
        plan.get_step_by_key("input_from_root_manager").step_input_named("from_manager").source
    )
    assert isinstance(input_from_root_manager_source, FromRootInputManager)

    fan_in_source = plan.get_step_by_key("sum_fan_in").step_input_named("nums").source
    assert isinstance(fan_in_source, FromMultipleSources)

    dynamic_source = plan.get_step_by_key("multiply_inputs[?]").step_input_named("y").source
    assert isinstance(dynamic_source, FromPendingDynamicStepOutput)

    unresolved_source = plan.get_step_by_key("multiply_by_two[?]").step_input_named("y").source
    assert isinstance(unresolved_source, FromUnresolvedStepOutput)

    dynamic_output = plan.get_step_by_key("emit").step_outputs[0]
    assert dynamic_output.is_dynamic
    assert dynamic_output.is_required

    static_output = plan.get_step_by_key("echo").step_outputs[0]
    assert not static_output.is_dynamic
    assert static_output.is_required

    optional_output = plan.get_step_by_key("optional_outputs").step_outputs[0]
    assert not optional_output.is_dynamic
    assert not optional_output.is_required


# Verify that an previously generated execution plan snapshot can still execute a
# pipeline successfully
def test_execution_plan_snapshot_backcompat():

    src_dir = file_relative_path(__file__, "test_execution_plan_snapshots/")
    snapshot_dirs = [f for f in os.listdir(src_dir) if not os.path.isfile(os.path.join(src_dir, f))]
    for snapshot_dir_path in snapshot_dirs:
        print(f"Executing a saved run from {snapshot_dir_path}")  # pylint: disable=print-call

        with copy_directory(os.path.join(src_dir, snapshot_dir_path)) as test_dir:
            with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
                runs = instance.get_runs()
                assert len(runs) == 1

                run = runs[0]
                assert run.status == PipelineRunStatus.NOT_STARTED

                the_pipeline = InMemoryPipeline(dynamic_pipeline)

                # First create a brand new plan from the pipeline and validate it
                new_plan = create_execution_plan(the_pipeline, run_config=run.run_config)
                _validate_execution_plan(new_plan)

                # Create a snapshot and rebuild it, validate the rebuilt plan
                new_plan_snapshot = snapshot_from_execution_plan(new_plan, run.pipeline_snapshot_id)
                rebuilt_plan = ExecutionPlan.rebuild_from_snapshot(
                    "dynamic_pipeline", new_plan_snapshot
                )
                _validate_execution_plan(rebuilt_plan)

                # Then validate the plan built from the historical snapshot on the run
                stored_snapshot = instance.get_execution_plan_snapshot(
                    run.execution_plan_snapshot_id
                )

                rebuilt_plan = ExecutionPlan.rebuild_from_snapshot(
                    "dynamic_pipeline", stored_snapshot
                )
                _validate_execution_plan(rebuilt_plan)

                # Finally, execute the run (using the historical execution plan snapshot)
                result = execute_run(the_pipeline, run, instance, raise_on_error=True)
                assert result.success


# To generate a new snapshot against your local DagsterInstance (run this script in python
# after wiping your sqlite instance, then copy the 'history' directory into a new subfolder
# in the test_execution_plan_snapshots folder)
#
# dagster run wipe
# python python_modules/dagster/dagster_tests/general_tests/compat_tests/test_execution_plan_snapshot.py
#
# cp -r ~/dagster-home/history python_modules/dagster/dagster_tests/general_tests/compat_tests/test_execution_plan_snapshots/<test_name>
if __name__ == "__main__":
    with DagsterInstance.get() as gen_instance:
        empty_runs = gen_instance.get_runs()
        assert len(empty_runs) == 0
        gen_instance.create_run_for_pipeline(
            pipeline_def=dynamic_pipeline,
            run_config={"solids": {"emit": {"inputs": {"range_input": 5}}}},
        )

        print("Created run for test")  # pylint: disable=print-call
