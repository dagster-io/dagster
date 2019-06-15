"""Type definitions for the airline_demo."""

from collections import namedtuple

import sqlalchemy

from dagster import Dict, Field, String, as_dagster_type
from dagster.core.types.runtime import Stringish

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
