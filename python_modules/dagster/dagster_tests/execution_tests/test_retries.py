import os
import tempfile
import time
from collections import defaultdict
from typing import List

import pytest
from dagster import (
    Backoff,
    DagsterEventType,
    Failure,
    Jitter,
    Output,
    OutputDefinition,
    PipelineRun,
    RetryPolicy,
    RetryRequested,
    execute_pipeline,
    execute_pipeline_iterator,
    graph,
    job,
    lambda_solid,
    op,
    pipeline,
    reconstructable,
    reexecute_pipeline,
    solid,
    success_hook,
)
from dagster.core.definitions.events import HookExecutionResult
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.events import DagsterEvent
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.execution.retries import RetryMode
from dagster.core.test_utils import default_mode_def_for_test, instance_for_test

executors = pytest.mark.parametrize(
    "environment",
    [
        {},
        {"execution": {"multiprocess": {}}},
    ],
)


def define_run_retry_pipeline():
    @solid(config_schema={"fail": bool})
    def can_fail(context, _start_fail):
        if context.solid_config["fail"]:
            raise Exception("blah")

        return "okay perfect"

    @solid(
        output_defs=[
            OutputDefinition(bool, "start_fail", is_required=False),
            OutputDefinition(bool, "start_skip", is_required=False),
        ]
    )
    def two_outputs(_):
        yield Output(True, "start_fail")
        # won't yield start_skip

    @solid
    def will_be_skipped(_, _start_skip):
        pass  # doesn't matter

    @solid
    def downstream_of_failed(_, input_str):
        return input_str

    @pipeline(mode_defs=[default_mode_def_for_test])
    def pipe():
        start_fail, start_skip = two_outputs()
        downstream_of_failed(can_fail(start_fail))
        will_be_skipped(will_be_skipped(start_skip))

    return pipe


@executors
def test_retries(environment):
    with instance_for_test() as instance:
        pipe = reconstructable(define_run_retry_pipeline)
        fails = dict(environment)
        fails["solids"] = {"can_fail": {"config": {"fail": True}}}

        result = execute_pipeline(
            pipe,
            run_config=fails,
            instance=instance,
            raise_on_error=False,
        )

        assert not result.success

        passes = dict(environment)
        passes["solids"] = {"can_fail": {"config": {"fail": False}}}

        second_result = reexecute_pipeline(
            pipe,
            parent_run_id=result.run_id,
            run_config=passes,
            instance=instance,
        )
        assert second_result.success
        downstream_of_failed = second_result.result_for_solid("downstream_of_failed").output_value()
        assert downstream_of_failed == "okay perfect"

        will_be_skipped = [
            e for e in second_result.event_list if "will_be_skipped" in str(e.solid_handle)
        ]
        assert str(will_be_skipped[0].event_type_value) == "STEP_SKIPPED"
        assert str(will_be_skipped[1].event_type_value) == "STEP_SKIPPED"


def define_step_retry_pipeline():
    @solid(config_schema=str)
    def fail_first_time(context):
        file = os.path.join(context.solid_config, "i_threw_up")
        if os.path.exists(file):
            return "okay perfect"
        else:
            open(file, "a").close()
            raise RetryRequested()

    @pipeline(mode_defs=[default_mode_def_for_test])
    def step_retry():
        fail_first_time()

    return step_retry


@executors
def test_step_retry(environment):
    with instance_for_test() as instance:
        with tempfile.TemporaryDirectory() as tempdir:
            env = dict(environment)
            env["solids"] = {"fail_first_time": {"config": tempdir}}
            result = execute_pipeline(
                reconstructable(define_step_retry_pipeline),
                run_config=env,
                instance=instance,
            )
        assert result.success
        events = defaultdict(list)
        for ev in result.event_list:
            events[ev.event_type].append(ev)

        assert len(events[DagsterEventType.STEP_START]) == 1
        assert len(events[DagsterEventType.STEP_UP_FOR_RETRY]) == 1
        assert len(events[DagsterEventType.STEP_RESTARTED]) == 1
        assert len(events[DagsterEventType.STEP_SUCCESS]) == 1


