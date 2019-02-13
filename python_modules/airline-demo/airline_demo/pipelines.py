"""Pipeline definitions for the airline_demo."""
from collections import namedtuple
import contextlib
import logging
import os
import shutil
import tempfile

from dagster import (
    DependencyDefinition,
    Dict,
    ExecutionContext,
    Field,
    PipelineContextDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    ResourceDefinition,
    SolidInstance,
    String,
)

from .solids import (
    average_sfo_outbound_avg_delays_by_destination,
    canonicalize_column_names,
    delays_by_geography,
    delays_vs_fares,
    delays_vs_fares_nb,
    download_from_s3,
    eastbound_delays,
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
    unzip_file,
    upload_to_s3,
    westbound_delays,
)

from .utils import (
    create_postgres_db_url,
    create_postgres_engine,
    create_redshift_db_url,
    create_redshift_engine,
    create_s3_session,
    create_spark_session_local,
)


def define_lambda_resource(func, *args, **kwargs):
    return ResourceDefinition(lambda _init_context: func(*args, **kwargs))


def define_value_resource(value):
    return ResourceDefinition(lambda _init_context: value)


def define_none_resource():
    return define_value_resource(None)


def define_string_resource():
    return ResourceDefinition(
        resource_fn=lambda init_context: init_context.resource_config, config_field=Field(String)
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


def _tempfile_resource_fn(_info):
    with make_tempfile_manager() as manager:
        yield manager


def define_tempfile_resource():
    return ResourceDefinition(resource_fn=_tempfile_resource_fn)


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


def define_redshift_db_info_resource():
    def _create_redshift_db_info(init_context):
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

    return ResourceDefinition(
        resource_fn=_create_redshift_db_info, config_field=Field(RedshiftConfigData)
    )


def define_postgres_db_info_resource():
    def _create_postgres_db_info(init_context):
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

    return ResourceDefinition(
        resource_fn=_create_postgres_db_info, config_field=Field(PostgresConfigData)
    )


test_context = PipelineContextDefinition(
    context_fn=lambda _: ExecutionContext.console_logging(log_level=logging.DEBUG),
    resources={
        'spark': define_lambda_resource(create_spark_session_local),
        's3': define_lambda_resource(create_s3_session, signed=False),
        'db_info': define_redshift_db_info_resource(),
        'tempfile': define_tempfile_resource(),
    },
)

PostgresConfigData = Dict(
    {
        'postgres_username': Field(String),
        'postgres_password': Field(String),
        'postgres_hostname': Field(String),
        'postgres_db_name': Field(String),
    }
)

local_context = PipelineContextDefinition(
    context_fn=lambda _: ExecutionContext.console_logging(log_level=logging.DEBUG),
    resources={
        'spark': define_lambda_resource(create_spark_session_local),
        's3': define_lambda_resource(create_s3_session, signed=False),
        'db_info': define_postgres_db_info_resource(),
        'tempfile': define_tempfile_resource(),
    },
)

prod_context = PipelineContextDefinition(
    context_fn=lambda _: ExecutionContext.console_logging(log_level=logging.DEBUG),
    resources={
        'spark': define_lambda_resource(create_spark_session_local),  # FIXME
        's3': define_lambda_resource(create_s3_session(), signed=False),
        'db_info': define_redshift_db_info_resource(),
        'tempfile': define_tempfile_resource(),
    },
)

CONTEXT_DEFINITIONS = {'test': test_context, 'local': local_context, 'prod': prod_context}


def define_airline_demo_download_pipeline():
    solids = [download_from_s3, unzip_file]
    dependencies = {
        SolidInstance('download_from_s3', alias='download_archives'): {},
        SolidInstance('unzip_file', alias='unzip_archives'): {
            'archive_paths': DependencyDefinition('download_archives')
        },
        SolidInstance('download_from_s3', alias='download_q2_sfo_weather'): {},
    }

    return PipelineDefinition(
        name='airline_demo_download_pipeline',
        context_definitions=CONTEXT_DEFINITIONS,
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
        prefix_column_names,
        subsample_spark_dataset,
        union_spark_data_frames,
    ]
    dependencies = {
        SolidInstance('ingest_csv_to_spark', alias='ingest_april_on_time_data'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_may_on_time_data'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_june_on_time_data'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_sfo_weather'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_coupon_data'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_market_data'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_ticket_data'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_master_cord_data'): {},
        SolidInstance('union_spark_data_frames', alias='combine_april_may_on_time_data'): {
            'left_data_frame': DependencyDefinition('ingest_april_on_time_data'),
            'right_data_frame': DependencyDefinition('ingest_may_on_time_data'),
        },
        SolidInstance('union_spark_data_frames', alias='combine_q2_on_time_data'): {
            'left_data_frame': DependencyDefinition('combine_april_may_on_time_data'),
            'right_data_frame': DependencyDefinition('ingest_june_on_time_data'),
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_q2_on_time_data'): {
            'data_frame': DependencyDefinition('combine_q2_on_time_data')
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_q2_ticket_data'): {
            'data_frame': DependencyDefinition('ingest_q2_ticket_data')
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_q2_market_data'): {
            'data_frame': DependencyDefinition('ingest_q2_market_data')
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_q2_coupon_data'): {
            'data_frame': DependencyDefinition('ingest_q2_coupon_data')
        },
        SolidInstance('normalize_weather_na_values', alias='normalize_q2_weather_na_values'): {
            'data_frame': DependencyDefinition('ingest_q2_sfo_weather')
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
            'data_frame': DependencyDefinition('join_q2_on_time_data_to_origin_cord_data')
        },
        SolidInstance('canonicalize_column_names', alias='canonicalize_q2_coupon_data'): {
            'data_frame': DependencyDefinition('subsample_q2_coupon_data')
        },
        SolidInstance('canonicalize_column_names', alias='canonicalize_q2_market_data'): {
            'data_frame': DependencyDefinition('subsample_q2_market_data')
        },
        SolidInstance('canonicalize_column_names', alias='canonicalize_q2_ticket_data'): {
            'data_frame': DependencyDefinition('subsample_q2_ticket_data')
        },
        SolidInstance('canonicalize_column_names', alias='canonicalize_q2_sfo_weather'): {
            'data_frame': DependencyDefinition('normalize_q2_weather_na_values')
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_on_time_data'): {
            'data_frame': DependencyDefinition('canonicalize_q2_on_time_data')
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_coupon_data'): {
            'data_frame': DependencyDefinition('canonicalize_q2_coupon_data')
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_market_data'): {
            'data_frame': DependencyDefinition('canonicalize_q2_market_data')
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_ticket_data'): {
            'data_frame': DependencyDefinition('canonicalize_q2_ticket_data')
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_sfo_weather'): {
            'data_frame': DependencyDefinition('canonicalize_q2_sfo_weather')
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
                'q2_sfo_outbound_flights': DependencyDefinition('q2_sfo_outbound_flights')
            },
            'delays_vs_fares': {
                'tickets_with_destination': DependencyDefinition('tickets_with_destination'),
                'average_sfo_outbound_avg_delays_by_destination': DependencyDefinition(
                    'average_sfo_outbound_avg_delays_by_destination'
                ),
            },
            'fares_vs_delays': {
                'db_url': DependencyDefinition('db_url'),
                'table_name': DependencyDefinition('delays_vs_fares'),
            },
            'sfo_delays_by_destination': {
                'db_url': DependencyDefinition('db_url'),
                'table_name': DependencyDefinition(
                    'average_sfo_outbound_avg_delays_by_destination'
                ),
            },
            'delays_by_geo': {
                'db_url': DependencyDefinition('db_url'),
                'eastbound_delays': DependencyDefinition('eastbound_delays'),
                'westbound_delays': DependencyDefinition('westbound_delays'),
            },
            SolidInstance('upload_to_s3', alias='upload_outbound_avg_delay_pdf_plots'): {
                'file_path': DependencyDefinition('sfo_delays_by_destination')
            },
            SolidInstance('upload_to_s3', alias='upload_delays_vs_fares_pdf_plots'): {
                'file_path': DependencyDefinition('fares_vs_delays')
            },
            SolidInstance('upload_to_s3', alias='upload_delays_by_geography_pdf_plots'): {
                'file_path': DependencyDefinition('delays_by_geo')
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
        },
    )
