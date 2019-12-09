import os
import random
import string
import sys

import pytest

from dagster import DagsterEventType, execute_pipeline, lambda_solid, pipeline
from dagster.core.execution.compute_logs import should_disable_io_stream_redirect
from dagster.core.instance import DagsterInstance
from dagster.core.storage.compute_log_manager import ComputeIOType


@lambda_solid
def spew():
    print(HELLO_WORLD)
    return


@pipeline
def spew_pipeline():
    spew()


HELLO_WORLD = 'Hello World'
SEPARATOR = os.linesep if (os.name == 'nt' and sys.version_info < (3,)) else '\n'


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_stdout():
    instance = DagsterInstance.local_temp()
    manager = instance.compute_log_manager
    result = execute_pipeline(spew_pipeline, instance=instance)
    assert result.success
    compute_steps = [
        event.step_key
        for event in result.step_event_list
        if event.event_type == DagsterEventType.STEP_START
    ]
    assert len(compute_steps) == 1
    step_key = compute_steps[0]
    assert manager.is_compute_completed(result.run_id, step_key)

    stdout = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDOUT)
    assert stdout.data == HELLO_WORLD + SEPARATOR

    stderr = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDERR)
    cleaned_logs = stderr.data.replace('\x1b[34m', '').replace('\x1b[0m', '')
    assert 'dagster - DEBUG - spew_pipeline - ' in cleaned_logs

    bad_logs = manager.read_logs_file('not_a_run_id', step_key, ComputeIOType.STDOUT)
    assert bad_logs.data is None
    assert not manager.is_compute_completed('not_a_run_id', step_key)


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_stdout_subscriptions():
    instance = DagsterInstance.local_temp()
    step_key = 'spew.compute'
    result = execute_pipeline(spew_pipeline, instance=instance)
    stdout_observable = instance.compute_log_manager.observable(
        result.run_id, step_key, ComputeIOType.STDOUT
    )
    stderr_observable = instance.compute_log_manager.observable(
        result.run_id, step_key, ComputeIOType.STDERR
    )
    stdout = []
    stdout_observable.subscribe(stdout.append)
    stderr = []
    stderr_observable.subscribe(stderr.append)
    assert len(stdout) == 1
    assert stdout[0].data.startswith(HELLO_WORLD)
    assert stdout[0].cursor in [12, 13]
    assert len(stderr) == 1
    assert stderr[0].cursor == len(stderr[0].data)
    assert stderr[0].cursor > 400


def gen_solid_name(length):
    return ''.join(random.choice(string.ascii_lowercase) for x in range(length))


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_long_solid_names():
    solid_name = gen_solid_name(300)

    @pipeline
    def long_pipeline():
        spew.alias(name=solid_name)()

    instance = DagsterInstance.local_temp()
    manager = instance.compute_log_manager

    result = execute_pipeline(long_pipeline, instance=instance)
    assert result.success

    compute_steps = [
        event.step_key
        for event in result.step_event_list
        if event.event_type == DagsterEventType.STEP_START
    ]

    assert len(compute_steps) == 1
    step_key = compute_steps[0]
    assert manager.is_compute_completed(result.run_id, step_key)

    stdout = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDOUT)
    assert stdout.data == HELLO_WORLD + SEPARATOR
