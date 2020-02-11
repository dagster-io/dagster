import os

from pyspark.rdd import RDD
from pyspark.sql import DataFrame as NativeSparkDataFrame

from dagster import (
    Bool,
    Field,
    Materialization,
    Path,
    PythonObjectDagsterType,
    String,
    check,
    resource,
)
from dagster.config.field_utils import Selector
from dagster.core.storage.system_storage import fs_system_storage
from dagster.core.storage.type_storage import TypeStoragePlugin
from dagster.core.types.config_schema import input_selector_schema, output_selector_schema

from .decorators import pyspark_solid
from .resources import PySparkResourceDefinition, pyspark_resource, spark_session_from_config


@input_selector_schema(
    Selector(
        {
            'csv': {
                'path': Field(Path),
                'sep': Field(String, is_required=False),
                'header': Field(Bool, is_required=False),
            }
        }
    ),
    required_resource_keys={'spark'},
)
def load_rdd(context, file_type, file_options):
    if file_type == 'csv':
        return context.resources.spark.spark_session.read.csv(
            file_options['path'], sep=file_options.get('sep')
        ).rdd
    else:
        check.failed('Unsupported file type: {}'.format(file_type))


@output_selector_schema(
    Selector(
        {
            'csv': Field(
                {
                    'path': Field(Path),
                    'sep': Field(String, is_required=False),
                    'header': Field(Bool, is_required=False),
                }
            )
        }
    ),
    required_resource_keys={'spark'},
)
def write_rdd(context, file_type, file_options, spark_rdd):
    if file_type == 'csv':
        df = context.resources.spark.spark_session.createDataFrame(spark_rdd)
        context.log.info('DF: {}'.format(df))
        df.write.csv(
            file_options['path'], header=file_options.get('header'), sep=file_options.get('sep')
        )
    else:
        check.failed('Unsupported file type: {}'.format(file_type))


SparkRDD = PythonObjectDagsterType(
    python_type=RDD,
    name='SparkRDD',
    input_hydration_config=load_rdd,
    output_materialization_config=write_rdd,
)


@output_selector_schema(
    Selector(
        {
            'csv': {
                'path': Field(Path),
                'sep': Field(String, is_required=False),
                'header': Field(Bool, is_required=False),
            },
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
        return context.resources.spark.spark_session.read.parquet(
            intermediate_store.uri_for_paths(paths, protocol='s3a://')
        )

    @classmethod
    def required_resource_keys(cls):
        return frozenset({'spark'})


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
        return context.resources.spark.spark_session.read.parquet(
            os.path.join(intermediate_store.root, *paths)
        )

    @classmethod
    def required_resource_keys(cls):
        return frozenset({'spark'})


DataFrame = PythonObjectDagsterType(
    python_type=NativeSparkDataFrame,
    name='PySparkDataFrame',
    description='A Pyspark data frame.',
    auto_plugins=[SparkDataFrameS3StoragePlugin, SparkDataFrameFilesystemStoragePlugin],
    output_materialization_config=spark_df_output_schema,
)
