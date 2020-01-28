import os

from dagster_pyspark import pyspark_resource, spark_session_from_config
from lakehouse import Lakehouse, construct_lakehouse_pipeline, input_table, pyspark_table
from lakehouse.util import invoke_compute
from pyspark.sql import DataFrame as SparkDF
from pyspark.sql import Row

from dagster import Materialization, check, execute_pipeline
from dagster.utils.temp_file import get_temp_dir

FEATURE_AREA = 'feature_area'


def this_pyspark_table(feature_area, name=None, input_tables=None):
    def _wrap(fn):
        return pyspark_table(
            name=name, tags={FEATURE_AREA: feature_area}, input_tables=input_tables
        )(fn)

    return _wrap


FEATURE_ONE = 'feature_one'
FEATURE_TWO = 'feature_two'


@this_pyspark_table(feature_area=FEATURE_ONE)
def TableOne(context) -> SparkDF:
    return context.resources.spark.spark_session.createDataFrame([Row(num=1)])


@this_pyspark_table(feature_area=FEATURE_ONE)
def TableTwo(context) -> SparkDF:
    return context.resources.spark.spark_session.createDataFrame([Row(num=2)])


@this_pyspark_table(
    input_tables=[input_table('table_one', TableOne), input_table('table_two', TableTwo)],
    feature_area=FEATURE_TWO,
)
def TableThree(_, table_one: SparkDF, table_two: SparkDF) -> SparkDF:
    return table_one.union(table_two)


class ByFeatureParquetLakehouse(Lakehouse):
    def __init__(self, root_dir):
        self.lakehouse_path = check.str_param(root_dir, 'root_dir')

    def _path_for_table(self, table_type, table_metadata):
        return os.path.join(self.lakehouse_path, table_metadata[FEATURE_AREA], table_type.name)

    def hydrate(self, context, table_type, table_metadata, _table_handle, _dest_metadata):
        path = self._path_for_table(table_type, table_metadata)
        return context.resources.spark.spark_session.read.parquet(path)

    def materialize(self, _context, table_type, table_metadata, value):
        path = self._path_for_table(table_type, table_metadata)
        value.write.parquet(path=path, mode='overwrite')
        return Materialization.file(path), None


def test_execute_byfeature_parquet_lakehouse():
    with get_temp_dir() as temp_dir:
        lakehouse = ByFeatureParquetLakehouse(temp_dir)
        pipeline_def = construct_lakehouse_pipeline(
            name='test',
            lakehouse_tables=[TableOne, TableTwo, TableThree],
            resources={'spark': pyspark_resource, 'lakehouse': lakehouse},
        )

        pipeline_result = execute_pipeline(pipeline_def)
        assert pipeline_result.success

        def get_table(table_def):
            spark = spark_session_from_config()
            return spark.read.parquet(
                os.path.join(temp_dir, table_def.tags[FEATURE_AREA], table_def.name)
            ).collect()

        assert get_table(TableOne) == [Row(num=1)]
        assert get_table(TableTwo) == [Row(num=2)]
        assert set(get_table(TableThree)) == set([Row(num=1), Row(num=2)])


def test_smoke_test_table_three():
    spark = spark_session_from_config()

    result = invoke_compute(
        TableThree,
        inputs={
            'table_one': spark.createDataFrame([Row(num=1)]),
            'table_two': spark.createDataFrame([Row(num=2)]),
        },
    )

    assert result.success
    assert set(result.output_value().collect()) == set([Row(num=1), Row(num=2)])
