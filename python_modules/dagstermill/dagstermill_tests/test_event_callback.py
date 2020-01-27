import time
from collections import defaultdict

from dagster import RunConfig, execute_pipeline
from dagster.cli.load_handle import handle_for_pipeline_cli_args
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventRecord
from dagster.core.instance import DagsterInstance


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
    run_config = RunConfig()
    instance = DagsterInstance.local_temp()

    instance.watch_event_logs(run_config.run_id, -1, _event_callback)

    execute_pipeline(handle.build_pipeline_definition(), run_config=run_config, instance=instance)

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
