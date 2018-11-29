"""Pipeline definitions for the airline_demo."""
import logging

import boto3
import sqlalchemy

from pyspark.sql import SparkSession

from dagster import (
    DependencyDefinition,
    ExecutionContext,
    Field,
    PipelineContextDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    SolidInstance,
    types,
)

from .solids import (
    download_from_s3,
    ingest_csv_to_spark,
    join_spark_data_frames,
    load_data_to_database_from_spark,
    normalize_weather_na_values,
    subsample_spark_dataset,
    thunk,
    unzip_file,
)
from .types import (
    AirlineDemoResources,
)


def _create_spark_session_local():
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


def _create_s3_session():
    s3 = boto3.resource('s3').meta.client  # pylint:disable=C0103
    return s3


def _create_redshift_db_url(username, password, hostname, db_name, jdbc=True):
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


def _create_redshift_engine(username, password, hostname, db_name):
    db_url = _create_redshift_db_url(username, password, hostname, db_name, jdbc=False)
    return sqlalchemy.create_engine(db_url)


def _create_postgres_db_url(username, password, hostname, db_name, jdbc=True):
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


def _create_postgres_engine(username, password, hostname, db_name):
    db_url = _create_postgres_db_url(username, password, hostname, db_name, jdbc=False)
    return sqlalchemy.create_engine(db_url)


test_context = PipelineContextDefinition(
    context_fn=(
        lambda info: ExecutionContext.console_logging(
            log_level=logging.DEBUG,
            resources=AirlineDemoResources(
                _create_spark_session_local(), # FIXME
                _create_s3_session(),
                _create_redshift_db_url(
                    info.config['redshift_username'],
                    info.config['redshift_password'],
                    info.config['redshift_hostname'],
                    info.config['redshift_db_name'],
                ),
                _create_redshift_engine(
                    info.config['redshift_username'],
                    info.config['redshift_password'],
                    info.config['redshift_hostname'],
                    info.config['redshift_db_name'],
                ),
                info.config['db_dialect'],
                info.config['redshift_s3_temp_dir'],
            )
        )
    ),
    config_field=Field(
        dagster_type=types.ConfigDictionary(
            'TestContextConfig', {
                'redshift_username': Field(types.String),
                'redshift_password': Field(types.String),
                'redshift_hostname': Field(types.String),
                'redshift_db_name': Field(types.String),
                'db_dialect': Field(types.String),
                'redshift_s3_temp_dir': Field(types.String),
            }
        )
    ),
)


local_context = PipelineContextDefinition(
    context_fn=(
        lambda info: ExecutionContext.console_logging(
            log_level=logging.DEBUG,
            resources=AirlineDemoResources(
                _create_spark_session_local(),
                _create_s3_session(),
                _create_postgres_db_url(
                    info.config['postgres_username'],
                    info.config['postgres_password'],
                    info.config['postgres_hostname'],
                    info.config['postgres_db_name'],
                ),
                _create_postgres_engine(
                    info.config['postgres_username'],
                    info.config['postgres_password'],
                    info.config['postgres_hostname'],
                    info.config['postgres_db_name'],
                ),
                info.config['db_dialect'],
                ''
            )
        )
    ),
    config_field=Field(
        dagster_type=types.ConfigDictionary(
            'LocalContextConfig', {
                'postgres_username': Field(types.String),
                'postgres_password': Field(types.String),
                'postgres_hostname': Field(types.String),
                'postgres_db_name': Field(types.String),
                'db_dialect': Field(types.String),
            }
        )
    ),
)


