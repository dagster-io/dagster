import math
import tempfile
from collections import defaultdict
from typing import List, Set

import pytest
from dagster import job, op
from dagster._core.errors import DagsterExecutionInterruptedError, DagsterInvariantViolationError
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.plan.instance_concurrency_context import InstanceConcurrencyContext
from dagster._core.execution.plan.objects import StepRetryData, StepSuccessData
from dagster._core.execution.plan.outputs import StepOutputData, StepOutputHandle
from dagster._core.execution.retries import RetryMode
from dagster._core.storage.tags import GLOBAL_CONCURRENCY_TAG
from dagster._core.test_utils import instance_for_test
from dagster._core.utils import make_new_run_id
from dagster._utils.error import SerializableErrorInfo


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

    with instance_for_test():
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
                        job_name=foo_job.name,
                        step_key=step_1.key,
                    )
                )

        # CRASH!- we've closed the active execution. Now we recover, spinning up a new one

        with create_execution_plan(foo_job).start(RetryMode.DISABLED) as active_execution:
            possibly_in_flight_steps = active_execution.rebuild_from_events(
                [
                    DagsterEvent(
                        DagsterEventType.STEP_START.value,
                        job_name=foo_job.name,
                        step_key=step_1.key,
                    )
                ]
            )
            assert possibly_in_flight_steps == [step_1]

            assert not active_execution.get_steps_to_execute()

            active_execution.handle_event(
                DagsterEvent(
                    DagsterEventType.STEP_SUCCESS.value,
                    job_name=foo_job.name,
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
            job_name=two_op_job.name,
            step_key="foo_op",
        ),
        DagsterEvent(
            DagsterEventType.STEP_OUTPUT.value,
            job_name=two_op_job.name,
            event_specific_data=StepOutputData(
                StepOutputHandle(step_key="foo_op", output_name="result")
            ),
            step_key="foo_op",
        ),
        DagsterEvent(
            DagsterEventType.STEP_SUCCESS.value,
            job_name=two_op_job.name,
            event_specific_data=StepSuccessData(duration_ms=10.0),
            step_key="foo_op",
        ),
    ]

    with instance_for_test():
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
                    job_name=two_op_job.name,
                    step_key="bar_op",
                )
            )
            active_execution.handle_event(
                DagsterEvent(
                    DagsterEventType.STEP_SUCCESS.value,
                    job_name=two_op_job.name,
                    event_specific_data=StepSuccessData(duration_ms=10.0),
                    step_key="bar_op",
                )
            )


def define_concurrency_job():
    @op(tags={GLOBAL_CONCURRENCY_TAG: "foo"})
    def foo_op():
        pass

    @op(tags={GLOBAL_CONCURRENCY_TAG: "foo"})
    def bar_op():
        pass

    @job
    def foo_job():
        foo_op()
        bar_op()

    return foo_job


def test_active_concurrency():
    foo_job = define_concurrency_job()
    run_id = make_new_run_id()

    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(
            overrides={
                "event_log_storage": {
                    "module": "dagster.utils.test",
                    "class": "ConcurrencyEnabledSqliteTestEventLogStorage",
                    "config": {"base_dir": temp_dir},
                },
            }
        ) as instance:
            assert instance.event_log_storage.supports_global_concurrency_limits

            instance.event_log_storage.set_concurrency_slots("foo", 1)
            run = instance.create_run_for_job(foo_job, run_id=run_id)

            with pytest.raises(
                DagsterInvariantViolationError,
                match="Execution finished without completing the execution plan",
            ):
                with InstanceConcurrencyContext(instance, run) as instance_concurrency_context:
                    with create_execution_plan(foo_job).start(
                        RetryMode.DISABLED,
                        instance_concurrency_context=instance_concurrency_context,
                    ) as active_execution:
                        steps = active_execution.get_steps_to_execute()
                        assert len(steps) == 1
                        step_1 = steps[0]

                        foo_info = instance.event_log_storage.get_concurrency_info("foo")
                        assert foo_info.active_slot_count == 1
                        assert foo_info.active_run_ids == {run_id}
                        assert foo_info.pending_step_count == 1
                        assert foo_info.assigned_step_count == 1

                        active_execution.handle_event(
                            DagsterEvent(
                                DagsterEventType.STEP_START.value,
                                job_name=foo_job.name,
                                step_key=step_1.key,
                            )
                        )

            foo_info = instance.event_log_storage.get_concurrency_info("foo")
            assert foo_info.active_slot_count == 1
            assert foo_info.active_run_ids == {run_id}
            assert foo_info.pending_step_count == 0
            assert foo_info.assigned_step_count == 1


