# pylint: disable=W0613

import pytest

import pandas as pd

import dagster
import dagster.pandas_kernel as dagster_pd
from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    SolidDefinition,
    config,
    execute_pipeline,
    solid,
)
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution import execute_single_solid
from dagster.utils.test import script_relative_path
from dagster.core.utility_solids import define_pass_mem_value


def _dataframe_solid(name, inputs, transform_fn):
    return SolidDefinition.single_output_transform(
        name=name,
        inputs=inputs,
        transform_fn=transform_fn,
        output=OutputDefinition(dagster_type=dagster_pd.DataFrame),
    )


def test_wrong_output_value():
    csv_input = InputDefinition('num_csv', dagster_pd.DataFrame)

    @solid(
        name="test_wrong_output",
        inputs=[csv_input],
        output=OutputDefinition(dagster_type=dagster_pd.DataFrame)
    )
    def df_solid(num_csv):
        return 'not a dataframe'

    pass_solid = define_pass_mem_value('pass_solid', pd.DataFrame())

    pipeline = PipelineDefinition(
        solids=[pass_solid, df_solid],
        dependencies={'test_wrong_output': {
            'num_csv': DependencyDefinition('pass_solid'),
        }}
    )

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(
            pipeline,
            environment=config.Environment(),
        )


def test_wrong_input_value():
    @solid(
        name="test_wrong_input",
        inputs=[InputDefinition('foo', dagster_pd.DataFrame)],
        output=OutputDefinition(),
    )
    def df_solid(foo):
        return foo

    pass_solid = define_pass_mem_value('pass_solid', 'not a dataframe')

    pipeline = PipelineDefinition(
        solids=[pass_solid, df_solid],
        dependencies={'test_wrong_input': {
            'foo': DependencyDefinition('pass_solid'),
        }}
    )

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(
            pipeline,
            environment=config.Environment(),
        )
