import os
import sys

from dagster import DagsterEventType, execute_pipeline, lambda_solid, pipeline
from dagster.core.instance import DagsterInstance


@lambda_solid
def spew():
    print(HELLO_WORLD)
    return


@pipeline
def spew_pipeline():
    spew()


HELLO_WORLD = 'Hello World'
SEPARATOR = os.linesep if (os.name == 'nt' and sys.version_info < (3,)) else '\n'


def test_stdout():
    instance = DagsterInstance.local_temp()
    result = execute_pipeline(spew_pipeline, instance=instance)
    assert result.success
    compute_steps = [
        event.step_key
        for event in result.step_event_list
        if event.event_type == DagsterEventType.STEP_START
    ]
    assert len(compute_steps) == 1
    step_key = compute_steps[0]
    logs = instance.compute_log_manager.read_logs(result.run_id, step_key)
    assert logs.stdout.data == HELLO_WORLD + SEPARATOR

    cleaned_logs = logs.stderr.data.replace('\x1b[34m', '').replace('\x1b[0m', '')

    assert 'dagster - DEBUG - spew_pipeline - ' in cleaned_logs
    logs = instance.compute_log_manager.read_logs(result.run_id, step_key, cursor='0:0')
    assert logs.stdout.data == HELLO_WORLD + SEPARATOR
    assert 'dagster - DEBUG - spew_pipeline - ' in cleaned_logs
    assert instance.compute_log_manager.is_compute_completed(result.run_id, step_key)

    bad_logs = instance.compute_log_manager.read_logs('not_a_run_id', step_key)
    assert bad_logs.stdout.data is None
    assert bad_logs.stderr.data is None
    assert not instance.compute_log_manager.is_compute_completed('not_a_run_id', step_key)


def test_stdout_subscriptions():
    instance = DagsterInstance.local_temp()
    step_key = 'spew.compute'
    result = execute_pipeline(spew_pipeline, instance=instance)
    observable = instance.compute_log_manager.observable(result.run_id, step_key)
    logs = []
    observable.subscribe(logs.append)
    assert len(logs) == 1
    stdout_cursor, stderr_cursor = map(int, logs[0].cursor.split(':'))
    assert stdout_cursor == len(logs[0].stdout.data)
    assert stdout_cursor in [12, 13]
    assert stderr_cursor == len(logs[0].stderr.data)
    assert stderr_cursor > 400
