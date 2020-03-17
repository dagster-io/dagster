import logging
import os

# pylint: disable=unused-import
from dagster_airflow.test_fixtures import dagster_airflow_custom_operator_pipeline
from dagster_airflow_tests.test_factory.utils import validate_pipeline_execution
from dagster_examples.dagster_airflow.custom_operator import CustomOperator

from dagster import ExecutionTargetHandle


def test_my_custom_operator(
    dagster_airflow_custom_operator_pipeline, environments_path, caplog,
):  # pylint: disable=redefined-outer-name
    caplog.set_level(logging.INFO, logger='CustomOperatorLogger')
    pipeline_name = 'demo_pipeline'
    operator = CustomOperator
    results = dagster_airflow_custom_operator_pipeline(
        pipeline_name=pipeline_name,
        handle=ExecutionTargetHandle.for_pipeline_module('test_pipelines.repo', pipeline_name),
        operator=operator,
        environment_yaml=[
            os.path.join(environments_path, 'env.yaml'),
            os.path.join(environments_path, 'env_filesystem_no_explicit_base_dir.yaml'),
        ],
    )
    validate_pipeline_execution(results)

    log_lines = 0
    for record in caplog.records:
        if record.name == 'CustomOperatorLogger':
            log_lines += 1
            assert record.message == 'CustomOperator is called'

    assert log_lines == 2
