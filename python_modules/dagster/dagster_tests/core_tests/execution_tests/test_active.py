import pytest

from dagster import job, op
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.plan.objects import StepSuccessData
from dagster._core.execution.plan.outputs import StepOutputData, StepOutputHandle
from dagster._core.execution.retries import RetryMode


def define_foo_job():
    @op
    def foo_op():
        pass

    @job
    def foo_job():
        foo_op()

    return foo_job


def test_recover_with_step_in_flight():
    foo_job = define_foo_job()

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Execution finished without completing the execution plan",
    ):
        with create_execution_plan(foo_job).start(RetryMode.DISABLED) as active_execution:
            steps = active_execution.get_steps_to_execute()
            assert len(steps) == 1
            step_1 = steps[0]
            assert step_1.key == "foo_op"

            active_execution.handle_event(
                DagsterEvent(
                    DagsterEventType.STEP_START.value,
                    pipeline_name=foo_job.name,
                    step_key=step_1.key,
                )
            )

    # CRASH!- we've closed the active execution. Now we recover, spinning up a new one

    with create_execution_plan(foo_job).start(RetryMode.DISABLED) as active_execution:
        possibly_in_flight_steps = active_execution.rebuild_from_events(
            [
                DagsterEvent(
                    DagsterEventType.STEP_START.value,
                    pipeline_name=foo_job.name,
                    step_key=step_1.key,
                )
            ]
        )
        assert possibly_in_flight_steps == [step_1]

        assert not active_execution.get_steps_to_execute()

        active_execution.handle_event(
            DagsterEvent(
                DagsterEventType.STEP_SUCCESS.value,
                pipeline_name=foo_job.name,
                event_specific_data=StepSuccessData(duration_ms=10.0),
                step_key=step_1.key,
            )
        )


def define_two_op_job():
    @op
    def foo_op():
        pass

    @op
    def bar_op(_data):
        pass

    @job
    def two_op_job():
        bar_op(foo_op())

    return two_op_job


def test_recover_in_between_steps():
    two_op_job = define_two_op_job()

    events = [
        DagsterEvent(
            DagsterEventType.STEP_START.value,
            pipeline_name=two_op_job.name,
            step_key="foo_op",
        ),
        DagsterEvent(
            DagsterEventType.STEP_OUTPUT.value,
            pipeline_name=two_op_job.name,
            event_specific_data=StepOutputData(
                StepOutputHandle(step_key="foo_op", output_name="result")
            ),
            step_key="foo_op",
        ),
        DagsterEvent(
            DagsterEventType.STEP_SUCCESS.value,
            pipeline_name=two_op_job.name,
            event_specific_data=StepSuccessData(duration_ms=10.0),
            step_key="foo_op",
        ),
    ]

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Execution finished without completing the execution plan",
    ):
        with create_execution_plan(two_op_job).start(RetryMode.DISABLED) as active_execution:
            steps = active_execution.get_steps_to_execute()
            assert len(steps) == 1
            step_1 = steps[0]
            assert step_1.key == "foo_op"

            active_execution.handle_event(events[0])
            active_execution.handle_event(events[1])
            active_execution.handle_event(events[2])

    # CRASH!- we've closed the active execution. Now we recover, spinning up a new one

    with create_execution_plan(two_op_job).start(RetryMode.DISABLED) as active_execution:
        possibly_in_flight_steps = active_execution.rebuild_from_events(events)
        assert len(possibly_in_flight_steps) == 1
        step_2 = possibly_in_flight_steps[0]
        assert step_2.key == "bar_op"

        assert not active_execution.get_steps_to_execute()

        active_execution.handle_event(
            DagsterEvent(
                DagsterEventType.STEP_START.value,
                pipeline_name=two_op_job.name,
                step_key="bar_op",
            )
        )
        active_execution.handle_event(
            DagsterEvent(
                DagsterEventType.STEP_SUCCESS.value,
                pipeline_name=two_op_job.name,
                event_specific_data=StepSuccessData(duration_ms=10.0),
                step_key="bar_op",
            )
        )
