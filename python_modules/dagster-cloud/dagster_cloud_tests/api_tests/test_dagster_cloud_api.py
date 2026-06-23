from dagster_cloud.api.dagster_cloud_api import DagsterCloudApiThreadTelemetry


def test_thread_telemetry():
    thread_telemetry = DagsterCloudApiThreadTelemetry(
        submitted_to_executor_timestamp=0.0,
        thread_start_run_timestamp=0.5,
        thread_end_handle_api_request_timestamp=3.0,
    )

    assert thread_telemetry.time_to_thread_initialization_seconds == 0.5
    assert thread_telemetry.time_to_handle_api_request_seconds == 2.5
