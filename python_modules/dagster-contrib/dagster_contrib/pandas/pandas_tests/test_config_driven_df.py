from dagster import (
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
