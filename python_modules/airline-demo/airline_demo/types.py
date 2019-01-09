"""Type definitions for the airline_demo."""

from collections import namedtuple

import os

import sqlalchemy

from pyspark.sql import DataFrame

from dagster.core.types.runtime import PythonObjectType, Stringish

AirlineDemoResources = namedtuple(
    'AirlineDemoResources',
    ('spark', 's3', 'db_url', 'db_engine', 'db_dialect', 'redshift_s3_temp_dir', 'db_load'),
)


class SparkDataFrameType(PythonObjectType):
    def __init__(self):
        super(SparkDataFrameType, self).__init__(
            python_type=DataFrame, description='A Pyspark data frame.'
        )


class SqlAlchemyEngineType(PythonObjectType):
    def __init__(self):
        super(SqlAlchemyEngineType, self).__init__(
            python_type=sqlalchemy.engine.Connectable, description='A SqlAlchemy Connectable'
        )


class SqlTableName(Stringish):
    def __init__(self):
        super(SqlTableName, self).__init__(description='The name of a database table')


class FileExistsAtPath(Stringish):
    def __init__(self):
        super(FileExistsAtPath, self).__init__(description='A path at which a file actually exists')

    def coerce_runtime_value(self, value):
        value = super(FileExistsAtPath, self).coerce_runtime_value(value)
        return self.throw_if_false(os.path.isfile, value)
