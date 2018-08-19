import pytest

import pandas as pd

import dagster
import dagster.pandas_kernel as dagster_pd
import dagster_ge
from dagster import (InputDefinition, OutputDefinition)
from dagster.core.decorators import solid
from dagster.core.errors import DagsterExecutionFailureReason
from dagster.utils.test import script_relative_path


def _sum_solid_impl(num_df):
    sum_df = num_df
    sum_df['sum'] = sum_df['num1'] + sum_df['num2']
    return sum_df


def col_exists(name, col_name):
    return dagster_ge.ge_expectation(name, lambda ge_df: ge_df.expect_column_to_exist(col_name))


@solid(
    inputs=[
        InputDefinition(
            'num_df', dagster_pd.DataFrame, expectations=[col_exists('num1_exists', 'num1')]
        )
    ],
    output=OutputDefinition(dagster_type=dagster_pd.DataFrame)
)
def sum_solid(num_df):
    return _sum_solid_impl(num_df)


@solid(
    inputs=[
        InputDefinition(
            'num_df',
            dagster_pd.DataFrame,
            expectations=[col_exists('failing', 'not_a_column')],
        )
    ],
    output=OutputDefinition(dagster_type=dagster_pd.DataFrame)
)
def sum_solid_fails_input_expectation(num_df):
    return _sum_solid_impl(num_df)


@solid(
    inputs=[
        InputDefinition(
            'num_df',
            dagster_pd.DataFrame,
            expectations=[
                dagster_ge.json_config_expectation(
                    'num_expectations', script_relative_path('num_expectations.json')
                )
            ],
        ),
    ],
    output=OutputDefinition(dagster_type=dagster_pd.DataFrame)
)
def sum_solid_expectations_config(num_df):
    return _sum_solid_impl(num_df)


def test_single_node_passing_expectation():
    in_df = pd.DataFrame.from_dict({'num1': [1, 3], 'num2': [2, 4]})
    pipeline = dagster.PipelineDefinition(solids=[sum_solid])

    return
    # result = execute_pipeline_in_memory(
    #     dagster.ExecutionContext(),
    #     pipeline,
    #     input_values={sum_solid.name: {
    #         'num_df': in_df
    #     }},
    # )
    # assert result.success
    # assert result.result_list[0].success
    # assert result.result_list[0].transformed_value.to_dict('list') == {
    #     'num1': [1, 3],
    #     'num2': [2, 4],
    #     'sum': [3, 7],
    # }


def test_single_node_passing_json_config_expectations():
    in_df = pd.DataFrame.from_dict({'num1': [1, 3], 'num2': [2, 4]})
    pipeline = dagster.PipelineDefinition(solids=[sum_solid_expectations_config])

    return
    # result = execute_pipeline_in_memory(
    #     dagster.ExecutionContext(),
    #     pipeline,
    #     input_values={sum_solid_expectations_config.name: {
    #         'num_df': in_df
    #     }},
    # )
    # assert result.success
    # assert result.result_list[0].success
    # assert result.result_list[0].transformed_value.to_dict('list') == {
    #     'num1': [1, 3],
    #     'num2': [2, 4],
    #     'sum': [3, 7],
    # }


def test_single_node_failing_expectation():
    in_df = pd.DataFrame.from_dict({'num1': [1, 3], 'num2': [2, 4]})
    pipeline = dagster.PipelineDefinition(solids=[sum_solid_fails_input_expectation])
    return
    # result = execute_pipeline_in_memory(
    #     dagster.ExecutionContext(),
    #     pipeline,
    #     input_values={sum_solid_fails_input_expectation.name: {
    #         'num_df': in_df
    #     }},
    #     throw_on_error=False
    # )
    # assert not result.success

    # return
    # TODO redo expectation result API
    # assert len(result.result_list) == 1
    # first_solid_result = result.result_list[0]
    # assert not first_solid_result.success
    # assert first_solid_result.reason == DagsterExecutionFailureReason.EXPECTATION_FAILURE
    # assert isinstance(first_solid_result.input_expectation_results, dagster.InputExpectationResults)
    # input_expt_results = first_solid_result.input_expectation_results
    # assert len(input_expt_results.result_dict) == 1
    # input_expt_result = list(input_expt_results.result_dict.values())[0]
    # assert isinstance(input_expt_result, dagster.InputExpectationResult)
    # assert len(list(input_expt_result.passes)) == 0
    # assert len(list(input_expt_result.fails)) == 1
