from dagster import repository
from dagster.core.definitions.run_status_sensor_definition import pipeline_failure_sensor


def test_pipeline_failure_sensor_def():
    called = {}

    @pipeline_failure_sensor
    def call_on_pipeline_failure(context):
        called[context.pipeline_run.run_id] = True

    @repository
    def my_repo():
        return [call_on_pipeline_failure]

    assert my_repo.has_sensor_def("call_on_pipeline_failure")
