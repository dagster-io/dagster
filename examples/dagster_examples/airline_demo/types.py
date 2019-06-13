"""Type definitions for the airline_demo."""
import os

from collections import namedtuple

import sqlalchemy

from pyspark.sql import DataFrame

from dagster import (
    Bool,
    Dict,
    Field,
    Path,
    Selector,
    String,
    as_dagster_type,
    check,
    output_selector_schema,
)
from dagster.core.definitions.system_storage import fs_system_storage
from dagster.core.storage.type_storage import TypeStoragePlugin
from dagster.core.types.runtime import Stringish

from dagster_aws.s3.system_storage import s3_system_storage

AirlineDemoResources = namedtuple(
    'AirlineDemoResources',
    ('spark', 's3', 'db_url', 'db_engine', 'db_dialect', 'redshift_s3_temp_dir', 'db_load'),
)


class SparkDataFrameS3StoragePlugin(TypeStoragePlugin):  # pylint: disable=no-init
    @classmethod
    def compatible_with_storage_def(cls, system_storage_def):
        return system_storage_def is s3_system_storage

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
        return file_options['path']
    else:
        check.failed('Unsupported file type: {}'.format(file_type))


SparkDataFrameType = as_dagster_type(
    DataFrame,
    name='SparkDataFrameType',
    description='A Pyspark data frame.',
    auto_plugins=[SparkDataFrameS3StoragePlugin, SparkDataFrameFilesystemStoragePlugin],
    output_schema=spark_df_output_schema,
)


SqlAlchemyEngineType = as_dagster_type(
    sqlalchemy.engine.Connectable,
    name='SqlAlchemyEngineType',
    description='A SqlAlchemy Connectable',
)


class SqlTableName(Stringish):
    def __init__(self):
        super(SqlTableName, self).__init__(description='The name of a database table')


RedshiftConfigData = Dict(
    {
        'redshift_username': Field(String),
        'redshift_password': Field(String),
        'redshift_hostname': Field(String),
        'redshift_db_name': Field(String),
        's3_temp_dir': Field(String),
    }
)


DbInfo = namedtuple('DbInfo', 'engine url jdbc_url dialect load_table')


PostgresConfigData = Dict(
    {
        'postgres_username': Field(String),
        'postgres_password': Field(String),
        'postgres_hostname': Field(String),
        'postgres_db_name': Field(String),
    }
)
