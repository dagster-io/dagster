from collections import defaultdict

from dagster import execute_pipeline, RunConfig
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventRecord

from dagstermill.examples.repository import define_hello_logging_pipeline


def test_event_callback_logging():
    events = defaultdict(list)

    def _event_callback(record):
        assert isinstance(record, EventRecord)
        if record.is_dagster_event:
            events[record.dagster_event.event_type].append(record)

    execute_pipeline(
        define_hello_logging_pipeline(), run_config=RunConfig(event_callback=_event_callback)
    )

    assert DagsterEventType.PIPELINE_SUCCESS in events.keys()
