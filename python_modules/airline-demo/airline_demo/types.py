"""Type definitions for the airline_demo."""


from collections import namedtuple

import sqlalchemy

from pyspark.sql import DataFrame

from dagster import as_dagster_type, Dict, Field, String
from dagster.core.object_store import get_valid_target_path
from dagster.core.runs import RunStorageMode
from dagster.core.types.runtime import Stringish
from dagster.utils import safe_isfile


AirlineDemoResources = namedtuple(
    'AirlineDemoResources',
    ('spark', 's3', 'db_url', 'db_engine', 'db_dialect', 'redshift_s3_temp_dir', 'db_load'),
)


def filesystem_set_spark_data_frame(self, obj, _context, _runtime_type, paths):
    target_path = get_valid_target_path(self.root, paths)
    obj.write.parquet('file://' + target_path)
    return target_path


def filesystem_get_spark_data_frame(self, context, _runtime_type, paths):
    return context.resources.spark.read.parquet(get_valid_target_path(self.root, paths))


def s3_set_spark_data_frame(self, obj, _context, _runtime_type, paths):
    target_path = self._key_for_paths(paths)
    obj.write.parquet('s3a://' + target_path)
    return target_path


def s3_get_spark_data_frame(self, context, _runtime_type, paths):
    return context.resources.spark.read.parquet('s3a://' + self._key_for_paths(paths))


SparkDataFrameType = as_dagster_type(
    DataFrame,
    name='SparkDataFrameType',
    description='A Pyspark data frame.',
    storage_overrides={
        RunStorageMode.S3: {
            'get_object': s3_get_spark_data_frame,
            'set_object': s3_set_spark_data_frame,
        },
        RunStorageMode.FILESYSTEM: {
            'get_object': filesystem_get_spark_data_frame,
            'set_object': filesystem_set_spark_data_frame,
        },
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
