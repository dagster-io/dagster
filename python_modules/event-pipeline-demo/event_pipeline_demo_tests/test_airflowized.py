import pytest

from dagster.utils import script_relative_path

# pylint: disable=unused-import
from dagster_airflow.test_fixtures import dagster_airflow_python_operator_pipeline

from event_pipeline_demo.pipelines import define_event_ingest_pipeline


@pytest.mark.skip
class TestAirflowizedEventPipeline(object):
    config_yaml = [script_relative_path('../environments/default.yml')]
    pipeline = define_event_ingest_pipeline()

    # pylint: disable=redefined-outer-name
    def test_airflowized_event_pipeline(self, dagster_airflow_python_operator_pipeline):
        pass
