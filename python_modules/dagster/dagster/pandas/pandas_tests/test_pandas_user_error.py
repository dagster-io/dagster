# pylint: disable=W0613

import pytest

import pandas as pd

import dagster.pandas as dagster_pd
from dagster import (
    DagsterInvariantViolationError,
    DagsterTypeError,
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    SolidDefinition,
    config,
    execute_pipeline,
    lambda_solid,
)
from dagster.core.utility_solids import define_stub_solid


def test_wrong_output_value():
    csv_input = InputDefinition('num_csv', dagster_pd.DataFrame)

    @lambda_solid(
        name="test_wrong_output",
        inputs=[csv_input],
        output=OutputDefinition(dagster_pd.DataFrame),
    )
    def df_solid(num_csv):
        return 'not a dataframe'

    pass_solid = define_stub_solid('pass_solid', pd.DataFrame())

    pipeline = PipelineDefinition(
        solids=[pass_solid, df_solid],
        dependencies={'test_wrong_output': {
            'num_csv': DependencyDefinition('pass_solid'),
        }}
    )

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(pipeline)


def test_wrong_input_value():
    @lambda_solid(
        name="test_wrong_input",
        inputs=[InputDefinition('foo', dagster_pd.DataFrame)],
    )
    def df_solid(foo):
        return foo

    pass_solid = define_stub_solid('pass_solid', 'not a dataframe')

    pipeline = PipelineDefinition(
        solids=[pass_solid, df_solid],
        dependencies={'test_wrong_input': {
            'foo': DependencyDefinition('pass_solid'),
        }}
    )

    with pytest.raises(DagsterTypeError):
        execute_pipeline(pipeline)
