"""Type definitions for the airline_demo."""

from collections import namedtuple

import sqlalchemy

from dagster import as_dagster_type
from dagster.core.types.runtime.runtime_type import Stringish

AirlineDemoResources = namedtuple(
    'AirlineDemoResources',
    ('spark', 's3', 'db_url', 'db_engine', 'db_dialect', 'redshift_s3_temp_dir', 'db_load'),
)


SqlAlchemyEngineType = as_dagster_type(
    sqlalchemy.engine.Connectable,
    name='SqlAlchemyEngineType',
    description='A SqlAlchemy Connectable',
)


class SqlTableName(Stringish):
    def __init__(self):
        super(SqlTableName, self).__init__(description='The name of a database table')


DbInfo = namedtuple('DbInfo', 'engine url jdbc_url dialect load_table host db_name')
