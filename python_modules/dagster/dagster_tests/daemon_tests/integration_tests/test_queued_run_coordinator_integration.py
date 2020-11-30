import contextlib
import os
import subprocess

from dagster.core.instance import DagsterInstance
from dagster.core.test_utils import create_run_for_test, poll_for_finished_run
from dagster.utils import merge_dicts
from dagster.utils.external import external_pipeline_from_run


def setup_instance(dagster_home):
    os.environ["DAGSTER_HOME"] = dagster_home
    config = """run_coordinator:
    module: dagster.core.run_coordinator
    class: QueuedRunCoordinator
    config:
        dequeue_interval_seconds: 1
    """
    with open(os.path.join(dagster_home, "dagster.yaml"), "w") as file:
        file.write(config)


@contextlib.contextmanager
def start_daemon():
    p = subprocess.Popen(["dagster-daemon", "run"])
    yield
    p.kill()


def create_run(instance, pipeline_handle, **kwargs):  # pylint: disable=redefined-outer-name
    pipeline_args = merge_dicts(
        {
            "pipeline_name": "foo_pipeline",
            "external_pipeline_origin": pipeline_handle.get_external_origin(),
        },
        kwargs,
    )
    return create_run_for_test(instance, **pipeline_args)


def assert_events_in_order(logs, expected_events):

    logged_events = [log.dagster_event.event_type_value for log in logs]
    filtered_logged_events = [event for event in logged_events if event in expected_events]

    assert filtered_logged_events == expected_events


def test_queued_runs(tmpdir, foo_pipeline_handle):
    dagster_home_path = tmpdir.strpath
    setup_instance(dagster_home_path)
    with DagsterInstance.get() as instance:
        with start_daemon():

            run = create_run(instance, foo_pipeline_handle)
            with external_pipeline_from_run(run) as external_pipeline:
                instance.submit_run(run.run_id, external_pipeline)

            poll_for_finished_run(instance, run.run_id)

            logs = instance.all_logs(run.run_id)
            assert_events_in_order(
                logs, ["PIPELINE_ENQUEUED", "PIPELINE_DEQUEUED", "PIPELINE_SUCCESS"],
            )
