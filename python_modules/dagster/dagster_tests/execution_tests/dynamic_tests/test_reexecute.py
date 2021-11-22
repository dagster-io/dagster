from typing import List

import pytest
from dagster import (
    DynamicOutput,
    DynamicOutputDefinition,
    execute_pipeline,
    fs_io_manager,
    job,
    op,
    pipeline,
    reconstructable,
    reexecute_pipeline,
    solid,
)
from dagster.core.definitions.events import Output
from dagster.core.definitions.output import DynamicOut, Out
from dagster.core.errors import DagsterExecutionStepNotFoundError, DagsterInvariantViolationError
from dagster.core.test_utils import default_mode_def_for_test, instance_for_test


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


@pipeline(mode_defs=[default_mode_def_for_test])
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
        parent_result = execute_pipeline(dynamic_pipeline, instance=instance)
        parent_run_id = parent_result.run_id

        reexec_result = reexecute_pipeline(
            pipeline=dynamic_pipeline,
            parent_run_id=parent_run_id,
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
        parent_result = execute_pipeline(dynamic_pipeline, instance=instance)
        parent_run_id = parent_result.run_id

        reexec_result = reexecute_pipeline(
            pipeline=dynamic_pipeline,
            parent_run_id=parent_run_id,
            step_selection=["multiply_inputs[0]"],
            instance=instance,
        )
        assert reexec_result.success
        assert reexec_result.result_for_solid("multiply_inputs").output_value() == {
            "0": 0,
        }


def test_reexec_from_parent_dynamic_fails():
    with instance_for_test() as instance:
        parent_result = execute_pipeline(dynamic_pipeline, instance=instance)
        parent_run_id = parent_result.run_id

        # not currently supported, this needs to know all fan outs of previous step, should just run previous step
        with pytest.raises(
            DagsterInvariantViolationError,
            match=r'Unresolved ExecutionStep "multiply_inputs\[\?\]" is resolved by "emit" which is not part of the current step selection',
        ):
            reexecute_pipeline(
                pipeline=dynamic_pipeline,
                parent_run_id=parent_run_id,
                step_selection=["multiply_inputs[?]"],
                instance=instance,
            )


def test_reexec_from_parent_2():
    with instance_for_test() as instance:
        parent_result = execute_pipeline(dynamic_pipeline, instance=instance)
        parent_run_id = parent_result.run_id

        reexec_result = reexecute_pipeline(
            pipeline=dynamic_pipeline,
            parent_run_id=parent_run_id,
            step_selection=["multiply_by_two[1]"],
            instance=instance,
        )
        assert reexec_result.success
        assert reexec_result.result_for_solid("multiply_by_two").output_value() == {
            "1": 20,
        }


def test_reexec_from_parent_3():
    with instance_for_test() as instance:
        parent_result = execute_pipeline(dynamic_pipeline, instance=instance)
        parent_run_id = parent_result.run_id

        reexec_result = reexecute_pipeline(
            pipeline=dynamic_pipeline,
            parent_run_id=parent_run_id,
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


@op
def echo(x):
    return x


@op
def adder(ls: List[int]) -> int:
    return sum(ls)


@op(out=DynamicOut())
def dynamic_op():
    for i in range(10):
        yield DynamicOutput(value=i, mapping_key=str(i))


def dynamic_with_optional_output_job():
    @op(out=DynamicOut(is_required=False))
    def dynamic_optional_output_op(context):
        for i in range(10):
            if (
                context.pipeline_run.parent_run_id
                and i % 2 == 0  # re-execution run skipped odd numbers
                or not context.pipeline_run.parent_run_id
                and i % 2 == 1  # root run skipped even numbers
            ):
                yield DynamicOutput(value=i, mapping_key=str(i))

    @job(resource_defs={"io_manager": fs_io_manager})
    def _dynamic_with_optional_output_job():
        dynamic_results = dynamic_optional_output_op().map(echo)
        adder(dynamic_results.collect())

    return _dynamic_with_optional_output_job


def test_reexec_dynamic_with_optional_output_job_1():
    with instance_for_test() as instance:
        result = dynamic_with_optional_output_job().execute_in_process(instance=instance)

        # re-execute all
        re_result = reexecute_pipeline(
            reconstructable(dynamic_with_optional_output_job),
            parent_run_id=result.run_id,
            instance=instance,
        )
        assert re_result.success
        assert re_result.output_for_solid("adder") == sum([i for i in range(10) if i % 2 == 0])


def test_reexec_dynamic_with_optional_output_job_2():
    with instance_for_test() as instance:
        result = dynamic_with_optional_output_job().execute_in_process(instance=instance)

        # re-execute the step where the source yielded an output
        re_result = reexecute_pipeline(
            reconstructable(dynamic_with_optional_output_job),
            parent_run_id=result.run_id,
            instance=instance,
            step_selection=["echo[1]"],
        )
        assert re_result.success
        assert re_result.result_for_solid("echo").output_value() == {
            "1": 1,
        }


def test_reexec_dynamic_with_optional_output_job_3():
    with instance_for_test() as instance:
        result = dynamic_with_optional_output_job().execute_in_process(instance=instance)

        # re-execute the step where the source did not yield
        # -> error because the dynamic step wont exist in execution plan
        with pytest.raises(
            DagsterExecutionStepNotFoundError,
            match=r"Step selection refers to unknown step: echo\[0\]",
        ):
            reexecute_pipeline(
                reconstructable(dynamic_with_optional_output_job),
                parent_run_id=result.run_id,
                instance=instance,
                step_selection=["echo[0]"],
            )


def dynamic_with_transitive_optional_output_job():
    @op(out=Out(is_required=False))
    def add_one_with_optional_output(context, i: int):
        if (
            context.pipeline_run.parent_run_id
            and i % 2 == 0  # re-execution run skipped odd numbers
            or not context.pipeline_run.parent_run_id
            and i % 2 == 1  # root run skipped even numbers
        ):
            yield Output(i + 1)

    @job(resource_defs={"io_manager": fs_io_manager})
    def _dynamic_with_transitive_optional_output_job():
        dynamic_results = dynamic_op().map(lambda n: echo(add_one_with_optional_output(n)))
        adder(dynamic_results.collect())

    return _dynamic_with_transitive_optional_output_job


def test_reexec_dynamic_with_transitive_optional_output_job_1():
    with instance_for_test() as instance:
        result = dynamic_with_transitive_optional_output_job().execute_in_process(instance=instance)
        assert result.success
        assert result.output_for_node("adder") == sum([i + 1 for i in range(10) if i % 2 == 1])

        # re-execute all
        re_result = reexecute_pipeline(
            reconstructable(dynamic_with_transitive_optional_output_job),
            parent_run_id=result.run_id,
            instance=instance,
        )
        assert re_result.success
        assert re_result.output_for_solid("adder") == sum([i + 1 for i in range(10) if i % 2 == 0])


def test_reexec_dynamic_with_transitive_optional_output_job_2():
    with instance_for_test() as instance:
        result = dynamic_with_transitive_optional_output_job().execute_in_process(instance=instance)

        # re-execute the step where the source yielded an output
        re_result = reexecute_pipeline(
            reconstructable(dynamic_with_transitive_optional_output_job),
            parent_run_id=result.run_id,
            instance=instance,
            step_selection=["echo[1]"],
        )
        assert re_result.success
        assert re_result.result_for_solid("echo").output_value() == {"1": 2}


def test_reexec_dynamic_with_transitive_optional_output_job_3():
    with instance_for_test() as instance:
        result = dynamic_with_transitive_optional_output_job().execute_in_process(instance=instance)

        # re-execute the step where the source did not yield
        re_result = reexecute_pipeline(
            reconstructable(dynamic_with_transitive_optional_output_job),
            parent_run_id=result.run_id,
            instance=instance,
            step_selection=["echo[0]"],
            raise_on_error=False,
        )
        # when all the previous runs have skipped yielding the source,
        # run would fail because of run_id returns None
        # FIXME: https://github.com/dagster-io/dagster/issues/3511
        # ideally it should skip the step because all its previous runs have skipped and finish the run successfully
        assert not re_result.success
