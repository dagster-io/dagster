import dagster as dg
from dagster._core.events import MARKER_EVENTS


def define_job() -> dg.JobDefinition:
    @dg.op
    def ping():
        return "ping"

    @dg.job
    def simple():
        ping()

    return simple


def test_multiproc_markers():
    with dg.instance_for_test() as instance:
        with dg.execute_job(
            dg.reconstructable(define_job),
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
                        key = f"{event.step_key}.{dagster_event.engine_event_data.marker_start}"
                        start_markers[key] = event.timestamp
                    if dagster_event.engine_event_data.marker_end:
                        key = f"{event.step_key}.{dagster_event.engine_event_data.marker_end}"
                        end_markers[key] = event.timestamp

            seen = set()
            assert set(start_markers.keys()) == set(end_markers.keys())
            for key in end_markers:
                assert end_markers[key] - start_markers[key] > 0
                seen.add(key)

            assert "ping.step_process_start" in end_markers
