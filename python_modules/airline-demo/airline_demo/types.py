"""Type definitions for the airline_demo."""


import os

from collections import namedtuple

import sqlalchemy

from pyspark.sql import DataFrame

from dagster import as_dagster_type, Bool, dagster_type, Dict, Field, String
from dagster.core.types.runtime import PythonObjectType, Stringish
from dagster.utils import safe_isfile


AirlineDemoResources = namedtuple(
    'AirlineDemoResources',
    ('spark', 's3', 'db_url', 'db_engine', 'db_dialect', 'redshift_s3_temp_dir', 'db_load'),
)


SparkDataFrameType = as_dagster_type(
    DataFrame, name='SparkDataFrameType', description='A Pyspark data frame.'
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


S3ConfigData = Dict(
    {'s3_bucket_name': Field(String), 'signed': Field(Bool, default_value=False, is_optional=True)}
)
