"""Type definitions for the airline_demo."""

import os

import sqlalchemy

from collections import namedtuple

from pyspark.sql import DataFrame
from dagster import types

AirlineDemoResources = namedtuple(
    'AirlineDemoResources',
    ('spark', 's3', 'db_url', 'db_engine', 'db_dialect', 'redshift_s3_temp_dir', 'db_load'),
)

SparkDataFrameType = types.PythonObjectType(
    'SparkDataFrameType', python_type=DataFrame, description='A Pyspark data frame.'
)

SqlAlchemyEngineType = types.PythonObjectType(
    'SqlAlchemyEngineType',
    python_type=sqlalchemy.engine.Connectable,
    description='A SqlAlchemy Connectable',
)
# SqlAlchemyQueryType = types.PythonObjectType(
#     'SqlAlchemyQueryType',
#     python_type=sqlalchemy.orm.query.Query,
#     description='A SQLAlchemy query.',
# )

# SqlAlchemySubqueryType = types.PythonObjectType(
#     'SqlAlchemySubqueryType',
#     python_type=sqlalchemy.sql.expression.Alias,
#     description='A SQLAlchemy subquery',
# )

# SqlAlchemyResultProxyType = types.PythonObjectType(
#     'SqlAlchemyResultProxyType',
#     python_type=sqlalchemy.engine.ResultProxy,
#     description='A SQLAlchemy result proxy',
# )

SqlTableName = types.DagsterStringType(
    name='SqlTableName', description='The name of a database table'
)


class _FileExistsAtPath(types.DagsterStringType):
    def __init__(self):
        super(_FileExistsAtPath, self).__init__(
            name='FileExistsAtPath', description='A path at which a file actually exists'
        )

    def is_python_valid_value(self, value):
        return super(_FileExistsAtPath, self).is_python_valid_value(value) and os.path.isfile(value)


FileExistsAtPath = _FileExistsAtPath()
