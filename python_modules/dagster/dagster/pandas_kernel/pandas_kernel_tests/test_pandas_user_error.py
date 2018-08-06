# pylint: disable=W0613

import pytest

import dagster
import dagster.pandas_kernel as dagster_pd
from dagster import (config, InputDefinition, OutputDefinition, SolidDefinition)
from dagster.core.decorators import solid, source
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution import execute_single_solid
from dagster.utils.test import script_relative_path


def _dataframe_solid(name, inputs, transform_fn):
    return SolidDefinition(
        name=name,
        inputs=inputs,
        transform_fn=transform_fn,
        output=OutputDefinition(dagster_pd.DataFrame),
    )


def test_wrong_output_value():
    csv_input = InputDefinition('num_csv', dagster_pd.DataFrame)

    @solid(
        name="test_wrong_output", inputs=[csv_input], output=OutputDefinition(dagster_pd.DataFrame)
    )
    def df_solid(num_csv):
        return 'not a dataframe'

    with pytest.raises(DagsterInvariantViolationError):
        execute_single_solid(
            dagster.ExecutionContext(),
            df_solid,
            environment=config.Environment(
                sources={
                    'test_wrong_output': {
                        'num_csv': config.Source('CSV', {'path': script_relative_path('num.csv')})
                    },
                },
            ),
        )


def test_wrong_input_value():
    @source(name="WRONG")
    def wrong_source():
        return 'not a dataframe'

    @solid(
        name="test_wrong_input",
        inputs=[InputDefinition('foo', dagster_pd.DataFrame, sources=[wrong_source])],
        output=OutputDefinition(),
    )
    def df_solid(foo):
        return foo

    with pytest.raises(DagsterInvariantViolationError):
        execute_single_solid(
            dagster.ExecutionContext(),
            df_solid,
            environment=config.Environment(
                sources={'test_wrong_input': {
                    'foo': config.Source('WRONG', {})
                }}
            )
        )


def test_wrong_input_arg_dict():
    csv_input = InputDefinition('num_csv', dagster_pd.DataFrame)

    def transform_fn(context, args):
        return args['num_csv']

    df_solid = _dataframe_solid(
        name='test_wrong_value', inputs=[csv_input], transform_fn=transform_fn
    )

    with pytest.raises(DagsterInvariantViolationError):
        execute_single_solid(
            dagster.ExecutionContext(),
            df_solid,
            environment=config.Environment(
                sources={
                    'test_wrong_value': {
                        'num_jdkfjskdfjs':
                        config.Source('CSV', {'path': script_relative_path('num.csv')})
                    },
                },
            ),
        )
