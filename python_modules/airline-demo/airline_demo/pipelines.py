"""Pipeline definitions for the airline_demo."""
import logging

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
    canonicalize_column_names,
    download_from_s3,
    ingest_csv_to_spark,
    join_spark_data_frames,
    load_data_to_database_from_spark,
    normalize_weather_na_values,
    sfo_delays_by_destination,
    subsample_spark_dataset,
    thunk,
    union_spark_data_frames,
    unzip_file,
)
from .types import (
    AirlineDemoResources,
)
from .utils import (
    create_postgres_db_url,
    create_postgres_engine,
    create_redshift_db_url,
    create_redshift_engine,
    create_s3_session,
    create_spark_session_local,
)


def _db_load(data_frame, table_name, resources):
    db_dialect = resources.db_dialect
    if db_dialect == 'redshift':
        data_frame.write \
        .format('com.databricks.spark.redshift') \
        .option('tempdir', resources.redshift_s3_temp_dir) \
        .mode('overwrite') \
        .jdbc(
            resources.db_url,
            table_name,
        )
    elif db_dialect == 'postgres':
        data_frame.write \
        .option('driver', 'org.postgresql.Driver') \
        .mode('overwrite') \
        .jdbc(
            resources.db_url,
            table_name,
        )
    else:
        raise NotImplementedError(
            'No implementation for db_dialect "{db_dialect}"'.format(db_dialect=db_dialect)
        )

