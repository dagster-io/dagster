import os
import tempfile
import time
from collections import defaultdict

import pytest
from dagster import (
    DagsterEventType,
    Output,
    OutputDefinition,
    PipelineRun,
    RetryRequested,
    execute_pipeline,
    execute_pipeline_iterator,
    lambda_solid,
    pipeline,
    reconstructable,
    reexecute_pipeline,
    solid,
)
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.execution.retries import RetryMode
from dagster.core.test_utils import instance_for_test

executors = pytest.mark.parametrize(
    "environment",
    [
        {"intermediate_storage": {"filesystem": {}}},
        {"intermediate_storage": {"filesystem": {}}, "execution": {"multiprocess": {}}},
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

    @pipeline
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

    @pipeline
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

    @pipeline
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

    @pipeline
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
