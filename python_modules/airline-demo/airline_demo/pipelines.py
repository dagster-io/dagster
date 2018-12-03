"""Pipeline definitions for the airline_demo."""
import contextlib
import logging
import os
import shutil
import tempfile

from dagster import (
    DependencyDefinition,
    ExecutionContext,
    Field,
    PipelineContextDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    ResourceDefinition,
    SolidInstance,
    types,
)

from .solids import (
    average_sfo_outbound_avg_delays_by_destination,
    canonicalize_column_names,
    delays_by_geography,
    delays_vs_fares,
    delays_vs_fares_nb,
    eastbound_delays,
    download_and_unzip_files_from_s3,
    ingest_csv_to_spark,
    join_spark_data_frames,
    load_data_to_database_from_spark,
    normalize_weather_na_values,
    prefix_column_names,
    q2_sfo_outbound_flights,
    sfo_delays_by_destination,
    subsample_spark_dataset,
    thunk,
    tickets_with_destination,
    union_spark_data_frames,
    upload_to_s3,
    westbound_delays,
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


def define_lambda_resource(func, *args, **kwargs):
    return ResourceDefinition(lambda _info: func(*args, **kwargs))


def define_value_resource(value):
    return ResourceDefinition(lambda _info: value)


def define_null_resource():
    return define_value_resource(None)


def define_string_resource():
    return ResourceDefinition(
        resource_fn=lambda info: info.config,
        config_field=types.Field(types.String),
    )


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
def make_tempfile_manager():
    manager = TempfileManager()
    try:
        yield manager
    finally:
        manager.close()


def _tempfile_resource_fn(info):
    with make_tempfile_manager() as manager:
        yield manager


def define_tempfile_resource():
    return ResourceDefinition(resource_fn=_tempfile_resource_fn)


RedshiftConfigData = types.ConfigDictionary(
    'RedshiftConfigData',
    {
        'redshift_username': types.Field(types.String),
        'redshift_password': types.Field(types.String),
        'redshift_hostname': types.Field(types.String),
        'redshift_db_name': types.Field(types.String),
    },
)

test_context = PipelineContextDefinition(
    context_fn= lambda info: ExecutionContext.console_logging(log_level=logging.DEBUG),
    resources={
        'spark': define_lambda_resource(create_spark_session_local),
        's3': define_lambda_resource(create_s3_session),
        'db_url': ResourceDefinition(
            resource_fn=lambda info: create_redshift_db_url(
                info.config['redshift_username'],
                info.config['redshift_password'],
                info.config['redshift_hostname'],
                info.config['redshift_db_name'],
            ),
            config_field=types.Field(RedshiftConfigData),
        ),
        'db_engine': ResourceDefinition(
            resource_fn=lambda info: create_redshift_engine(
                create_redshift_db_url(
                    info.config['redshift_username'],
                    info.config['redshift_password'],
                    info.config['redshift_hostname'],
                    info.config['redshift_db_name'],
                )
            ),
            config_field=types.Field(RedshiftConfigData),
        ),
        'db_dialect' : define_string_resource(),
        'redshift_s3_temp_dir' : define_string_resource(),
        'db_load': define_value_resource(_db_load),
        'tempfile': define_tempfile_resource(),
    },
)

PostgresConfigData = types.ConfigDictionary(
    'PostgresConfigData',
    {
        'postgres_username': types.Field(types.String),
        'postgres_password': types.Field(types.String),
        'postgres_hostname': types.Field(types.String),
        'postgres_db_name': types.Field(types.String),
    },
)

local_context = PipelineContextDefinition(
    context_fn=lambda info: ExecutionContext.console_logging(log_level=logging.DEBUG),
    resources={
        'spark': define_lambda_resource(create_spark_session_local),
        's3': define_lambda_resource(create_s3_session),
        'db_url': ResourceDefinition(
            resource_fn=lambda info: create_postgres_db_url(
                info.config['postgres_username'],
                info.config['postgres_password'],
                info.config['postgres_hostname'],
                info.config['postgres_db_name'],
            ),
            config_field=types.Field(PostgresConfigData),
        ),
        'db_engine': ResourceDefinition(
            resource_fn=lambda info: create_postgres_engine(
                create_postgres_db_url(
                    info.config['postgres_username'],
                    info.config['postgres_password'],
                    info.config['postgres_hostname'],
                    info.config['postgres_db_name'],
                )
            ),
            config_field=types.Field(PostgresConfigData),
        ),
        'db_dialect' : define_string_resource(),
        'redshift_s3_temp_dir' : define_value_resource(''),
        'db_load': define_value_resource(_db_load),
        'tempfile': define_tempfile_resource(),
    },
)


cloud_context = PipelineContextDefinition(
    context_fn=lambda info: ExecutionContext.console_logging(log_level=logging.DEBUG),
    resources={
        'spark': define_lambda_resource(create_spark_session_local), # FIXME
        's3': define_lambda_resource(create_s3_session()),
        'db_url': ResourceDefinition(
            resource_fn=lambda info: create_redshift_db_url(
                info.config['redshift_username'],
                info.config['redshift_password'],
                info.config['redshift_hostname'],
                info.config['redshift_db_name'],
            ),
            config_field=types.Field(RedshiftConfigData),
        ),
        'db_engine': ResourceDefinition(
            resource_fn=lambda info: create_redshift_engine(
                create_redshift_db_url(
                    info.config['redshift_username'],
                    info.config['redshift_password'],
                    info.config['redshift_hostname'],
                    info.config['redshift_db_name'],
                    jdbc=False,
                ),
            ),
            config_field=types.Field(RedshiftConfigData),
        ),
        'db_dialect' : define_string_resource(),
        'redshift_s3_temp_dir' : define_string_resource(),
        'db_load': define_value_resource(_db_load),
        'tempfile': define_tempfile_resource(),
    },
)

CONTEXT_DEFINITIONS = {
    'test': test_context,
    'local': local_context,
    'cloud': cloud_context,
}


def define_airline_demo_download_pipeline():
    solids = [
        download_and_unzip_files_from_s3,
    ]
    return PipelineDefinition(
        name='airline_demo_download_pipeline',
        context_definitions=CONTEXT_DEFINITIONS,
        solids=solids,
    )


def define_airline_demo_ingest_pipeline():
    solids = [
        canonicalize_column_names,
        ingest_csv_to_spark,
        join_spark_data_frames,
        load_data_to_database_from_spark,
        normalize_weather_na_values,
        prefix_column_names,
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
        SolidInstance('prefix_column_names', alias='prefix_dest_cord_data'): {
            'data_frame': DependencyDefinition('ingest_master_cord_data')
        },
        SolidInstance('prefix_column_names', alias='prefix_origin_cord_data'): {
            'data_frame': DependencyDefinition('ingest_master_cord_data')
        },
        SolidInstance('join_spark_data_frames', alias='join_q2_on_time_data_to_dest_cord_data'): {
            'left_data_frame': DependencyDefinition('subsample_q2_on_time_data'),
            'right_data_frame': DependencyDefinition('prefix_dest_cord_data'),
        },
        SolidInstance('join_spark_data_frames', alias='join_q2_on_time_data_to_origin_cord_data'): {
            'left_data_frame': DependencyDefinition('join_q2_on_time_data_to_dest_cord_data'),
            'right_data_frame': DependencyDefinition('prefix_origin_cord_data'),
        },
        SolidInstance('canonicalize_column_names', alias='canonicalize_q2_on_time_data'): {
            'data_frame': DependencyDefinition('join_q2_on_time_data_to_origin_cord_data'),
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
        context_definitions=CONTEXT_DEFINITIONS,
    )


def define_airline_demo_warehouse_pipeline():
    return PipelineDefinition(
        name="airline_demo_warehouse_pipeline",
        solids=[
            average_sfo_outbound_avg_delays_by_destination,
            delays_by_geography,
            delays_vs_fares,
            delays_vs_fares_nb,
            eastbound_delays,
            q2_sfo_outbound_flights,
            sfo_delays_by_destination,
            thunk,
            tickets_with_destination,
            upload_to_s3,
            westbound_delays,
        ],
        dependencies={
            SolidInstance('thunk', alias='db_url'): {},
            'q2_sfo_outbound_flights': {},
            'tickets_with_destination': {},
            'westbound_delays': {},
            'eastbound_delays': {},
            'average_sfo_outbound_avg_delays_by_destination': {
                'q2_sfo_outbound_flights': DependencyDefinition('q2_sfo_outbound_flights'),
            },
            'delays_vs_fares': {
                'tickets_with_destination':
                DependencyDefinition('tickets_with_destination'),
                'average_sfo_outbound_avg_delays_by_destination':
                DependencyDefinition('average_sfo_outbound_avg_delays_by_destination')
            },
            'fares_vs___delays': {
                'db_url': DependencyDefinition('db_url'),
                'table_name': DependencyDefinition('delays_vs_fares'),
            },
            's_f_o__delays_by__destination': {
                'db_url': DependencyDefinition('db_url'),
                'table_name':
                DependencyDefinition('average_sfo_outbound_avg_delays_by_destination'),
            },
            'delays_by__geography': {
                'db_url': DependencyDefinition('db_url'),
                'eastbound_delays': DependencyDefinition('eastbound_delays'),
                'westbound_delays': DependencyDefinition('westbound_delays'),
            },
            SolidInstance('upload_to_s3', alias='upload_outbound_avg_delay_pdf_plots'): {
                'file_path': DependencyDefinition('s_f_o__delays_by__destination'),
            },
            SolidInstance('upload_to_s3', alias='upload_delays_vs_fares_pdf_plots'): {
                'file_path': DependencyDefinition('fares_vs___delays'),
            },
            SolidInstance('upload_to_s3', alias='upload_delays_by_geography_pdf_plots'): {
                'file_path': DependencyDefinition('delays_by__geography'),
            },
        },
        context_definitions=CONTEXT_DEFINITIONS,
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
