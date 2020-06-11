# pylint: disable=redefined-outer-name
import os

import pytest
from dagster_examples.airline_demo.pipelines import (  # pylint: disable=unused-import
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)

from dagster import reconstructable
from dagster.utils import script_relative_path

try:
    # pylint: disable=unused-import
    from dagster_airflow.test_fixtures import dagster_airflow_python_operator_pipeline
except ImportError:
    pass


@pytest.mark.slow
@pytest.mark.airflow
class TestAirflowPython_0IngestExecution(object):
    recon_repo = reconstructable(define_airline_demo_ingest_pipeline)
    pipeline_name = 'airline_demo_ingest_pipeline'
    environment_yaml = [
        script_relative_path(
            os.path.join(
                '..', '..', 'dagster_examples', 'airline_demo', 'environments', 'local_base.yaml'
            )
        ),
        script_relative_path(
            os.path.join(
                '..', '..', 'dagster_examples', 'airline_demo', 'environments', 's3_storage.yaml'
            )
        ),
        script_relative_path(
            os.path.join(
                '..',
                '..',
                'dagster_examples',
                'airline_demo',
                'environments',
                'local_fast_ingest.yaml',
            )
        ),
    ]
    mode = 'local'

    def test_airflow_run_ingest_pipeline(self, dagster_airflow_python_operator_pipeline):
        pass


@pytest.mark.slow
@pytest.mark.airflow
class TestAirflowPython_1WarehouseExecution(object):
    recon_repo = reconstructable(define_airline_demo_warehouse_pipeline)
    pipeline_name = 'airline_demo_warehouse_pipeline'
    environment_yaml = [
        script_relative_path(
            os.path.join(
                '..', '..', 'dagster_examples', 'airline_demo', 'environments', 'local_base.yaml'
            )
        ),
        script_relative_path(
            os.path.join(
                '..', '..', 'dagster_examples', 'airline_demo', 'environments', 's3_storage.yaml'
            )
        ),
        script_relative_path(
            os.path.join(
                '..',
                '..',
                'dagster_examples',
                'airline_demo',
                'environments',
                'local_warehouse.yaml',
            )
        ),
    ]
    mode = 'local'

    def test_airflow_run_warehouse_pipeline(self, dagster_airflow_python_operator_pipeline):
        pass
