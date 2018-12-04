import errno
import os

import boto3
import sqlalchemy

from botocore.handlers import disable_signing
from pyspark.sql import SparkSession


def mkdir_p(newdir, mode=0o777):
    """The missing mkdir -p functionality in os."""
    try:
        os.makedirs(newdir, mode)
    except OSError as err:
        # Reraise the error unless it's about an already existing directory
        if err.errno != errno.EEXIST or not os.path.isdir(newdir):
            raise


def create_spark_session_local():
    # Need two versions of this, one for test/local and one with a
    # configurable cluster
    spark = (
        SparkSession.builder.appName("AirlineDemo").config(
            'spark.jars.packages',
            'com.databricks:spark-avro_2.11:3.0.0,com.databricks:spark-redshift_2.11:2.0.1,'
            'com.databricks:spark-csv_2.11:1.5.0,org.postgresql:postgresql:42.2.5',
        ).getOrCreate()
    )
    return spark


def create_s3_session(signed=True):
    s3 = boto3.resource('s3').meta.client  # pylint:disable=C0103
    if not signed:
        s3.meta.events.register('choose-signer.s3.*', disable_signing)
    return s3


def create_redshift_db_url(username, password, hostname, db_name, jdbc=True):
    if jdbc:
        db_url = (
            'jdbc:postgresql://{hostname}:5432/{db_name}?'
            'user={username}&password={password}'.format(
                username=username,
                password=password,
                hostname=hostname,
                db_name=db_name,
            )
        )
    else:
        db_url = (
            "redshift_psycopg2://{username}:{password}@{hostname}:5439/{db_name}".format(
                username=username,
                password=password,
                hostname=hostname,
                db_name=db_name,
            )
        )
    return db_url


def create_redshift_engine(username, password, hostname, db_name):
    db_url = create_redshift_db_url(username, password, hostname, db_name, jdbc=False)
    return sqlalchemy.create_engine(db_url)


def create_postgres_db_url(username, password, hostname, db_name, jdbc=True):
    if jdbc:
        db_url = (
            'jdbc:postgresql://{hostname}:5432/{db_name}?'
            'user={username}&password={password}'.format(
                username=username,
                password=password,
                hostname=hostname,
                db_name=db_name,
            )
        )
    else:
        db_url = (
            'postgresql://{username}:{password}@{hostname}:5432/{db_name}'.format(
                username=username,
                password=password,
                hostname=hostname,
                db_name=db_name,
            )
        )
    return db_url


def create_postgres_engine(username, password, hostname, db_name):
    db_url = create_postgres_db_url(username, password, hostname, db_name, jdbc=False)
    return sqlalchemy.create_engine(db_url)