class MockInstanceConcurrencyContext(InstanceConcurrencyContext):
    def __init__(self, interval: float):
        self._interval = interval
        self._pending_timeouts = defaultdict(float)
        self._pending_claims = set()

    @property
    def global_concurrency_keys(self) -> set[str]:
        return {"foo"}

    def claim(self, concurrency_key: str, step_key: str, priority: int = 0):
        self._pending_claims.add(step_key)
        return False

    def interval_to_next_pending_claim_check(self) -> float:
        return self._interval

    def pending_claim_steps(self) -> list[str]:
        return list(self._pending_claims)

    def has_pending_claims(self) -> bool:
        return len(self._pending_claims) > 0

    def free_step(self, step_key) -> None:
        pass


def define_concurrency_retry_job():
    @op(tags={GLOBAL_CONCURRENCY_TAG: "foo"})
    def foo_op():
        pass

    @op
    def bar_op():
        pass

    @job
    def foo_job():
        foo_op()
        bar_op()

    return foo_job


def test_active_concurrency_sleep():
    instance_concurrency_context = MockInstanceConcurrencyContext(2.0)
    foo_job = define_concurrency_retry_job()
    with pytest.raises(DagsterExecutionInterruptedError):
        with create_execution_plan(foo_job).start(
            RetryMode.ENABLED,
            instance_concurrency_context=instance_concurrency_context,
        ) as active_execution:
            steps = active_execution.get_steps_to_execute()

            assert len(steps) == 1
            step = steps[0]
            assert step.key == "bar_op"

            # start the step
            active_execution.handle_event(
                DagsterEvent(
                    DagsterEventType.STEP_START.value,
                    job_name=foo_job.name,
                    step_key=step.key,
                )
            )

            assert instance_concurrency_context.has_pending_claims()
            assert math.isclose(active_execution.sleep_interval(), 2.0, abs_tol=0.1)

            error_info = SerializableErrorInfo("Exception", [], None)

            # retry the step
            active_execution.handle_event(
                DagsterEvent(
                    DagsterEventType.STEP_UP_FOR_RETRY.value,
                    job_name=foo_job.name,
                    step_key=step.key,
                    event_specific_data=StepRetryData(error=error_info, seconds_to_wait=1),
                )
            )
            assert math.isclose(active_execution.sleep_interval(), 1.0, abs_tol=0.1)
            active_execution.mark_interrupted()

    instance_concurrency_context = MockInstanceConcurrencyContext(2.0)
    with pytest.raises(DagsterExecutionInterruptedError):
        with create_execution_plan(foo_job).start(
            RetryMode.ENABLED,
            instance_concurrency_context=instance_concurrency_context,
        ) as active_execution:
            steps = active_execution.get_steps_to_execute()

            assert len(steps) == 1
            step = steps[0]
            assert step.key == "bar_op"

            # start the step
            active_execution.handle_event(
                DagsterEvent(
                    DagsterEventType.STEP_START.value,
                    job_name=foo_job.name,
                    step_key=step.key,
                )
            )

            assert instance_concurrency_context.has_pending_claims()
            assert math.isclose(active_execution.sleep_interval(), 2.0, abs_tol=0.1)

            error_info = SerializableErrorInfo("Exception", [], None)

            # retry the step
            active_execution.handle_event(
                DagsterEvent(
                    DagsterEventType.STEP_UP_FOR_RETRY.value,
                    job_name=foo_job.name,
                    step_key=step.key,
                    event_specific_data=StepRetryData(error=error_info, seconds_to_wait=3),
                )
            )
            assert math.isclose(active_execution.sleep_interval(), 2.0, abs_tol=0.1)
            active_execution.mark_interrupted()
