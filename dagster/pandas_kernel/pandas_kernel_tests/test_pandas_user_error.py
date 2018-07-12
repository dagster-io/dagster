# pylint: disable=W0613

import pytest

import dagster
import dagster.pandas_kernel as dagster_pd
from dagster import config
from dagster.core.decorators import solid, source
from dagster.core.definitions import InputDefinition
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution import execute_single_solid
from dagster.utils.test import script_relative_path

from .utils import simple_csv_input


def test_wrong_output_value():
    csv_input = simple_csv_input('num_csv')

    @solid(name="test_wrong_output", inputs=[csv_input], output=dagster_pd.dataframe_output())
    def df_solid(num_csv):
        return 'not a dataframe'

    with pytest.raises(DagsterInvariantViolationError):
        execute_single_solid(
            dagster.context(),
            df_solid,
            environment=config.Environment(
                sources={
                    'num_csv': config.Source('CSV', {'path': script_relative_path('num.csv')})
                }
            )
        )


def test_wrong_input_value():
    @source(name="WRONG")
    def wrong_source():
        return 'not a dataframe'

    input_ = InputDefinition(name="foo", sources=[wrong_source])

    @solid(name="test_wrong_input", inputs=[input_], output=dagster_pd.dataframe_output())
    def df_solid(foo):
        return foo

    with pytest.raises(DagsterInvariantViolationError):
        execute_single_solid(
            dagster.context(),
            df_solid,
            environment=config.Environment(sources={'foo': config.Source('WRONG', {})})
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
                sources={
                    'num_jdkfjskdfjs': config.Source(
                        'CSV',
                        {'path': script_relative_path('num.csv')}
                    )
                }
            ),
        )
