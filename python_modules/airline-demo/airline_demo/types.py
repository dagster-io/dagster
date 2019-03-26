"""Type definitions for the airline_demo."""


import os
import shutil
import tempfile
import zipfile

from collections import namedtuple

import sqlalchemy

from pyspark.sql import DataFrame

from dagster import as_dagster_type, Dict, Field, String
from dagster.core.types.marshal import SerializationStrategy
from dagster.core.types.runtime import Stringish
from dagster.utils import safe_isfile


AirlineDemoResources = namedtuple(
    'AirlineDemoResources',
    ('spark', 's3', 'db_url', 'db_engine', 'db_dialect', 'redshift_s3_temp_dir', 'db_load'),
)


class SparkDataFrameParquetSerializationStrategy(SerializationStrategy):
    def serialize_value(self, _context, value, write_file_obj):
        parquet_dir = tempfile.mkdtemp()
        shutil.rmtree(parquet_dir)
        value.write.parquet(parquet_dir)

        archive_file_obj = tempfile.NamedTemporaryFile(delete=False)
        try:
            archive_file_obj.close()
            archive_file_path = archive_file_obj.name
            zipfile_path = shutil.make_archive(archive_file_path, 'zip', parquet_dir)
            try:
                with open(zipfile_path, 'rb') as archive_file_read_obj:
                    write_file_obj.write(archive_file_read_obj.read())
            finally:
                if os.path.isfile(zipfile_path):
                    os.remove(zipfile_path)
        finally:
            if os.path.isfile(archive_file_obj.name):
                os.remove(archive_file_obj.name)

    def deserialize_value(self, context, read_file_obj):
        archive_file_obj = tempfile.NamedTemporaryFile(delete=False)
        try:
            archive_file_obj.write(read_file_obj.read())
            archive_file_obj.close()
            parquet_dir = tempfile.mkdtemp()
            # We don't use the ZipFile context manager here because of py2
            zipfile_obj = zipfile.ZipFile(archive_file_obj.name)
            zipfile_obj.extractall(parquet_dir)
            zipfile_obj.close()
        finally:
            if os.path.isfile(archive_file_obj.name):
                os.remove(archive_file_obj.name)
        return context.resources.spark.read.parquet(parquet_dir)


SparkDataFrameType = as_dagster_type(
    DataFrame,
    name='SparkDataFrameType',
    description='A Pyspark data frame.',
    serialization_strategy=SparkDataFrameParquetSerializationStrategy(),
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
