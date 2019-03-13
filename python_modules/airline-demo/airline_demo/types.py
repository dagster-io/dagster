"""Type definitions for the airline_demo."""

import os
import shutil
import tempfile
import zipfile

from collections import namedtuple

import sqlalchemy

from pyspark.sql import DataFrame

from dagster import as_dagster_type, Bool, Dict, Field, String
from dagster.core.types.marshal import SerializationStrategy
from dagster.core.types.runtime import Stringish


# py2 compat
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


AirlineDemoResources = namedtuple(
    'AirlineDemoResources',
    ('spark', 's3', 'db_url', 'db_engine', 'db_dialect', 'redshift_s3_temp_dir', 'db_load'),
)


class SparkDataFrameSerializationStrategy(SerializationStrategy):
    def serialize_value(self, pipeline_context, value, write_file_obj):
        pickle_file_dir = pipeline_context.resources.tempfile.tempdir()
        shutil.rmtree(pickle_file_dir)
        value.rdd.saveAsPickleFile(pickle_file_dir)


        archive_file_obj = tempfile.NamedTemporaryFile(delete=False)
        try:
            archive_file_obj.close()
            archive_file_path = archive_file_obj.name
            zipfile_path = shutil.make_archive(
                archive_file_path, 'zip', pickle_file_dir
            )
            try:
                with open(zipfile_path, 'rb') as archive_file_read_obj:
                    write_file_obj.write(archive_file_read_obj.read())
            finally:
                try:
                    os.remove(zipfile_path)
                except FileNotFoundError:
                    pass
        finally:
            try:
                os.remove(archive_file_obj.name)
            except FileNotFoundError:
                pass

    def deserialize_value(self, pipeline_context, read_file_obj):
        archive_file_obj = tempfile.NamedTemporaryFile(delete=False)
        try:
            archive_file_obj.write(read_file_obj.read())
            archive_file_obj.close()
            pickle_file_dir = pipeline_context.resources.tempfile.tempdir()
            # We don't use the ZipFile context manager here because of py2
            zipfile_obj = zipfile.ZipFile(archive_file_obj.name)
            zipfile_obj.extractall(pickle_file_dir)
            zipfile_obj.close()
        finally:
            try:
                os.remove(archive_file_obj.name)
            except FileNotFoundError:
                pass
        rdd = pipeline_context.resources.spark.sparkContext.pickleFile(
            pickle_file_dir
        )
        return rdd.toDF()


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
