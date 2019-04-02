"""Type definitions for the airline_demo."""


from collections import namedtuple
from io import BytesIO

import sqlalchemy

from pyspark.sql import DataFrame

from dagster import as_dagster_type, check, Dict, Field, String
from dagster.core.object_store import get_valid_target_path, TypeStoragePlugin
from dagster.core.runs import RunStorageMode
from dagster.core.types.runtime import Stringish, RuntimeType


AirlineDemoResources = namedtuple(
    'AirlineDemoResources',
    ('spark', 's3', 'db_url', 'db_engine', 'db_dialect', 'redshift_s3_temp_dir', 'db_load'),
)


class SparkDataFrameS3StoragePlugin(TypeStoragePlugin):  # pylint: disable=no-init
    @classmethod
    def set_object(cls, object_store, obj, _context, _runtime_type, paths):
        target_path = object_store.key_for_paths(paths)
        obj.write.parquet(object_store.url_for_paths(paths, protocol='s3a://'))
        return target_path

    @classmethod
    def get_object(cls, object_store, context, _runtime_type, paths):
        return context.resources.spark.read.parquet(
            object_store.url_for_paths(paths, protocol='s3a://')
        )


class SparkDataFrameFilesystemStoragePlugin(TypeStoragePlugin):  # pylint: disable=no-init
    @classmethod
    def set_object(cls, object_store, obj, _context, _runtime_type, paths):
        target_path = get_valid_target_path(object_store.root, paths)
        obj.write.parquet(object_store.url_for_paths(paths))
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
        RunStorageMode.FILESYSTEM: SparkDataFrameFilesystemStoragePlugin,
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


class BytesIOS3StoragePlugin(TypeStoragePlugin):  # pylint: disable=no-init
    @classmethod
    def set_object(cls, object_store, obj, context, runtime_type, paths):
        if isinstance(obj, bytes):
            return super(BytesIOS3StoragePlugin, cls).set_object(
                object_store, obj, context, runtime_type, paths
            )
        elif isinstance(obj, BytesIO):
            return super(BytesIOS3StoragePlugin, cls).set_object(
                object_store, obj.read(), context, runtime_type, paths
            )
        else:
            check.invariant('Shouldn\'t be here')

    @classmethod
    def get_object(cls, object_store, context, runtime_type, paths):
        return BytesIO(
            super(BytesIOS3StoragePlugin, cls).get_object(
                object_store, context, runtime_type, paths
            )
        )


class Bytes(RuntimeType, BytesIO):
    def __init__(self):
        self.storage_plugins = {RunStorageMode.S3: BytesIOS3StoragePlugin}
        super(Bytes, self).__init__(
            'Bytes', 'Bytes', description='Bytes representing the contents of a file.'
        )

    def coerce_runtime_value(self, value):
        if isinstance(value, BytesIO):
            return value
        if isinstance(value, bytes):
            return BytesIO(value)


class FileFromPath(RuntimeType):
    def __init__(self):
        self.storage_plugins = {RunStorageMode.S3: BytesIOS3StoragePlugin}
        super(FileFromPath, self).__init__(
            'FileFromPath',
            'FileFromPath',
            description='Bytes representing the contents of a file at a specific path.',
        )

    def coerce_runtime_value(self, value):
        with open(value, 'rb') as fd:
            return BytesIO(fd.read())


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
