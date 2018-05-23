import dagster
from dagster.core.execution import execute_single_solid
import dagster.pandas_kernel as dagster_pd

from dagster.utils.test import script_relative_path

import pytest

from dagster.core.errors import DagsterInvariantViolationError


def test_wrong_value():
    csv_input = dagster_pd.csv_input('num_csv')

    def transform_fn(num_csv):
        return 'not a dataframe'

    df_solid = dagster_pd.dataframe_solid(
        name='test_wrong_value', inputs=[csv_input], transform_fn=transform_fn
    )

    input_arg_dicts = {'num_csv': {'path': script_relative_path('num.csv')}}

    with pytest.raises(DagsterInvariantViolationError):
        execute_single_solid(
            dagster.context(),
            df_solid,
            input_arg_dicts,
        )


def test_wrong_input_arg_dict():
    csv_input = dagster_pd.csv_input('num_csv')

    def transform_fn(num_csv):
        return num_csv

    df_solid = dagster_pd.dataframe_solid(
        name='test_wrong_value', inputs=[csv_input], transform_fn=transform_fn
    )

    input_arg_dicts = {'num_csvdlddjd': {'path': script_relative_path('num.csv')}}

    with pytest.raises(DagsterInvariantViolationError):
        execute_single_solid(
            dagster.context(),
            df_solid,
            input_arg_dicts,
        )