test_context = PipelineContextDefinition(
    context_fn=(
        lambda info: ExecutionContext.console_logging(
            log_level=logging.DEBUG,
            resources=AirlineDemoResources(
                create_spark_session_local(), # FIXME
                create_s3_session(),
                create_redshift_db_url(
                    info.config['redshift_username'],
                    info.config['redshift_password'],
                    info.config['redshift_hostname'],
                    info.config['redshift_db_name'],
                ),
                create_redshift_engine(
                    create_redshift_db_url(
                        info.config['redshift_username'],
                        info.config['redshift_password'],
                        info.config['redshift_hostname'],
                        info.config['redshift_db_name'],
                        jdbc=False,
                    ),
                ),
                info.config['db_dialect'],
                info.config['redshift_s3_temp_dir'],
                _db_load,
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
                create_spark_session_local(),
                create_s3_session(),
                create_postgres_db_url(
                    info.config['postgres_username'],
                    info.config['postgres_password'],
                    info.config['postgres_hostname'],
                    info.config['postgres_db_name'],
                ),
                create_postgres_engine(
                    create_postgres_db_url(
                        info.config['postgres_username'],
                        info.config['postgres_password'],
                        info.config['postgres_hostname'],
                        info.config['postgres_db_name'],
                        jdbc=False,
                    ),
                ),
                info.config['db_dialect'],
                '',
                _db_load,
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
                create_spark_session_local(), # FIXME
                create_s3_session(),
                create_redshift_db_url(
                    info.config['redshift_username'],
                    info.config['redshift_password'],
                    info.config['redshift_hostname'],
                    info.config['redshift_db_name'],
                ),
                create_redshift_engine(
                    create_redshift_db_url(
                        info.config['redshift_username'],
                        info.config['redshift_password'],
                        info.config['redshift_hostname'],
                        info.config['redshift_db_name'],
                        jdbc=False,
                    ),
                ),
                info.config['db_dialect'],
                '',
                _db_load,
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


def define_airline_demo_download_pipeline():
    solids = [
        download_from_s3,
        thunk,
        unzip_file,
    ]
    dependencies = {
        SolidInstance('thunk', alias='april_on_time_data_filename'): {},
        SolidInstance('thunk', alias='may_on_time_data_filename'): {},
        SolidInstance('thunk', alias='june_on_time_data_filename'): {},
        SolidInstance('thunk', alias='q2_coupon_data_filename'): {},
        SolidInstance('thunk', alias='q2_market_data_filename'): {},
        SolidInstance('thunk', alias='q2_ticket_data_filename'): {},
        SolidInstance('thunk', alias='master_cord_data_filename'): {},
        SolidInstance('download_from_s3', alias='download_april_on_time_data'): {},
        SolidInstance('download_from_s3', alias='download_may_on_time_data'): {},
        SolidInstance('download_from_s3', alias='download_june_on_time_data'): {},
        SolidInstance('download_from_s3', alias='download_q2_coupon_data'): {},
        SolidInstance('download_from_s3', alias='download_q2_market_data'): {},
        SolidInstance('download_from_s3', alias='download_q2_ticket_data'): {},
        SolidInstance('download_from_s3', alias='download_q2_sfo_weather'): {},
        SolidInstance('download_from_s3', alias='download_master_cord_data'): {},
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
        SolidInstance('unzip_file', alias='unzip_master_cord_data'): {
            'archive_path': DependencyDefinition('download_master_cord_data'),
            'archive_member': DependencyDefinition('master_cord_data_filename'),
        },
    }
    return PipelineDefinition(
        name='airline_demo_download_pipeline',
        context_definitions=context_definitions,
        solids=solids,
        dependencies=dependencies,
    )


def define_airline_demo_ingest_pipeline():
    solids = [
        canonicalize_column_names,
        ingest_csv_to_spark,
        join_spark_data_frames,
        load_data_to_database_from_spark,
        normalize_weather_na_values,
        subsample_spark_dataset,
        thunk,
        union_spark_data_frames,
    ]
    dependencies = {
        SolidInstance('thunk', alias='april_on_time_data_filename'): {},
        SolidInstance('thunk', alias='may_on_time_data_filename'): {},
        SolidInstance('thunk', alias='june_on_time_data_filename'): {},
        SolidInstance('thunk', alias='q2_coupon_data_filename'): {},
        SolidInstance('thunk', alias='q2_market_data_filename'): {},
        SolidInstance('thunk', alias='q2_ticket_data_filename'): {},
        SolidInstance('thunk', alias='q2_sfo_weather_filename'): {},
        SolidInstance('thunk', alias='master_cord_data_filename'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_april_on_time_data'): {
            'input_csv': DependencyDefinition('april_on_time_data_filename'),
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_may_on_time_data'): {
            'input_csv': DependencyDefinition('may_on_time_data_filename'),
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_june_on_time_data'): {
            'input_csv': DependencyDefinition('june_on_time_data_filename'),
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_sfo_weather'): {
            'input_csv': DependencyDefinition('q2_sfo_weather_filename'),
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_coupon_data'): {
            'input_csv': DependencyDefinition('q2_coupon_data_filename'),
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_market_data'): {
            'input_csv': DependencyDefinition('q2_market_data_filename'),
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_ticket_data'): {
            'input_csv': DependencyDefinition('q2_ticket_data_filename'),
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_master_cord_data'): {
            'input_csv': DependencyDefinition('master_cord_data_filename'),
        },
        SolidInstance('union_spark_data_frames', alias='combine_april_may_on_time_data'): {
            'left_data_frame': DependencyDefinition('ingest_april_on_time_data'),
            'right_data_frame': DependencyDefinition('ingest_may_on_time_data'),
        },
        SolidInstance('union_spark_data_frames', alias='combine_q2_on_time_data'): {
            'left_data_frame': DependencyDefinition('combine_april_may_on_time_data'),
            'right_data_frame': DependencyDefinition('ingest_june_on_time_data'),
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_q2_on_time_data'): {
            'data_frame': DependencyDefinition('combine_q2_on_time_data'),
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
        SolidInstance('join_spark_data_frames', alias='join_q2_on_time_data_to_master_cord_data'): {
            'left_data_frame': DependencyDefinition('subsample_q2_on_time_data'),
            'right_data_frame': DependencyDefinition('ingest_master_cord_data'),
        },
        SolidInstance('canonicalize_column_names', alias='canonicalize_q2_on_time_data'): {
            'data_frame': DependencyDefinition('join_q2_on_time_data_to_master_cord_data'),
        },
        SolidInstance('canonicalize_column_names', alias='canonicalize_q2_coupon_data'): {
            'data_frame': DependencyDefinition('subsample_q2_coupon_data'),
        },
        SolidInstance('canonicalize_column_names', alias='canonicalize_q2_market_data'): {
            'data_frame': DependencyDefinition('subsample_q2_market_data'),
        },
        SolidInstance('canonicalize_column_names', alias='canonicalize_q2_ticket_data'): {
            'data_frame': DependencyDefinition('subsample_q2_ticket_data'),
        },
        SolidInstance('canonicalize_column_names', alias='canonicalize_q2_sfo_weather'): {
            'data_frame': DependencyDefinition('normalize_q2_weather_na_values'),
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_on_time_data'): {
            'data_frame': DependencyDefinition('canonicalize_q2_on_time_data'),
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_coupon_data'): {
            'data_frame': DependencyDefinition('canonicalize_q2_coupon_data'),
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_market_data'): {
            'data_frame': DependencyDefinition('canonicalize_q2_market_data'),
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_ticket_data'): {
            'data_frame': DependencyDefinition('canonicalize_q2_ticket_data'),
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_sfo_weather'): {
            'data_frame': DependencyDefinition('canonicalize_q2_sfo_weather'),
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
        solids=[sfo_delays_by_destination, thunk],
        dependencies={
            SolidInstance('thunk', alias='db_url'): {},
            's_f_o__delays_by__destination': {
                'engine': DependencyDefinition('db_url'),
            }
        },
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
