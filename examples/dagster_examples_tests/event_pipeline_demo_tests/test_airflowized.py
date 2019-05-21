import pytest

from dagster import ExecutionTargetHandle
from dagster.utils import script_relative_path

# pylint: disable=unused-import
from dagster_airflow.test_fixtures import dagster_airflow_python_operator_pipeline

from dagster_examples.event_pipeline_demo.pipelines import define_event_ingest_pipeline


@pytest.mark.skip
class TestAirflowizedEventPipeline(object):
    config_yaml = [
        script_relative_path('../../dagster_examples/airline_demo/environments/default.yml')
    ]
    handle = ExecutionTargetHandle.for_pipeline_fn(define_event_ingest_pipeline)
    pipeline_name = 'event_ingest_pipeline'

    # pylint: disable=redefined-outer-name
    def test_airflowized_event_pipeline(self, dagster_airflow_python_operator_pipeline):
        pass
