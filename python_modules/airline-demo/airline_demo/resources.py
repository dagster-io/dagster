'''Resource definitions for the airline demo.'''
import contextlib
import io
import os
import shutil
import tempfile

from abc import ABCMeta, abstractmethod

import boto3
import six

from botocore.exceptions import ClientError
from botocore.handlers import disable_signing
from pyspark.sql import SparkSession

from dagster import Field, resource
from dagster.utils import safe_isfile

from .types import DbInfo, PostgresConfigData, RedshiftConfigData, S3ConfigData
from .utils import (
    create_postgres_db_url,
    create_postgres_engine,
    create_redshift_db_url,
    create_redshift_engine,
    create_s3_session,
)


@resource
def spark_session_local(_init_context):
    # Need two versions of this, one for test/local and one with a
    # configurable cluster
    spark = (
        SparkSession.builder.appName("AirlineDemo")
        .config(
            'spark.jars.packages',
            'com.databricks:spark-avro_2.11:3.0.0,com.databricks:spark-redshift_2.11:2.0.1,'
            'com.databricks:spark-csv_2.11:1.5.0,org.postgresql:postgresql:42.2.5',
        )
        .getOrCreate()
    )
    return spark


@resource
def unsigned_s3_session(_init_context):
    return create_s3_session(signed=False)


class TempfileManager(object):
    def __init__(self):
        self.paths = []
        self.files = []
        self.dirs = []

    def tempfile(self):
        temporary_file = tempfile.NamedTemporaryFile('w+b', delete=False)
        self.files.append(temporary_file)
        self.paths.append(temporary_file.name)
        return temporary_file

    def tempdir(self):
        temporary_directory = tempfile.mkdtemp()
        self.dirs.append(temporary_directory)
        return temporary_directory

    def close(self):
        for fobj in self.files:
            fobj.close()
        for path in self.paths:
            if os.path.exists(path):
                os.remove(path)
        for dir_ in self.dirs:
            shutil.rmtree(dir_)


@contextlib.contextmanager
def _tempfile_manager():
    manager = TempfileManager()
    try:
        yield manager
    finally:
        manager.close()


@resource
def tempfile_resource(_init_context):
    with _tempfile_manager() as manager:
        yield manager


@resource(config_field=Field(RedshiftConfigData))
def redshift_db_info_resource(init_context):
    db_url_jdbc = create_redshift_db_url(
        init_context.resource_config['redshift_username'],
        init_context.resource_config['redshift_password'],
        init_context.resource_config['redshift_hostname'],
        init_context.resource_config['redshift_db_name'],
    )

    db_url = create_redshift_db_url(
        init_context.resource_config['redshift_username'],
        init_context.resource_config['redshift_password'],
        init_context.resource_config['redshift_hostname'],
        init_context.resource_config['redshift_db_name'],
        jdbc=False,
    )

    s3_temp_dir = init_context.resource_config['s3_temp_dir']

    def _do_load(data_frame, table_name):
        data_frame.write.format('com.databricks.spark.redshift').option(
            'tempdir', s3_temp_dir
        ).mode('overwrite').jdbc(db_url_jdbc, table_name)

    return DbInfo(
        url=db_url,
        jdbc_url=db_url_jdbc,
        engine=create_redshift_engine(db_url),
        dialect='redshift',
        load_table=_do_load,
    )


@resource(config_field=Field(PostgresConfigData))
def postgres_db_info_resource(init_context):
    db_url_jdbc = create_postgres_db_url(
        init_context.resource_config['postgres_username'],
        init_context.resource_config['postgres_password'],
        init_context.resource_config['postgres_hostname'],
        init_context.resource_config['postgres_db_name'],
    )

    db_url = create_postgres_db_url(
        init_context.resource_config['postgres_username'],
        init_context.resource_config['postgres_password'],
        init_context.resource_config['postgres_hostname'],
        init_context.resource_config['postgres_db_name'],
        jdbc=False,
    )

    def _do_load(data_frame, table_name):
        data_frame.write.option('driver', 'org.postgresql.Driver').mode('overwrite').jdbc(
            db_url_jdbc, table_name
        )

    return DbInfo(
        url=db_url,
        jdbc_url=db_url_jdbc,
        engine=create_postgres_engine(db_url),
        dialect='postgres',
        load_table=_do_load,
    )


class AbstractFilesystemManager(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractmethod
    def is_file(self, path):
        pass

    @abstractmethod
    def is_dir(self, path):
        pass

    @abstractmethod
    @contextlib.contextmanager
    def write(self, path):
        pass

    @abstractmethod
    @contextlib.contextmanager
    def read(self, path):
        pass

    @abstractmethod
    def join(self, *path_fragments):
        pass


class LocalFilesystemManager(AbstractFilesystemManager):  # pylint: disable=no-init
    def is_file(self, path):
        return safe_isfile(path)

    def is_dir(self, path):
        return os.path.isdir(path)

    @contextlib.contextmanager
    def write(self, path):
        with open(path, 'wb') as file_obj:
            yield file_obj

    @contextlib.contextmanager
    def read(self, path):
        with open(path, 'rb') as file_obj:
            yield file_obj

    def join(self, *path_fragments):
        return os.path.join(*path_fragments)


class S3FilesystemManager(AbstractFilesystemManager):
    def __init__(self, s3_bucket_name, signed=True):
        self.s3_bucket_name = s3_bucket_name
        self.client = boto3.client('s3')

        self.signed = signed
        if not self.signed:
            self.client.meta.events.register('choose-signer.s3.*', disable_signing)


    def is_dir(self, path):
        try:
            self.client.head_object(Bucket=self.s3_bucket_name, Key=path)
            return False
        except ClientError as exc:
            if exc.response['Error']['Code'] == '404':
                res = self.client.list_objects(Bucket=self.s3_bucket_name, Prefix=path)
                if 'Contents' in res:
                    return True
                return False
            raise

    def is_file(self, path):
        try:
            self.client.head_object(Bucket=self.s3_bucket_name, Key=path)
            return True
        except ClientError as exc:
            if exc.response['Error']['Code'] == '404':
                return False
            raise

    @contextlib.contextmanager
    def write(self, path):
        with tempfile.TemporaryFile() as file_obj:
            yield file_obj
            file_obj.seek(0)
            if not self.signed:
                self.client.upload_fileobj(Fileobj=file_obj, Bucket=self.s3_bucket_name, Key=path, ExtraArgs={'ACL': 'public-read'})
            else:
                self.client.upload_fileobj(Fileobj=file_obj, Bucket=self.s3_bucket_name, Key=path)

    @contextlib.contextmanager
    def read(self, path):
        res = self.client.get_object(Bucket=self.s3_bucket_name, Key=path)
        yield io.BytesIO(res['Body'].read())

    def join(self, *path_fragments):
        return '/'.join(path_fragments)


@resource
def local_filesystem_resource(_init_context):
    yield LocalFilesystemManager()


@resource(config_field=Field(S3ConfigData))
def s3_filesystem_resource(init_context):
    yield S3FilesystemManager(s3_bucket_name=init_context.resource_config['s3_bucket_name'], signed=init_context.resource_config['signed'])
