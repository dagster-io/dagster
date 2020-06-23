import shutil

import pytest
from dagster_pyspark import DataFrame as DagsterPySparkDataFrame
from pyspark.sql import Row, SparkSession

from dagster import OutputDefinition, execute_solid, solid
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
