# getting false positives in vscode
from pyspark.sql import SparkSession  # pylint: disable=no-name-in-module,import-error
from pyspark.rdd import RDD  # pylint: disable=no-name-in-module,import-error

from dagster import resource, Field, Dict, as_dagster_type
from dagster.core.types.runtime import define_any_type

from dagster_framework.spark.configs_spark import spark_config

from dagster_framework.spark.utils import flatten_dict

SparkRDD = as_dagster_type(RDD, 'SparkRDD')


@resource(config_field=Field(Dict({'spark_conf': spark_config()})))
def spark_session_resource(init_context):
    builder = SparkSession.builder
    flat = flatten_dict(init_context.resource_config['spark_conf'])
    for key, value in flat:
        builder = builder.config(key, value)

    spark = builder.getOrCreate()
    try:
        yield spark
    finally:
        spark.stop()
