import os

from dagster import DagsterEventType, execute_pipeline, lambda_solid, pipeline
from dagster.core.execution.logs import fetch_compute_logs
from dagster.core.instance import DagsterInstance
from dagster.seven import mock


@lambda_solid
def spew():
    print(HELLO_WORLD)
    return


@pipeline
def spew_pipeline():
    spew()


HELLO_WORLD = 'Hello World'
SEPARATOR = "\n"


def test_stdout(tmpdir):
    with mock.patch.dict(os.environ, {'DAGSTER_HOME': str(tmpdir)}), mock.patch(
        'dagster.core.execution.logs.should_capture_stdout'
    ) as f:
        f.return_value = True
        instance = DagsterInstance.ephemeral()
        result = execute_pipeline(spew_pipeline, instance=instance)
        assert result.success
        compute_steps = [
            event.step_key
            for event in result.step_event_list
            if event.event_type == DagsterEventType.STEP_START
        ]
        assert len(compute_steps) == 1
        step_key = compute_steps[0]
        logs = fetch_compute_logs(instance, result.run_id, step_key)
        assert logs.stdout == HELLO_WORLD + SEPARATOR
