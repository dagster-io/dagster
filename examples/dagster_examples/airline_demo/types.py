"""Type definitions for the airline_demo."""

from collections import namedtuple

import sqlalchemy

from dagster import define_python_dagster_type
from dagster.core.types.dagster_type import create_string_type

AirlineDemoResources = namedtuple(
    'AirlineDemoResources',
    ('spark', 's3', 'db_url', 'db_engine', 'db_dialect', 'redshift_s3_temp_dir', 'db_load'),
)


SqlAlchemyEngineType = define_python_dagster_type(
    sqlalchemy.engine.Connectable,
    name='SqlAlchemyEngineType',
    description='A SqlAlchemy Connectable',
)

SqlTableName = create_string_type('SqlTableName', description='The name of a database table')
