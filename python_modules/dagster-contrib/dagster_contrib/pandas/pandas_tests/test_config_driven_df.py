from __future__ import unicode_literals

import pytest

import pandas as pd

from dagster import (
    DependencyDefinition,
    InputDefinition,
    PipelineConfigEvaluationError,
    PipelineDefinition,
    OutputDefinition,
    execute_pipeline,
    solid,
    types,
)

from dagster.utils import script_relative_path
from dagster.utils.test import get_temp_file_name

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


def test_dataframe_wrong_sep_from_inputs():
    called = {}

    @solid(inputs=[InputDefinition('df', DataFrame)])
    def df_as_config(_info, df):
        # this is the pandas behavior
        assert df.to_dict('list') == {'num1,num2': ['1,2', '3,4']}
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
                                'sep': '|'
                            },
                        },
                    },
                },
            },
        },
    )

    assert result.success
    assert called['yup']


def test_dataframe_pipe_sep_csv_from_inputs():
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
                                'path': script_relative_path('num_pipes.csv'),
                                'sep': '|'
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
    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(pipeline)

    assert 'Error 1: Missing required field "solids" at document config root' in str(exc_info.value)

    assert 'yup' not in called


def test_dataframe_csv_missing_input_collision():
    called = {}

    @solid(outputs=[OutputDefinition(DataFrame)])
    def df_as_output(_info):
        return pd.DataFrame()

    @solid(inputs=[InputDefinition('df', DataFrame)])
    def df_as_input(_info, df):  # pylint: disable=W0613
        called['yup'] = True

    pipeline = PipelineDefinition(
        name='overlapping',
        solids=[df_as_input, df_as_output],
        dependencies={
            'df_as_input': {
                'df': DependencyDefinition('df_as_output'),
            },
        },
    )
    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(
            pipeline,
            {
                'solids': {
                    'df_as_input': {
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

    assert 'Error 1: Undefined field "inputs" at path root:solids:df_as_input' in str(
        exc_info.value
    )

    assert 'yup' not in called


def test_dataframe_parquet_from_inputs():
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
                            'parquet': {
                                'path': script_relative_path('num.parquet'),
                            },
                        },
                    },
                },
            },
        },
    )

    assert result.success
    assert called['yup']


def test_dataframe_table_from_inputs():
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
                            'table': {
                                'path': script_relative_path('num_table.txt'),
                            },
                        },
                    },
                },
            },
        },
    )

    assert result.success
    assert called['yup']


def test_dataframe_csv_materialization():
    @solid(outputs=[OutputDefinition(DataFrame)])
    def return_df(_info):
        return pd.DataFrame({'num1': [1, 3], 'num2': [2, 4]})

    pipeline_def = PipelineDefinition(name='return_df_pipeline', solids=[return_df])

    with get_temp_file_name() as filename:
        result = execute_pipeline(
            pipeline_def,
            {
                'solids': {
                    'return_df': {
                        'outputs': [
                            {
                                'result': {
                                    'csv': {
                                        'path': filename,
                                    },
                                },
                            },
                        ],
                    },
                },
            },
        )

        assert result.success

        df = pd.read_csv(filename)
        assert df.to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
        }


def test_dataframe_parquet_materialization():
    @solid(outputs=[OutputDefinition(DataFrame)])
    def return_df(_info):
        return pd.DataFrame({'num1': [1, 3], 'num2': [2, 4]})

    pipeline_def = PipelineDefinition(name='return_df_pipeline', solids=[return_df])

    with get_temp_file_name() as filename:
        result = execute_pipeline(
            pipeline_def,
            {
                'solids': {
                    'return_df': {
                        'outputs': [
                            {
                                'result': {
                                    'parquet': {
                                        'path': filename,
                                    },
                                },
                            },
                        ],
                    },
                },
            },
        )

        assert result.success

        df = pd.read_parquet(filename)
        assert df.to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
        }


def test_dataframe_table_materialization():
    @solid(outputs=[OutputDefinition(DataFrame)])
    def return_df(_info):
        return pd.DataFrame({'num1': [1, 3], 'num2': [2, 4]})

    pipeline_def = PipelineDefinition(name='return_df_pipeline', solids=[return_df])

    with get_temp_file_name() as filename:
        filename = '/tmp/table_test.txt'
        result = execute_pipeline(
            pipeline_def,
            {
                'solids': {
                    'return_df': {
                        'outputs': [
                            {
                                'result': {
                                    'table': {
                                        'path': filename,
                                    },
                                },
                            },
                        ],
                    },
                },
            },
        )

        assert result.success

        df = pd.read_table(filename)
        assert df.to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
        }
