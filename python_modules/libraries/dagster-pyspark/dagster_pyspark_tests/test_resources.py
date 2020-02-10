from dagster_pyspark import pyspark_resource
from pyspark.sql import DataFrame, Row

from dagster import ModeDefinition, execute_solid, solid


@solid(required_resource_keys={'spark'})
def simple_solid(context):
    spark = context.resources.spark.spark_session
    data = [("1", "2")]
    df = spark.createDataFrame(data, ["col1", "col2"])
    return df


def test_leave_spark_session_alive():
    res = execute_solid(
        simple_solid,
        mode_def=ModeDefinition(resource_defs={'spark': pyspark_resource}),
        environment_dict={'resources': {'spark': {'config': {'stop_session': False}}}},
    )

    df = res.output_value()
    assert isinstance(df, DataFrame)
    assert df.collect() == [Row(col1='1', col2='2')]
