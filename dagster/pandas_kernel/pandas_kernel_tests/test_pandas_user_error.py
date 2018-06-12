# pylint: disable=W0613

import dagster
from dagster import config
from dagster.core.execution import (execute_single_solid, create_single_solid_env_from_arg_dicts)
import dagster.pandas_kernel as dagster_pd

from dagster.utils.test import script_relative_path

import pytest

from dagster.core.errors import DagsterInvariantViolationError, DagsterInvalidDefinitionError

from .utils import simple_csv_input


def test_wrong_definitions():
    def transform_varargs(num_csv, foo, *args):
        pass

    def transform_extra_argument(num_csv, foo, bar):
        pass

    def transform_missing(num_csv):
        pass

    def transform_missing_with_context(context, num_csv):
        pass

    def transform_with_context(context, num_csv, foo):
        pass

    def transform_missing_but_kwargs(num_csv, **kwargs):
        pass

    def make_solid(transform):
        input_1 = simple_csv_input('num_csv')
        input_2 = simple_csv_input('foo')

        return dagster_pd.dataframe_solid(
            name='test_transform_validation', inputs=[input_1, input_2], transform_fn=transform
        )

    with pytest.raises(DagsterInvalidDefinitionError):
        make_solid(transform_varargs)

    with pytest.raises(DagsterInvalidDefinitionError):
        make_solid(transform_extra_argument)

    with pytest.raises(DagsterInvalidDefinitionError):
        make_solid(transform_missing)

    with pytest.raises(DagsterInvalidDefinitionError):
        make_solid(transform_missing_with_context)

    make_solid(transform_with_context)
    make_solid(transform_missing_but_kwargs)


def test_wrong_value():
    csv_input = simple_csv_input('num_csv')

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
            environment=create_single_solid_env_from_arg_dicts(df_solid, input_arg_dicts),
        )


def test_wrong_input_arg_dict():
    csv_input = simple_csv_input('num_csv')

    def transform_fn(num_csv):
        return num_csv

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
