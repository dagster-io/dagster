import pytest

from dagster import (
    DagsterInvariantViolationError,
    InputDefinition,
    PipelineDefinition,
    execute_pipeline,
    solid,
    types,
)

from dagster.utils import script_relative_path

from dagster_contrib.pandas import DataFrame


def test_dataframe():
    assert DataFrame.name == 'PandasDataFrame'


def test_dataframe_csv_from_config():
    called = {}

    @solid(config_field=types.Field(DataFrame))
    def df_as_config(info):
        assert info.config.to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
        }
        called['yup'] = True

    pipeline = PipelineDefinition(solids=[df_as_config])

    result = execute_pipeline(
        pipeline,
        {
            'solids': {
                'df_as_config': {
                    'config': {
                        'csv': {
                            'path': script_relative_path('num.csv'),
                        },
                    },
                },
            },
        },
    )

    assert result.success
    assert called['yup']


def test_dataframe_csv_from_inputs():
    called = {}

    @solid(inputs=[InputDefinition('df', DataFrame)])
    def df_as_config(_info, df):
        assert df.to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
        }
        called['yup'] = True

    pipeline = PipelineDefinition(solids=[df_as_config])

    result = execute_pipeline(
        pipeline,
        {
            'solids': {
                'df_as_config': {
                    'inputs': {
                        'df': {
                            'csv': {
                                'path': script_relative_path('num.csv'),
                            },
                        },
                    },
                },
            },
        },
    )

    assert result.success
    assert called['yup']


def test_dataframe_csv_missing_inputs():
    called = {}

    @solid(inputs=[InputDefinition('df', DataFrame)])
    def df_as_input(_info, df):  # pylint: disable=W0613
        called['yup'] = True

    pipeline = PipelineDefinition(name='missing_inputs', solids=[df_as_input])
    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        execute_pipeline(pipeline)

    'In pipeline missing_inputs solid df_as_input, input df' in str(exc_info.value)

    assert 'yup' not in called
