import os

from dagster import DynamicOut, DynamicOutput, In, List, Out, Output, fs_io_manager, job, op
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.reconstruct import reconstructable
from dagster._core.execution.api import create_execution_plan, execute_run
from dagster._core.execution.plan.inputs import (
    FromConfig,
    FromDefaultValue,
    FromDynamicCollect,
    FromInputManager,
    FromMultipleSources,
    FromPendingDynamicStepOutput,
    FromStepOutput,
    FromUnresolvedStepOutput,
)
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._core.snap.execution_plan_snapshot import snapshot_from_execution_plan
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.input_manager import input_manager
from dagster._utils import file_relative_path
from dagster._utils.test import copy_directory


@op(out=Out(int))
def return_one(_):
    return 1


@op(ins={"nums": In(List[int])}, out=Out(int))
def sum_fan_in(_, nums):
    return sum(nums)


@input_manager
def fake_input_manager(_context):
    return 678


@op(ins={"from_manager": In(input_manager_key="input_manager")})
def input_from_input_manager(_context, from_manager):
    return from_manager


@op
def multiply_by_two(context, y):
    context.log.info("multiply_by_two is returning " + str(y * 2))
    return y * 2


@op
def multiply_inputs(context, y, ten):
    context.log.info("multiply_inputs is returning " + str(y * ten))
    return y * ten


@op(
    out={
        "optional_output": Out(int, is_required=False),
        "required_output": Out(int, is_required=True),
    }
)
def optional_outputs(_):
    yield Output(1234, "required_output")


@op
def emit_ten(_):
    return 10


@op
def echo(_, x: int) -> int:
    return x


@op(ins={"y": In(int, default_value=7)})
def echo_default(_, y: int) -> int:
    return y


@op(
    out=DynamicOut(),
    ins={"range_input": In(int, default_value=3)},
)
def emit(_context, range_input):
    for i in range(range_input):
        yield DynamicOutput(value=i, mapping_key=str(i))


@op
def sum_numbers(_, nums):
    return sum(nums)


@op(out=DynamicOut())
def dynamic_echo(_, nums):
    for x in nums:
        yield DynamicOutput(value=x, mapping_key=str(x))


def get_dynamic_job() -> JobDefinition:
    @job(
        resource_defs={
            "io_manager": fs_io_manager,
            "input_manager": fake_input_manager,
        }
    )
    def dynamic_job():
        input_from_input_manager()
        optional_outputs()
        numbers = emit()
        dynamic = numbers.map(lambda num: multiply_by_two(multiply_inputs(num, emit_ten())))
        n = multiply_by_two.alias("double_total")(sum_numbers(dynamic.collect()))
        echo(n)
        echo_default()
        fan_outs = []
        for i in range(0, 10):
            fan_outs.append(return_one.alias(f"return_one_{i}")())
        sum_fan_in(fan_outs)

    return dynamic_job


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

    input_from_input_manager_source = (
        plan.get_step_by_key("input_from_input_manager").step_input_named("from_manager").source
    )
    assert isinstance(input_from_input_manager_source, FromInputManager)

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
        print(f"Executing a saved run from {snapshot_dir_path}")  # noqa: T201

        with copy_directory(os.path.join(src_dir, snapshot_dir_path)) as test_dir:
            with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
                runs = instance.get_runs()
                assert len(runs) == 1

                run = runs[0]
                assert run.status == DagsterRunStatus.NOT_STARTED

                the_job = reconstructable(get_dynamic_job)

                # First create a brand new plan from the pipeline and validate it
                new_plan = create_execution_plan(the_job, run_config=run.run_config)
                _validate_execution_plan(new_plan)

                # Create a snapshot and rebuild it, validate the rebuilt plan
                new_plan_snapshot = snapshot_from_execution_plan(new_plan, run.job_snapshot_id)  # pyright: ignore[reportArgumentType]
                rebuilt_plan = ExecutionPlan.rebuild_from_snapshot("dynamic_job", new_plan_snapshot)
                _validate_execution_plan(rebuilt_plan)

                # Then validate the plan built from the historical snapshot on the run
                stored_snapshot = instance.get_execution_plan_snapshot(
                    run.execution_plan_snapshot_id  # pyright: ignore[reportArgumentType]
                )

                rebuilt_plan = ExecutionPlan.rebuild_from_snapshot("dynamic_job", stored_snapshot)
                _validate_execution_plan(rebuilt_plan)

                # Finally, execute the run (using the historical execution plan snapshot)
                result = execute_run(the_job, run, instance, raise_on_error=True)
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
        gen_instance.create_run_for_job(
            job_def=get_dynamic_job(),
            run_config={"ops": {"emit": {"inputs": {"range_input": 5}}}},
        )

        print("Created run for test")  # noqa: T201
