from collections import defaultdict

from dagster import RunConfig, execute_pipeline
from dagster.cli.load_handle import handle_for_pipeline_cli_args
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventRecord
from dagster.core.events import CallbackEventSink


def test_event_callback_logging():
    events = defaultdict(list)

    def _event_callback(record):
        assert isinstance(record, EventRecord)
        if record.is_dagster_event:
            events[record.dagster_event.event_type].append(record)

    handle = handle_for_pipeline_cli_args(
        {
            'module_name': 'dagstermill.examples.repository',
            'fn_name': 'define_hello_logging_pipeline',
        }
    )

    execute_pipeline(
        handle.build_pipeline_definition(),
        run_config=RunConfig(event_sink=CallbackEventSink(_event_callback)),
    )

    assert DagsterEventType.PIPELINE_SUCCESS in events.keys()
