import os

from pyspark.rdd import RDD
from pyspark.sql import DataFrame as NativeSparkDataFrame
from pyspark.sql import SparkSession

from dagster import (
    Bool,
    Dict,
    Field,
    Materialization,
    Path,
    String,
    as_dagster_type,
    check,
    resource,
)
from dagster.core.definitions.system_storage import fs_system_storage
from dagster.core.storage.type_storage import TypeStoragePlugin
from dagster.core.types import Selector, input_selector_schema, output_selector_schema
from dagster.core.types.runtime import define_any_type
from dagster_spark.configs_spark import spark_config
from dagster_spark.utils import flatten_dict


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


SparkRDD = as_dagster_type(
    RDD, 'SparkRDD', input_hydration_config=load_rdd, output_materialization_config=write_rdd
)


@resource({'spark_conf': spark_config()})
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
def spark_df_output_schema(_context, file_type, file_options, spark_df):
    if file_type == 'csv':
        spark_df.write.csv(
            file_options['path'], header=file_options.get('header'), sep=file_options.get('sep')
        )
        return Materialization.file(file_options['path'])
    else:
        check.failed('Unsupported file type: {}'.format(file_type))


class SparkDataFrameS3StoragePlugin(TypeStoragePlugin):  # pylint: disable=no-init
    @classmethod
    def compatible_with_storage_def(cls, system_storage_def):
        try:
            from dagster_aws.s3.system_storage import s3_system_storage

            return system_storage_def is s3_system_storage
        except ImportError:
            return False

    @classmethod
    def set_object(cls, intermediate_store, obj, _context, _runtime_type, paths):
        target_path = intermediate_store.object_store.key_for_paths(paths)
        obj.write.parquet(intermediate_store.uri_for_paths(paths, protocol='s3a://'))
        return target_path

    @classmethod
    def get_object(cls, intermediate_store, context, _runtime_type, paths):
        return context.resources.spark.read.parquet(
            intermediate_store.uri_for_paths(paths, protocol='s3a://')
        )


class SparkDataFrameFilesystemStoragePlugin(TypeStoragePlugin):  # pylint: disable=no-init
    @classmethod
    def compatible_with_storage_def(cls, system_storage_def):
        return system_storage_def is fs_system_storage

    @classmethod
    def set_object(cls, intermediate_store, obj, _context, _runtime_type, paths):
        target_path = os.path.join(intermediate_store.root, *paths)
        obj.write.parquet(intermediate_store.uri_for_paths(paths))
        return target_path

    @classmethod
    def get_object(cls, intermediate_store, context, _runtime_type, paths):
        return context.resources.spark.read.parquet(os.path.join(intermediate_store.root, *paths))


DataFrame = as_dagster_type(
    NativeSparkDataFrame,
    name='DataFrame',
    description='A Pyspark data frame.',
    auto_plugins=[SparkDataFrameS3StoragePlugin, SparkDataFrameFilesystemStoragePlugin],
    output_materialization_config=spark_df_output_schema,
)
