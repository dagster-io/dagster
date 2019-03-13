"""Type definitions for the airline_demo."""


import os
import pickle
import shutil
import tempfile

from collections import namedtuple

import sqlalchemy

from pyspark.sql import DataFrame

from dagster import as_dagster_type, Bool, dagster_type, Dict, Field, String
from dagster.core.types.marshal import SerializationStrategy
from dagster.core.types.runtime import Stringish


AirlineDemoResources = namedtuple(
    'AirlineDemoResources',
    ('spark', 's3', 'db_url', 'db_engine', 'db_dialect', 'redshift_s3_temp_dir', 'db_load'),
)


class SparkDataFrameSerializationStrategy(SerializationStrategy):
    def serialize_value(self, pipeline_context, value, write_file_obj):
        pickle_file_dir = pipeline_context.resources.tempfile.tempdir()
        shutil.rmtree(pickle_file_dir)
        value.rdd.saveAsPickleFile(pickle_file_dir)

        with tempfile.NamedTemporaryFile() as archive_file_obj:
            archive_file_path = archive_file_obj.name
            shutil.make_archive(archive_file_path, 'zip', pickle_file_dir)
            with open(archive_file_path, 'rb') as archive_file_read_obj:
                write_file_obj.write(archive_file_read_obj.read())

    def deserialize_value(self, pipeline_context, read_file_obj):
        with tempfile.NamedTemporaryFile() as archive_file_obj:
            archive_file_obj.write(read_file_obj.read())
            pickle_file_dir = pipeline_context.resources.tempfile.tempdir()
            # FIXME this breaks on py2
            shutil.unpack_archive(archive_file_obj.name, pickle_file_dir, 'zip')
            return pipeline_context.resources.spark.pickleFile(pickle_file_dir).toDF()


SparkDataFrameType = as_dagster_type(
    DataFrame,
    name='SparkDataFrameType',
    description='A Pyspark data frame.',
    serialization_strategy=SparkDataFrameSerializationStrategy(),
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


S3ConfigData = Dict(
    {'s3_bucket_name': Field(String), 'signed': Field(Bool, default_value=False, is_optional=True)}
)
