# getting false positives in vscode
from pyspark.sql import SparkSession  # pylint: disable=no-name-in-module,import-error
from pyspark.rdd import RDD  # pylint: disable=no-name-in-module,import-error

from dagster import (
    Bool,
    Dict,
    Field,
    Selector,
    Path,
    String,
    as_dagster_type,
    check,
    input_selector_schema,
    output_selector_schema,
    resource,
)
from dagster.core.types.runtime import define_any_type

from dagster_framework.spark.configs_spark import spark_config

from dagster_framework.spark.utils import flatten_dict


@input_selector_schema(
    Selector(
        {
            'csv': Field(
                Dict(
                    {
                        'path': Field(Path),
                        'sep': Field(String, is_optional=True),
                        'header': Field(Bool, is_optional=True),
                    }
                )
            )
        }
    )
)
def load_rdd(context, file_type, file_options):
    if file_type == 'csv':
        return context.resources.spark.read.csv(
            file_options['path'], sep=file_options.get('sep')
        ).rdd
    else:
        check.failed('Unsupported file type: {}'.format(file_type))


@output_selector_schema(
    Selector(
        {
            'csv': Field(
                Dict(
                    {
                        'path': Field(Path),
                        'sep': Field(String, is_optional=True),
                        'header': Field(Bool, is_optional=True),
                    }
                )
            )
        }
    )
)
def write_rdd(context, file_type, file_options, spark_rdd):
    if file_type == 'csv':
        df = context.resources.spark.createDataFrame(spark_rdd)
        context.log.info('DF: {}'.format(df))
        df.write.csv(
            file_options['path'], header=file_options.get('header'), sep=file_options.get('sep')
        )
    else:
        check.failed('Unsupported file type: {}'.format(file_type))


SparkRDD = as_dagster_type(RDD, 'SparkRDD', input_schema=load_rdd, output_schema=write_rdd)


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
