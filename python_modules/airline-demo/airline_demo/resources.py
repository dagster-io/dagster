import contextlib
import os
import shutil
import tempfile

from pyspark.sql import SparkSession

from dagster import Field, resource, check, Dict, String, Path, Bool
from dagster.utils import safe_isfile, mkdir_p

from .types import DbInfo, PostgresConfigData, RedshiftConfigData
from .utils import (
    create_postgres_db_url,
    create_postgres_engine,
    create_redshift_db_url,
    create_redshift_engine,
    create_s3_session,
    S3Logger,
)


class S3DownloadManager:
    def __init__(self, bucket, key, target_folder, skip_if_present):
        self.bucket = check.str_param(bucket, 'bucket')
        self.key = check.str_param(key, 'key')
        self.target_folder = check.str_param(target_folder, 'target_folder')
        self.skip_if_present = check.bool_param(skip_if_present, 'skip_if_present')

    def download_file(self, context, target_file):
        check.str_param(target_file, 'target_file')

        target_path = os.path.join(self.target_folder, target_file)

        if self.skip_if_present and safe_isfile(target_path):
            context.log.info(
                'Skipping download, file already present at {target_path}'.format(
                    target_path=target_path
                )
            )
        else:
            full_key = self.key + '/' + target_file
            if os.path.dirname(target_path):
                mkdir_p(os.path.dirname(target_path))

            context.log.info(
                'Starting download of {bucket}/{key} to {target_path}'.format(
                    bucket=self.bucket, key=full_key, target_path=target_path
                )
            )

            headers = context.resources.s3.head_object(Bucket=self.bucket, Key=full_key)
            logger = S3Logger(
                context.log.debug, self.bucket, full_key, target_path, int(headers['ContentLength'])
            )
            context.resources.s3.download_file(
                Bucket=self.bucket, Key=full_key, Filename=target_path, Callback=logger
            )

        return target_path

    def download_file_contents(self, context, target_file):
        check.str_param(target_file, 'target_file')
        full_key = self.key + '/' + target_file
        return context.resources.s3.get_object(Bucket=self.bucket, Key=full_key)['Body'].read()


@resource(
    config_field=Field(
        Dict(
            {
                'bucket': Field(String),
                'key': Field(String),
                'target_folder': Field(Path),
                'skip_if_present': Field(Bool),
            }
        )
    )
)
def s3_download_manager(init_context):
    return S3DownloadManager(
        bucket=init_context.resource_config['bucket'],
        key=init_context.resource_config['key'],
        target_folder=init_context.resource_config['target_folder'],
        skip_if_present=init_context.resource_config['skip_if_present'],
    )


@resource
def spark_session_local(_init_context):
    # Need two versions of this, one for test/local and one with a
    # configurable cluster
    spark = (
        SparkSession.builder.appName("AirlineDemo")
        .config(
            'spark.jars.packages',
            'com.databricks:spark-avro_2.11:3.0.0,'
            'com.databricks:spark-redshift_2.11:2.0.1,'
            'com.databricks:spark-csv_2.11:1.5.0,'
            'org.postgresql:postgresql:42.2.5,'
            'org.apache.hadoop:hadoop-aws:2.6.5,'
            'com.amazonaws:aws-java-sdk:1.7.4',
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


if __name__ == '__main__':
    # This is a brutal hack. When the SparkSession is created for the first time there is a lengthy
    # download process from Maven. This allows us to run python -m airline_demo.resources in the
    # Dockerfile and avoid a long runtime delay before each containerized solid executes.
    spark_session_local.resource_fn(None)
