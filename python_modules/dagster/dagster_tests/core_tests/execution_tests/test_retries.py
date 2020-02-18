from collections import defaultdict

import pytest

from dagster import (
    DagsterEventType,
    ExecutionTargetHandle,
    Output,
    OutputDefinition,
    RetryRequested,
    RunConfig,
    execute_pipeline,
    lambda_solid,
    pipeline,
    solid,
)
from dagster.core.instance import DagsterInstance

executors = pytest.mark.parametrize(
    "environment",
    [
        {'storage': {'filesystem': {}}},
        {'storage': {'filesystem': {}}, 'execution': {'multiprocess': {}}},
    ],
)


def define_run_retry_pipeline():
    @solid(config={'fail': bool})
    def can_fail(context, _start_fail):
        if context.solid_config['fail']:
            raise Exception('blah')

        return 'okay perfect'

    @solid(
        output_defs=[
            OutputDefinition(bool, 'start_fail', is_required=False),
            OutputDefinition(bool, 'start_skip', is_required=False),
        ]
    )
    def two_outputs(_):
        yield Output(True, 'start_fail')
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
    instance = DagsterInstance.local_temp()
    pipe = ExecutionTargetHandle.for_pipeline_python_file(
        __file__, 'define_run_retry_pipeline'
    ).build_pipeline_definition()
    fails = dict(environment)
    fails['solids'] = {'can_fail': {'config': {'fail': True}}}

    result = execute_pipeline(
        pipe, environment_dict=fails, instance=instance, raise_on_error=False,
    )

    passes = dict(environment)
    passes['solids'] = {'can_fail': {'config': {'fail': False}}}
    second_result = execute_pipeline(
        pipe,
        environment_dict=passes,
        run_config=RunConfig(previous_run_id=result.run_id),
        instance=instance,
    )

    assert second_result.success
    downstream_of_failed = second_result.result_for_solid('downstream_of_failed').output_value()
    assert downstream_of_failed == 'okay perfect'

    will_be_skipped = [
        e for e in second_result.event_list if 'will_be_skipped' in str(e.solid_handle)
    ]
    assert str(will_be_skipped[0].event_type_value) == 'STEP_SKIPPED'
    assert str(will_be_skipped[1].event_type_value) == 'STEP_SKIPPED'


def define_step_retry_pipeline():
    # this works since we handle step retries in the same single subprocess
    fail = {'count': 0}

    @lambda_solid
    def fail_first_time():
        if fail['count'] < 1:
            fail['count'] += 1
            raise RetryRequested()

        return 'okay perfect'

    @pipeline
    def step_retry():
        fail_first_time()

    return step_retry


@executors
def test_step_retry(environment):

    result = execute_pipeline(
        ExecutionTargetHandle.for_pipeline_python_file(
            __file__, 'define_step_retry_pipeline'
        ).build_pipeline_definition(),
        environment_dict=environment,
        instance=DagsterInstance.local_temp(),
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
    result = execute_pipeline(
        ExecutionTargetHandle.for_pipeline_python_file(
            __file__, 'define_retry_limit_pipeline'
        ).build_pipeline_definition(),
        environment_dict=environment,
        raise_on_error=False,
        instance=DagsterInstance.local_temp(),
    )
    assert not result.success

    events = defaultdict(list)
    for ev in result.events_by_step_key['default_max.compute']:
        events[ev.event_type].append(ev)

    assert len(events[DagsterEventType.STEP_START]) == 1
    assert len(events[DagsterEventType.STEP_UP_FOR_RETRY]) == 1
    assert len(events[DagsterEventType.STEP_RESTARTED]) == 1
    assert len(events[DagsterEventType.STEP_FAILURE]) == 1

    events = defaultdict(list)
    for ev in result.events_by_step_key['three_max.compute']:
        events[ev.event_type].append(ev)

    assert len(events[DagsterEventType.STEP_START]) == 1
    assert len(events[DagsterEventType.STEP_UP_FOR_RETRY]) == 3
    assert len(events[DagsterEventType.STEP_RESTARTED]) == 3
    assert len(events[DagsterEventType.STEP_FAILURE]) == 1
