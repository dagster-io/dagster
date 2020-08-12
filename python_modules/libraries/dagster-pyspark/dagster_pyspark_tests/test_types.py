import shutil

import pytest
from dagster_pyspark import DataFrame as DagsterPySparkDataFrame
from dagster_pyspark import pyspark_resource
from pyspark.sql import Row, SparkSession

from dagster import (
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    execute_solid,
    file_relative_path,
    solid,
)
from dagster.utils.test import get_temp_dir

spark = SparkSession.builder.getOrCreate()


def create_pyspark_df():
    data = [Row(_c0=str(i), _c1=str(i)) for i in range(100)]
    return spark.createDataFrame(data)


@pytest.mark.parametrize(
    'file_type,read',
    [
        pytest.param('csv', spark.read.csv, id='csv'),
        pytest.param('parquet', spark.read.parquet, id='parquet'),
        pytest.param('json', spark.read.json, id='json'),
    ],
)
def test_dataframe_outputs(file_type, read):
    df = create_pyspark_df()

    @solid(output_defs=[OutputDefinition(dagster_type=DagsterPySparkDataFrame, name='df')])
    def return_df(_):
        return df

    with get_temp_dir() as temp_path:
        shutil.rmtree(temp_path)

        result = execute_solid(
            return_df,
            run_config={
                'solids': {'return_df': {'outputs': [{'df': {file_type: {'path': temp_path}}}]}}
            },
        )
        assert result.success
        actual = read(temp_path)
        assert sorted(df.collect()) == sorted(actual.collect())

        result = execute_solid(
            return_df,
            run_config={
                'solids': {
                    'return_df': {
                        'outputs': [
                            {
                                'df': {
                                    file_type: {
                                        'path': temp_path,
                                        'mode': 'overwrite',
                                        'compression': 'gzip',
                                    }
                                }
                            }
                        ]
                    }
                }
            },
        )
        assert result.success
        actual = read(temp_path)
        assert sorted(df.collect()) == sorted(actual.collect())


@pytest.mark.parametrize(
    'file_type,read',
    [
        pytest.param('csv', spark.read.csv, id='csv'),
        pytest.param('parquet', spark.read.parquet, id='parquet'),
        pytest.param('json', spark.read.json, id='json'),
    ],
)
def test_dataframe_inputs(file_type, read):
    @solid(input_defs=[InputDefinition(dagster_type=DagsterPySparkDataFrame, name='input_df')],)
    def return_df(_, input_df):
        return input_df

    file_name = file_relative_path(__file__, "num.{file_type}".format(file_type=file_type))
    result = execute_solid(
        return_df,
        mode_def=ModeDefinition(resource_defs={'pyspark': pyspark_resource}),
        run_config={
            'solids': {'return_df': {'inputs': {'input_df': {file_type: {'path': file_name}}}}}
        },
    )
    assert result.success
    assert sorted(result.output_value().collect()) == sorted(read(file_name).collect())
