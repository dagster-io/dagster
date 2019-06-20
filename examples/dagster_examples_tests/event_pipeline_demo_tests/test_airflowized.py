import pytest

from dagster import ExecutionTargetHandle
from dagster.utils import script_relative_path

# pylint: disable=unused-import
from dagster_airflow.test_fixtures import dagster_airflow_python_operator_pipeline

from dagster_examples.event_pipeline_demo.pipelines import event_ingest_pipeline


@pytest.mark.skip
class TestAirflowizedEventPipeline(object):
    config_yaml = [
        script_relative_path('../../dagster_examples/airline_demo/environments/default.yaml')
    ]

    pipeline_name = 'event_ingest_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module(
        'dagster_examples.event_pipeline_demo', pipeline_name
    )

    # pylint: disable=redefined-outer-name
    def test_airflowized_event_pipeline(self, dagster_airflow_python_operator_pipeline):
        pass
