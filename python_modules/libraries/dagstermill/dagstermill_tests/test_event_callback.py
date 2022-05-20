import time
from collections import defaultdict

from dagster.core.definitions.reconstruct import ReconstructablePipeline
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventLogEntry
from dagster.core.execution.api import execute_run
from dagster.core.test_utils import instance_for_test


def test_event_callback_logging():
    events = defaultdict(list)

    def _event_callback(record, _cursor):
        assert isinstance(record, EventLogEntry)
        if record.is_dagster_event:
            events[record.dagster_event.event_type].append(record)

    pipeline = ReconstructablePipeline.for_module(
        "dagstermill.examples.repository",
        "hello_logging_pipeline",
    )
    pipeline_def = pipeline.get_definition()
    with instance_for_test() as instance:
        pipeline_run = instance.create_run_for_pipeline(pipeline_def)

        instance.watch_event_logs(pipeline_run.run_id, None, _event_callback)

        res = execute_run(
            pipeline,
            pipeline_run,
            instance,
        )

        assert res.success

        passed_before_timeout = False
        retries = 5
        while retries > 0:
            time.sleep(0.333)
            if DagsterEventType.PIPELINE_FAILURE in events.keys():
                break
            if DagsterEventType.PIPELINE_SUCCESS in events.keys():
                passed_before_timeout = True
                break
            retries -= 1

        assert passed_before_timeout
