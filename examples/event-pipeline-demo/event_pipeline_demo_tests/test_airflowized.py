import pytest

from dagster import RepositoryTargetInfo
from dagster.utils import script_relative_path

# pylint: disable=unused-import
from dagster_airflow.test_fixtures import dagster_airflow_python_operator_pipeline

from event_pipeline_demo.pipelines import define_event_ingest_pipeline


@pytest.mark.skip
class TestAirflowizedEventPipeline(object):
    config_yaml = [script_relative_path('../environments/default.yml')]
    repository_target_info = RepositoryTargetInfo(
        python_file=__file__, fn_name='define_event_ingest_pipeline'
    )
    pipeline_name = 'event_ingest_pipeline'

    # pylint: disable=redefined-outer-name
    def test_airflowized_event_pipeline(self, dagster_airflow_python_operator_pipeline):
        pass
