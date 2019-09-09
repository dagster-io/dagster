import pandas as pd

from dagster import execute_pipeline
from dagster.cli.load_handle import handle_for_pipeline_cli_args
from dagster.core.instance import DagsterInstance
from dagster.utils import script_relative_path


def test_papermill_pandas_hello_world_pipeline():
    handle = handle_for_pipeline_cli_args(
        {
            'module_name': 'dagster_pandas.examples',
            'fn_name': 'papermill_pandas_hello_world_pipeline',
        }
    )

    pipeline = handle.build_pipeline_definition()
    pipeline_result = execute_pipeline(
        pipeline,
        {
            'solids': {
                'papermill_pandas_hello_world': {
                    'inputs': {'df': {'csv': {'path': script_relative_path('num_prod.csv')}}}
                }
            }
        },
        instance=DagsterInstance.local_temp(),
    )
    assert pipeline_result.success
    solid_result = pipeline_result.result_for_solid('papermill_pandas_hello_world')
    expected = pd.read_csv(script_relative_path('num_prod.csv')) + 1
    assert solid_result.output_value().equals(expected)
