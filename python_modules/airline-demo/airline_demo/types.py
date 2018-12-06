"""Type definitions for the airline_demo."""

import sqlalchemy

from collections import namedtuple

from pyspark.sql import (
    DataFrame,
)
from dagster import (
    types,
)

AirlineDemoResources = namedtuple(
    'AirlineDemoResources',
    ('spark', 's3', 'db_url', 'db_engine', 'db_dialect', 'redshift_s3_temp_dir', 'db_load'),
)

SparkDataFrameType = types.PythonObjectType(
    'SparkDataFrameType',
    python_type=DataFrame,
    description='A Pyspark data frame.',
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