def define_retry_limit_pipeline():
    @lambda_solid
    def default_max():
        raise RetryRequested()

    @lambda_solid
    def three_max():
        raise RetryRequested(max_retries=3)

    @pipeline(mode_defs=[default_mode_def_for_test])
    def retry_limits():
        default_max()
        three_max()

    return retry_limits


@executors
def test_step_retry_limit(environment):
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(define_retry_limit_pipeline),
            run_config=environment,
            raise_on_error=False,
            instance=instance,
        )
        assert not result.success

        events = defaultdict(list)
        for ev in result.events_by_step_key["default_max"]:
            events[ev.event_type].append(ev)

        assert len(events[DagsterEventType.STEP_START]) == 1
        assert len(events[DagsterEventType.STEP_UP_FOR_RETRY]) == 1
        assert len(events[DagsterEventType.STEP_RESTARTED]) == 1
        assert len(events[DagsterEventType.STEP_FAILURE]) == 1

        events = defaultdict(list)
        for ev in result.events_by_step_key["three_max"]:
            events[ev.event_type].append(ev)

        assert len(events[DagsterEventType.STEP_START]) == 1
        assert len(events[DagsterEventType.STEP_UP_FOR_RETRY]) == 3
        assert len(events[DagsterEventType.STEP_RESTARTED]) == 3
        assert len(events[DagsterEventType.STEP_FAILURE]) == 1


def test_retry_deferral():
    with instance_for_test() as instance:
        pipeline_def = define_retry_limit_pipeline()
        events = execute_plan(
            create_execution_plan(pipeline_def),
            InMemoryPipeline(pipeline_def),
            pipeline_run=PipelineRun(pipeline_name="retry_limits", run_id="42"),
            retry_mode=RetryMode.DEFERRED,
            instance=instance,
        )
        events_by_type = defaultdict(list)
        for ev in events:
            events_by_type[ev.event_type].append(ev)

        assert len(events_by_type[DagsterEventType.STEP_START]) == 2
        assert len(events_by_type[DagsterEventType.STEP_UP_FOR_RETRY]) == 2
        assert DagsterEventType.STEP_RESTARTED not in events
        assert DagsterEventType.STEP_SUCCESS not in events


DELAY = 2


def define_retry_wait_fixed_pipeline():
    @solid(config_schema=str)
    def fail_first_and_wait(context):
        file = os.path.join(context.solid_config, "i_threw_up")
        if os.path.exists(file):
            return "okay perfect"
        else:
            open(file, "a").close()
            raise RetryRequested(seconds_to_wait=DELAY)

    @pipeline(mode_defs=[default_mode_def_for_test])
    def step_retry():
        fail_first_and_wait()

    return step_retry


@executors
def test_step_retry_fixed_wait(environment):
    with instance_for_test() as instance:
        with tempfile.TemporaryDirectory() as tempdir:
            env = dict(environment)
            env["solids"] = {"fail_first_and_wait": {"config": tempdir}}

            event_iter = execute_pipeline_iterator(
                reconstructable(define_retry_wait_fixed_pipeline),
                run_config=env,
                instance=instance,
            )
            start_wait = None
            end_wait = None
            success = None
            for event in event_iter:
                if event.is_step_up_for_retry:
                    start_wait = time.time()
                if event.is_step_restarted:
                    end_wait = time.time()
                if event.is_pipeline_success:
                    success = True

            assert success
            assert start_wait is not None
            assert end_wait is not None
            delay = end_wait - start_wait
            assert delay > DELAY


