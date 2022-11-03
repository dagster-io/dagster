from dagster import job, op, reconstructable
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.events import MARKER_EVENTS
from dagster._core.execution.api import execute_job
from dagster._core.test_utils import instance_for_test


def define_job() -> JobDefinition:
    @op
    def ping():
        return "ping"

    @job
    def simple():
        ping()

    return simple


def test_multiproc_markers():
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(define_job),
            instance=instance,
        ) as result:
            assert result.success
            events = instance.all_logs(result.run_id)
            start_markers = {}
            end_markers = {}
            for event in events:
                dagster_event = event.dagster_event
                if dagster_event and dagster_event.event_type in MARKER_EVENTS:
                    if dagster_event.engine_event_data.marker_start:
                        key = "{step}.{marker}".format(
                            step=event.step_key,
                            marker=dagster_event.engine_event_data.marker_start,
                        )
                        start_markers[key] = event.timestamp
                    if dagster_event.engine_event_data.marker_end:
                        key = "{step}.{marker}".format(
                            step=event.step_key,
                            marker=dagster_event.engine_event_data.marker_end,
                        )
                        end_markers[key] = event.timestamp

            seen = set()
            assert set(start_markers.keys()) == set(end_markers.keys())
            for key in end_markers:
                assert end_markers[key] - start_markers[key] > 0
                seen.add(key)

            assert "ping.step_process_start" in end_markers
