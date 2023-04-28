import time
from collections import defaultdict

from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.events import DagsterEventType
from dagster._core.events.log import EventLogEntry
from dagster._core.execution.api import execute_run
from dagster._core.test_utils import instance_for_test


def test_event_callback_logging():
    events = defaultdict(list)

    def _event_callback(record, _cursor):
        assert isinstance(record, EventLogEntry)
        if record.is_dagster_event:
            events[record.dagster_event.event_type].append(record)

    recon_job = ReconstructableJob.for_module(
        "dagstermill.examples.repository",
        "hello_logging_job",
    )
    job_def = recon_job.get_definition()
    with instance_for_test() as instance:
        dagster_run = instance.create_run_for_job(job_def)

        instance.watch_event_logs(dagster_run.run_id, None, _event_callback)

        res = execute_run(
            recon_job,
            dagster_run,
            instance,
        )

        assert res.success

        passed_before_timeout = False
        retries = 5
        while retries > 0:
            time.sleep(0.333)
            if DagsterEventType.RUN_FAILURE in events.keys():
                break
            if DagsterEventType.RUN_SUCCESS in events.keys():
                passed_before_timeout = True
                break
            retries -= 1

        assert passed_before_timeout
