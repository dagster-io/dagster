from dagster.utils import script_relative_path

from dagster_airflow.test_fixtures import dagster_airflow_python_operator_pipeline

from event_pipeline_demo.pipelines import define_event_ingest_pipeline


class TestAirflowizedEventPipeline(object):
    config_yaml = [script_relative_path('../environments/default.yml')]
    pipeline = define_event_ingest_pipeline()

    def test_airflowized_event_pipeline(dagster_airflow_python_operator_pipeline):
        pass