def test_basic_retry_policy():
    @solid(retry_policy=RetryPolicy())
    def throws(_):
        raise Exception("I fail")

    @pipeline
    def policy_test():
        throws()

    result = execute_pipeline(policy_test, raise_on_error=False)
    assert not result.success
    assert result.result_for_solid("throws").retry_attempts == 1


def test_retry_policy_rules():
    @solid(retry_policy=RetryPolicy(max_retries=2))
    def throw_with_policy():
        raise Exception("I throw")

    @solid
    def throw_no_policy():
        raise Exception("I throw")

    @solid
    def fail_no_policy():
        raise Failure("I fail")

    @pipeline(solid_retry_policy=RetryPolicy(max_retries=3))
    def policy_test():
        throw_with_policy()
        throw_no_policy()
        throw_with_policy.with_retry_policy(RetryPolicy(max_retries=1)).alias("override_with")()
        throw_no_policy.alias("override_no").with_retry_policy(RetryPolicy(max_retries=1))()
        throw_no_policy.configured({"jonx": True}, name="config_override_no").with_retry_policy(
            RetryPolicy(max_retries=1)
        )()
        fail_no_policy.alias("override_fail").with_retry_policy(RetryPolicy(max_retries=1))()

    result = execute_pipeline(policy_test, raise_on_error=False)
    assert not result.success
    assert result.result_for_solid("throw_no_policy").retry_attempts == 3
    assert result.result_for_solid("throw_with_policy").retry_attempts == 2
    assert result.result_for_solid("override_no").retry_attempts == 1
    assert result.result_for_solid("override_with").retry_attempts == 1
    assert result.result_for_solid("config_override_no").retry_attempts == 1
    assert result.result_for_solid("override_fail").retry_attempts == 1


def test_delay():
    delay = 0.3

    @solid(retry_policy=RetryPolicy(delay=delay))
    def throws(_):
        raise Exception("I fail")

    @pipeline
    def policy_test():
        throws()

    start = time.time()
    result = execute_pipeline(policy_test, raise_on_error=False)
    elapsed_time = time.time() - start
    assert not result.success
    assert elapsed_time > delay
    assert result.result_for_solid("throws").retry_attempts == 1


def test_policy_delay_calc():
    empty = RetryPolicy()
    assert empty.calculate_delay(1) == 0
    assert empty.calculate_delay(2) == 0
    assert empty.calculate_delay(3) == 0

    one = RetryPolicy(delay=1)
    assert one.calculate_delay(1) == 1
    assert one.calculate_delay(2) == 1
    assert one.calculate_delay(3) == 1

    one_linear = RetryPolicy(delay=1, backoff=Backoff.LINEAR)
    assert one_linear.calculate_delay(1) == 1
    assert one_linear.calculate_delay(2) == 2
    assert one_linear.calculate_delay(3) == 3

    one_expo = RetryPolicy(delay=1, backoff=Backoff.EXPONENTIAL)
    assert one_expo.calculate_delay(1) == 1
    assert one_expo.calculate_delay(2) == 3
    assert one_expo.calculate_delay(3) == 7

    # jitter

    one_linear_full = RetryPolicy(delay=1, backoff=Backoff.LINEAR, jitter=Jitter.FULL)
    one_expo_full = RetryPolicy(delay=1, backoff=Backoff.EXPONENTIAL, jitter=Jitter.FULL)
    one_linear_pm = RetryPolicy(delay=1, backoff=Backoff.LINEAR, jitter=Jitter.PLUS_MINUS)
    one_expo_pm = RetryPolicy(delay=1, backoff=Backoff.EXPONENTIAL, jitter=Jitter.PLUS_MINUS)
    one_full = RetryPolicy(delay=1, jitter=Jitter.FULL)
    one_pm = RetryPolicy(delay=1, jitter=Jitter.PLUS_MINUS)

    # test many times to navigate randomness
    for _ in range(100):
        assert 0 < one_linear_full.calculate_delay(2) < 2
        assert 0 < one_linear_full.calculate_delay(3) < 3
        assert 0 < one_expo_full.calculate_delay(2) < 3
        assert 0 < one_expo_full.calculate_delay(3) < 7

        assert 2 < one_linear_pm.calculate_delay(3) < 4
        assert 3 < one_linear_pm.calculate_delay(4) < 5

        assert 6 < one_expo_pm.calculate_delay(3) < 8
        assert 14 < one_expo_pm.calculate_delay(4) < 16

        assert 0 < one_full.calculate_delay(100) < 1
        assert 0 < one_pm.calculate_delay(100) < 2

    with pytest.raises(DagsterInvalidDefinitionError):
        RetryPolicy(jitter=Jitter.PLUS_MINUS)

    with pytest.raises(DagsterInvalidDefinitionError):
        RetryPolicy(backoff=Backoff.EXPONENTIAL)


