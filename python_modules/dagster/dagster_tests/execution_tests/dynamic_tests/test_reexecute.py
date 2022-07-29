from typing import List

import pytest

from dagster import (
    DynamicOutput,
    ReexecutionOptions,
    execute_job,
    fs_io_manager,
    in_process_executor,
    job,
    op,
    reconstructable,
)
from dagster._core.definitions.events import Output
from dagster._core.definitions.output import DynamicOut, Out
from dagster._core.errors import DagsterExecutionStepNotFoundError, DagsterInvariantViolationError
from dagster._core.test_utils import instance_for_test


@op
def multiply_by_two(context, y):
    context.log.info("multiply_by_two is returning " + str(y * 2))
    return y * 2


@op
def multiply_inputs(context, y, ten):
    # current_run = context.instance.get_run_by_id(context.run_id)
    # if y == 2 and current_run.parent_run_id is None:
    #     raise Exception()
    context.log.info("multiply_inputs is returning " + str(y * ten))
    return y * ten


@op
def emit_ten(_):
    return 10


@op(out=DynamicOut())
def emit(_):
    for i in range(3):
        yield DynamicOutput(value=i, mapping_key=str(i))


@job(executor_def=in_process_executor)
def dynamic_pipeline():
    # pylint: disable=no-member
    emit().map(lambda n: multiply_by_two(multiply_inputs(n, emit_ten())))


def test_map():
    result = dynamic_pipeline.execute_in_process()
    assert result.success


def test_reexec_from_parent_basic():
    with instance_for_test() as instance:
        parent_result = execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
        )
        parent_run_id = parent_result.run_id

        with execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=parent_run_id,
                step_selection=["emit"],
            ),
        ) as reexec_result:
            assert reexec_result.success
            assert reexec_result.output_for_node("emit") == {
                "0": 0,
                "1": 1,
                "2": 2,
            }


def test_reexec_from_parent_1():
    with instance_for_test() as instance:
        parent_result = execute_job(reconstructable(dynamic_pipeline), instance=instance)
        parent_run_id = parent_result.run_id

        with execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=parent_run_id,
                step_selection=["multiply_inputs[0]"],
            ),
        ) as reexec_result:
            assert reexec_result.success
            assert reexec_result.output_for_node("multiply_inputs") == {
                "0": 0,
            }


def test_reexec_from_parent_dynamic_fails():
    with instance_for_test() as instance:
        parent_result = execute_job(reconstructable(dynamic_pipeline), instance=instance)
        parent_run_id = parent_result.run_id

        # not currently supported, this needs to know all fan outs of previous step, should just run previous step
        with pytest.raises(
            DagsterInvariantViolationError,
            match=r'Unresolved ExecutionStep "multiply_inputs\[\?\]" is resolved by "emit" which is not part of the current step selection',
        ):
            execute_job(
                reconstructable(dynamic_pipeline),
                instance=instance,
                reexecution_options=ReexecutionOptions(
                    parent_run_id=parent_run_id,
                    step_selection=["multiply_inputs[?]"],
                ),
            )


def test_reexec_from_parent_2():
    with instance_for_test() as instance:
        parent_result = execute_job(reconstructable(dynamic_pipeline), instance=instance)
        parent_run_id = parent_result.run_id

        with execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=parent_run_id,
                step_selection=["multiply_by_two[1]"],
            ),
        ) as reexec_result:
            assert reexec_result.success
            assert reexec_result.output_for_node("multiply_by_two") == {
                "1": 20,
            }


def test_reexec_from_parent_3():
    with instance_for_test() as instance:
        parent_result = execute_job(reconstructable(dynamic_pipeline), instance=instance)
        parent_run_id = parent_result.run_id

        with execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=parent_run_id,
                step_selection=["multiply_inputs[1]", "multiply_by_two[2]"],
            ),
        ) as reexec_result:
            assert reexec_result.success
            assert reexec_result.output_for_node("multiply_inputs") == {
                "1": 10,
            }
            assert reexec_result.output_for_node("multiply_by_two") == {
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
                # re-execution run skipped odd numbers
                context.pipeline_run.parent_run_id
                and i % 2 == 0
            ) or (
                # root run skipped even numbers
                not context.pipeline_run.parent_run_id
                and i % 2 == 1
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
        with execute_job(
            reconstructable(dynamic_with_optional_output_job),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=result.run_id,
            ),
        ) as re_result:
            assert re_result.success
            assert re_result.output_for_node("adder") == sum([i for i in range(10) if i % 2 == 0])


def test_reexec_dynamic_with_optional_output_job_2():
    with instance_for_test() as instance:
        result = dynamic_with_optional_output_job().execute_in_process(instance=instance)

        # re-execute the step where the source yielded an output
        with execute_job(
            reconstructable(dynamic_with_optional_output_job),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=result.run_id,
                step_selection=["echo[1]"],
            ),
        ) as re_result:
            assert re_result.success
            assert re_result.output_for_node("echo") == {
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
            execute_job(
                reconstructable(dynamic_with_optional_output_job),
                instance=instance,
                reexecution_options=ReexecutionOptions(
                    parent_run_id=result.run_id,
                    step_selection=["echo[0]"],
                ),
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
        with execute_job(
            reconstructable(dynamic_with_transitive_optional_output_job),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=result.run_id,
            ),
        ) as re_result:
            assert re_result.success
            assert re_result.output_for_node("adder") == sum(
                [i + 1 for i in range(10) if i % 2 == 0]
            )


def test_reexec_dynamic_with_transitive_optional_output_job_2():
    with instance_for_test() as instance:
        result = dynamic_with_transitive_optional_output_job().execute_in_process(instance=instance)

        # re-execute the step where the source yielded an output
        with execute_job(
            reconstructable(dynamic_with_transitive_optional_output_job),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=result.run_id,
                step_selection=["echo[1]"],
            ),
        ) as re_result:
            assert re_result.success
            assert re_result.output_for_node("echo") == {"1": 2}


def test_reexec_dynamic_with_transitive_optional_output_job_3():
    with instance_for_test() as instance:
        result = dynamic_with_transitive_optional_output_job().execute_in_process(instance=instance)

        # re-execute the step where the source did not yield
        re_result = execute_job(
            reconstructable(dynamic_with_transitive_optional_output_job),
            instance=instance,
            raise_on_error=False,
            reexecution_options=ReexecutionOptions(
                parent_run_id=result.run_id,
                step_selection=["echo[0]"],
            ),
        )
        # when all the previous runs have skipped yielding the source,
        # run would fail because of run_id returns None
        # FIXME: https://github.com/dagster-io/dagster/issues/3511
        # ideally it should skip the step because all its previous runs have skipped and finish the run successfully
        assert not re_result.success