cloud_context = PipelineContextDefinition(
    context_fn=(
        lambda info: ExecutionContext.console_logging(
            log_level=logging.DEBUG,
            resources=AirlineDemoResources(
                _create_spark_session_local(), # FIXME
                _create_s3_session(),
                _create_redshift_db_url(
                    info.config['redshift_username'],
                    info.config['redshift_password'],
                    info.config['redshift_hostname'],
                    info.config['redshift_db_name'],
                ),
                _create_redshift_engine(
                    info.config['redshift_username'],
                    info.config['redshift_password'],
                    info.config['redshift_hostname'],
                    info.config['redshift_db_name'],
                ),
                info.config['db_dialect'],
                ''
            )
        )
    ),
    config_field=Field(
        dagster_type=types.ConfigDictionary(
            'CloudContextConfig', {
                'redshift_username': Field(types.String),
                'redshift_password': Field(types.String),
                'redshift_hostname': Field(types.String),
                'db_dialect': Field(types.String),
                'redshift_s3_temp_dir': Field(types.String),
            }
        )
    ),
)

context_definitions = {
    'test': test_context,
    'local': local_context,
    'cloud': cloud_context,
}

solids = [
    download_from_s3,
    ingest_csv_to_spark,
    join_spark_data_frames,
    load_data_to_database_from_spark,
    normalize_weather_na_values,
    subsample_spark_dataset,
    thunk,
    unzip_file,
]


def define_airline_demo_download_pipeline():
    dependencies = {
        SolidInstance('thunk', alias='april_on_time_data_filename'): {},
        SolidInstance('thunk', alias='may_on_time_data_filename'): {},
        SolidInstance('thunk', alias='june_on_time_data_filename'): {},
        SolidInstance('thunk', alias='q2_coupon_data_filename'): {},
        SolidInstance('thunk', alias='q2_market_data_filename'): {},
        SolidInstance('thunk', alias='q2_ticket_data_filename'): {},
        SolidInstance('download_from_s3', alias='download_april_on_time_data'): {},
        SolidInstance('download_from_s3', alias='download_may_on_time_data'): {},
        SolidInstance('download_from_s3', alias='download_june_on_time_data'): {},
        SolidInstance('download_from_s3', alias='download_q2_coupon_data'): {},
        SolidInstance('download_from_s3', alias='download_q2_market_data'): {},
        SolidInstance('download_from_s3', alias='download_q2_ticket_data'): {},
        SolidInstance('download_from_s3', alias='download_q2_sfo_weather'): {},
        SolidInstance('unzip_file', alias='unzip_april_on_time_data'): {
            'archive_path': DependencyDefinition('download_april_on_time_data'),
            'archive_member': DependencyDefinition('april_on_time_data_filename'),
        },
        SolidInstance('unzip_file', alias='unzip_may_on_time_data'): {
            'archive_path': DependencyDefinition('download_may_on_time_data'),
            'archive_member': DependencyDefinition('may_on_time_data_filename'),
        },
        SolidInstance('unzip_file', alias='unzip_june_on_time_data'): {
            'archive_path': DependencyDefinition('download_june_on_time_data'),
            'archive_member': DependencyDefinition('june_on_time_data_filename'),
        },
        SolidInstance('unzip_file', alias='unzip_q2_coupon_data'): {
            'archive_path': DependencyDefinition('download_q2_coupon_data'),
            'archive_member': DependencyDefinition('q2_coupon_data_filename'),
        },
        SolidInstance('unzip_file', alias='unzip_q2_market_data'): {
            'archive_path': DependencyDefinition('download_q2_market_data'),
            'archive_member': DependencyDefinition('q2_market_data_filename'),
        },
        SolidInstance('unzip_file', alias='unzip_q2_ticket_data'): {
            'archive_path': DependencyDefinition('download_q2_ticket_data'),
            'archive_member': DependencyDefinition('q2_ticket_data_filename'),
        },
    }
    return PipelineDefinition(
        name='airline_demo_download_pipeline',
        context_definitions=context_definitions,
        solids=solids,
        dependencies=dependencies,
    )