def test_linear_backoff():
    delay = 0.1
    logged_times = []

    @solid
    def throws(_):
        logged_times.append(time.time())
        raise Exception("I fail")

    @pipeline
    def linear_backoff():
        throws.with_retry_policy(RetryPolicy(max_retries=3, delay=delay, backoff=Backoff.LINEAR))()

    execute_pipeline(linear_backoff)
    assert len(logged_times) == 4
    assert (logged_times[1] - logged_times[0]) > delay
    assert (logged_times[2] - logged_times[1]) > (delay * 2)
    assert (logged_times[3] - logged_times[2]) > (delay * 3)


def test_expo_backoff():
    delay = 0.1
    logged_times = []

    @solid
    def throws(_):
        logged_times.append(time.time())
        raise Exception("I fail")

    @pipeline
    def expo_backoff():
        throws.with_retry_policy(
            RetryPolicy(max_retries=3, delay=delay, backoff=Backoff.EXPONENTIAL)
        )()

    execute_pipeline(expo_backoff)
    assert len(logged_times) == 4
    assert (logged_times[1] - logged_times[0]) > delay
    assert (logged_times[2] - logged_times[1]) > (delay * 3)
    assert (logged_times[3] - logged_times[2]) > (delay * 7)


def _get_retry_events(events: List[DagsterEvent]):
    return list(
        filter(
            lambda evt: evt.event_type == DagsterEventType.STEP_UP_FOR_RETRY,
            events,
        )
    )


def test_basic_op_retry_policy():
    @op(retry_policy=RetryPolicy())
    def throws(_):
        raise Exception("I fail")

    @job
    def policy_test():
        throws()

    result = policy_test.execute_in_process(raise_on_error=False)
    assert not result.success
    assert len(_get_retry_events(result.events_for_node("throws"))) == 1


def test_retry_policy_rules_job():
    @op(retry_policy=RetryPolicy(max_retries=2))
    def throw_with_policy():
        raise Exception("I throw")

    @op
    def throw_no_policy():
        raise Exception("I throw")

    @op
    def fail_no_policy():
        raise Failure("I fail")

    @job(op_retry_policy=RetryPolicy(max_retries=3))
    def policy_test():
        throw_with_policy()
        throw_no_policy()
        throw_with_policy.with_retry_policy(RetryPolicy(max_retries=1)).alias("override_with")()
        throw_no_policy.alias("override_no").with_retry_policy(RetryPolicy(max_retries=1))()
        throw_no_policy.configured({"jonx": True}, name="config_override_no").with_retry_policy(
            RetryPolicy(max_retries=1)
        )()
        fail_no_policy.alias("override_fail").with_retry_policy(RetryPolicy(max_retries=1))()

    result = policy_test.execute_in_process(raise_on_error=False)
    assert not result.success
    assert len(_get_retry_events(result.events_for_node("throw_no_policy"))) == 3
    assert len(_get_retry_events(result.events_for_node("throw_with_policy"))) == 2
    assert len(_get_retry_events(result.events_for_node("override_no"))) == 1
    assert len(_get_retry_events(result.events_for_node("override_with"))) == 1
    assert len(_get_retry_events(result.events_for_node("config_override_no"))) == 1
    assert len(_get_retry_events(result.events_for_node("override_fail"))) == 1


