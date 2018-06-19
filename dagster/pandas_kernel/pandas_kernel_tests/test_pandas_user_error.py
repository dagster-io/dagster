# pylint: disable=W0613

import dagster
from dagster import config
from dagster.core.execution import (execute_single_solid, create_single_solid_env_from_arg_dicts)
import dagster.pandas_kernel as dagster_pd

from dagster.utils.test import script_relative_path

import pytest

from dagster.core.errors import DagsterInvariantViolationError, DagsterInvalidDefinitionError, DagsterExpectationFailedError

from .utils import simple_csv_input


def test_wrong_value():
    csv_input = simple_csv_input('num_csv')

    def transform_fn(context, args):
        return 'not a dataframe'

    df_solid = dagster_pd.dataframe_solid(
        name='test_wrong_value', inputs=[csv_input], transform_fn=transform_fn
    )

    input_arg_dicts = {'num_csv': {'path': script_relative_path('num.csv')}}

    with pytest.raises(DagsterExpectationFailedError):
        execute_single_solid(
            dagster.context(),
            df_solid,
            environment=create_single_solid_env_from_arg_dicts(df_solid, input_arg_dicts),
        )


def test_wrong_input_arg_dict():
    csv_input = simple_csv_input('num_csv')

    def transform_fn(context, args):
        return args['num_csv']

    df_solid = dagster_pd.dataframe_solid(
        name='test_wrong_value', inputs=[csv_input], transform_fn=transform_fn
    )

    with pytest.raises(DagsterInvariantViolationError):
        execute_single_solid(
            dagster.context(),
            df_solid,
            environment=config.Environment(
                input_sources=[
                    config.Input(
                        input_name='num_jdkfjskdfjs',
                        source='CSV',
                        args={
                            'path': script_relative_path('num.csv'),
                        }
                    )
                ]
            ),
        )
