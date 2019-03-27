"""Type definitions for the airline_demo."""


from collections import namedtuple

import sqlalchemy

from pyspark.sql import DataFrame

from dagster import as_dagster_type, Dict, Field, String
from dagster.core.object_store import get_valid_target_path, TypeStoragePlugin
from dagster.core.runs import RunStorageMode
from dagster.core.types.runtime import Stringish
from dagster.utils import safe_isfile


AirlineDemoResources = namedtuple(
    'AirlineDemoResources',
    ('spark', 's3', 'db_url', 'db_engine', 'db_dialect', 'redshift_s3_temp_dir', 'db_load'),
)


class SparkDataFrameS3StoragePlugin(TypeStoragePlugin):  # pylint: disable=no-init
    @classmethod
    def set_object(cls, object_store, obj, _context, _runtime_type, paths):
        target_path = object_store.key_for_paths(paths)
        obj.write.parquet('s3a://' + target_path)
        return target_path

    @classmethod
    def get_object(cls, object_store, context, _runtime_type, paths):
        return context.resources.spark.read.parquet('s3a://' + object_store.key_for_paths(paths))


class SparkDataFrameFilesystemStorageOverride(TypeStoragePlugin):  # pylint: disable=no-init
    @classmethod
    def set_object(cls, object_store, obj, _context, _runtime_type, paths):
        target_path = get_valid_target_path(object_store.root, paths)
        obj.write.parquet('file://' + target_path)
        return target_path

    @classmethod
    def get_object(cls, object_store, context, _runtime_type, paths):
        return context.resources.spark.read.parquet(get_valid_target_path(object_store.root, paths))


SparkDataFrameType = as_dagster_type(
    DataFrame,
    name='SparkDataFrameType',
    description='A Pyspark data frame.',
    storage_plugins={
        RunStorageMode.S3: SparkDataFrameS3StoragePlugin,
        RunStorageMode.FILESYSTEM: SparkDataFrameFilesystemStorageOverride,
    },
)


SqlAlchemyEngineType = as_dagster_type(
    sqlalchemy.engine.Connectable,
    name='SqlAlchemyEngineType',
    description='A SqlAlchemy Connectable',
)


class SqlTableName(Stringish):
    def __init__(self):
        super(SqlTableName, self).__init__(description='The name of a database table')


class FileExistsAtPath(Stringish):
    def __init__(self):
        super(FileExistsAtPath, self).__init__(description='A path at which a file actually exists')

    def coerce_runtime_value(self, value):
        value = super(FileExistsAtPath, self).coerce_runtime_value(value)
        return self.throw_if_false(safe_isfile, value)


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