def test_basic_op_retry_policy_subset():
    @op
    def do_nothing():
        pass

    @op
    def throws(_):
        raise Exception("I fail")

    @job(op_retry_policy=RetryPolicy())
    def policy_test():
        throws()
        do_nothing()

    result = policy_test.execute_in_process(raise_on_error=False, op_selection=["throws"])
    assert not result.success
    assert len(_get_retry_events(result.events_for_node("throws"))) == 1


def test_retry_policy_rules_on_graph_to_job():
    @op(retry_policy=RetryPolicy(max_retries=2))
    def throw_with_policy():
        raise Exception("I throw")

    @op
    def throw_no_policy():
        raise Exception("I throw")

    @op
    def fail_no_policy():
        raise Failure("I fail")

    @graph
    def policy_test():
        throw_with_policy()
        throw_no_policy()
        throw_with_policy.with_retry_policy(RetryPolicy(max_retries=1)).alias("override_with")()
        throw_no_policy.alias("override_no").with_retry_policy(RetryPolicy(max_retries=1))()
        throw_no_policy.configured({"jonx": True}, name="config_override_no").with_retry_policy(
            RetryPolicy(max_retries=1)
        )()
        fail_no_policy.alias("override_fail").with_retry_policy(RetryPolicy(max_retries=1))()

    my_job = policy_test.to_job(op_retry_policy=RetryPolicy(max_retries=3))
    result = my_job.execute_in_process(raise_on_error=False)
    assert not result.success
    assert len(_get_retry_events(result.events_for_node("throw_no_policy"))) == 3
    assert len(_get_retry_events(result.events_for_node("throw_with_policy"))) == 2
    assert len(_get_retry_events(result.events_for_node("override_no"))) == 1
    assert len(_get_retry_events(result.events_for_node("override_with"))) == 1
    assert len(_get_retry_events(result.events_for_node("config_override_no"))) == 1
    assert len(_get_retry_events(result.events_for_node("override_fail"))) == 1


def test_retry_policy_rules_on_pending_node_invocation_to_job():
    @success_hook
    def a_hook(_):
        return HookExecutionResult("a_hook")

    @op(retry_policy=RetryPolicy(max_retries=2))
    def throw_with_policy():
        raise Exception("I throw")

    @op
    def throw_no_policy():
        raise Exception("I throw")

    @op
    def fail_no_policy():
        raise Failure("I fail")

    @a_hook  # turn policy_test into a PendingNodeInvocation
    @graph
    def policy_test():
        throw_with_policy()
        throw_no_policy()
        throw_with_policy.with_retry_policy(RetryPolicy(max_retries=1)).alias("override_with")()
        throw_no_policy.alias("override_no").with_retry_policy(RetryPolicy(max_retries=1))()
        throw_no_policy.configured({"jonx": True}, name="config_override_no").with_retry_policy(
            RetryPolicy(max_retries=1)
        )()
        fail_no_policy.alias("override_fail").with_retry_policy(RetryPolicy(max_retries=1))()

    my_job = policy_test.to_job(op_retry_policy=RetryPolicy(max_retries=3))
    result = my_job.execute_in_process(raise_on_error=False)
    assert not result.success
    assert len(_get_retry_events(result.events_for_node("throw_no_policy"))) == 3
    assert len(_get_retry_events(result.events_for_node("throw_with_policy"))) == 2
    assert len(_get_retry_events(result.events_for_node("override_no"))) == 1
    assert len(_get_retry_events(result.events_for_node("override_with"))) == 1
    assert len(_get_retry_events(result.events_for_node("config_override_no"))) == 1
    assert len(_get_retry_events(result.events_for_node("override_fail"))) == 1
