import dagster
from dagster.core.execution import execute_single_solid
import dagster.pandas_kernel as dagster_pd

from dagster.utils.test import script_relative_path


def test_wrong_value():
    csv_input = dagster_pd.csv_input('num_csv')

    def transform_fn(num_csv):
        return 'not a dataframe'

    # supports CSV and PARQUET by default
    df_solid = dagster_pd.dataframe_solid(
        name='test_wrong_value', inputs=[csv_input], transform_fn=transform_fn
    )

    input_arg_dicts = {'num_csv': {'path': script_relative_path('num.csv')}}

    execute_single_solid(
        dagster.context(),
        df_solid,
        input_arg_dicts,
    )