def define_airline_demo_ingest_pipeline():
    dependencies = {
        SolidInstance('ingest_csv_to_spark', alias='ingest_april_on_time_data'): {
            'input_csv': DependencyDefinition('unzip_april_on_time_data'),
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_may_on_time_data'): {
            'input_csv': DependencyDefinition('unzip_may_on_time_data'),
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_june_on_time_data'): {
            'input_csv': DependencyDefinition('unzip_june_on_time_data'),
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_sfo_weather'): {
            'input_csv': DependencyDefinition('download_q2_sfo_weather'),
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_coupon_data'): {
            'input_csv': DependencyDefinition('unzip_q2_coupon_data'),
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_market_data'): {
            'input_csv': DependencyDefinition('unzip_q2_market_data'),
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_ticket_data'): {
            'input_csv': DependencyDefinition('unzip_q2_ticket_data'),
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_april_on_time_data'): {
            'data_frame': DependencyDefinition('ingest_april_on_time_data'),
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_may_on_time_data'): {
            'data_frame': DependencyDefinition('ingest_may_on_time_data'),
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_june_on_time_data'): {
            'data_frame': DependencyDefinition('ingest_june_on_time_data'),
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_q2_ticket_data'): {
            'data_frame': DependencyDefinition('ingest_q2_ticket_data'),
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_q2_market_data'): {
            'data_frame': DependencyDefinition('ingest_q2_market_data'),
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_q2_coupon_data'): {
            'data_frame': DependencyDefinition('ingest_q2_coupon_data'),
        },
        SolidInstance('normalize_weather_na_values', alias='normalize_q2_weather_na_values'): {
            'data_frame': DependencyDefinition('ingest_q2_sfo_weather'),
        },
        SolidInstance('join_spark_data_frames', alias='join_april_weather_to_on_time_data'): {
            'left_data_frame': DependencyDefinition('subsample_april_on_time_data'),
            'right_data_frame': DependencyDefinition('normalize_q2_weather_na_values'),
        },
        SolidInstance('join_spark_data_frames', alias='join_may_weather_to_on_time_data'): {
            'left_data_frame': DependencyDefinition('subsample_may_on_time_data'),
            'right_data_frame': DependencyDefinition('normalize_q2_weather_na_values'),
        },
        SolidInstance('join_spark_data_frames', alias='join_june_weather_to_on_time_data'): {
            'left_data_frame': DependencyDefinition('subsample_june_on_time_data'),
            'right_data_frame': DependencyDefinition('normalize_q2_weather_na_values'),
        },
        SolidInstance(
            'load_data_to_database_from_spark', alias='load_april_weather_and_on_time_data'
        ): {
            'data_frame': DependencyDefinition('join_april_weather_to_on_time_data'),
        },
        SolidInstance(
            'load_data_to_database_from_spark', alias='load_may_weather_and_on_time_data'
        ): {
            'data_frame': DependencyDefinition('join_may_weather_to_on_time_data'),
        },
        SolidInstance(
            'load_data_to_database_from_spark', alias='load_june_weather_and_on_time_data'
        ): {
            'data_frame': DependencyDefinition('join_june_weather_to_on_time_data'),
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_coupon_data'): {
            'data_frame': DependencyDefinition('subsample_q2_coupon_data'),
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_market_data'): {
            'data_frame': DependencyDefinition('subsample_q2_coupon_data'),
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_ticket_data'): {
            'data_frame': DependencyDefinition('subsample_q2_coupon_data'),
        },
    }

    return PipelineDefinition(
        name="airline_demo_ingest_pipeline",
        solids=solids,
        dependencies=dependencies,
        context_definitions=context_definitions,
    )


def define_airline_demo_warehouse_pipeline():
    return PipelineDefinition(
        name="airline_demo_warehouse_pipeline",
        solids=[],
        dependencies={},
        context_definitions=context_definitions,
    )


def define_repo():
    return RepositoryDefinition(
        name='airline_demo_repo',
        pipeline_dict={
            'airline_demo_download_pipeline': define_airline_demo_download_pipeline,
            'airline_demo_ingest_pipeline': define_airline_demo_ingest_pipeline,
            'airline_demo_warehouse_pipeline': define_airline_demo_warehouse_pipeline,
        }
    )
