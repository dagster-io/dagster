"""Pipeline definitions for the airline_demo."""

from dagster import (
    CompositeSolidDefinition,
    DependencyDefinition,
    ModeDefinition,
    PipelineDefinition,
    PresetDefinition,
    SolidInstance,
    file_relative_path,
)

from dagster_aws.s3.resources import s3_resource
from dagster_aws.s3.solids import put_object_to_s3_bytes, download_from_s3_to_bytes

from .resources import (
    postgres_db_info_resource,
    redshift_db_info_resource,
    spark_session_local,
    tempfile_resource,
)
from .solids import (
    average_sfo_outbound_avg_delays_by_destination,
    delays_by_geography,
    delays_vs_fares,
    delays_vs_fares_nb,
    eastbound_delays,
    ingest_csv_to_spark,
    load_data_to_database_from_spark,
    join_q2_data,
    process_sfo_weather_data,
    q2_sfo_outbound_flights,
    sfo_delays_by_destination,
    tickets_with_destination,
    westbound_delays,
    s3_to_dw_table,
    s3_to_df,
)


test_mode = ModeDefinition(
    name='test',
    resources={
        'spark': spark_session_local,
        'db_info': redshift_db_info_resource,
        'tempfile': tempfile_resource,
        's3': s3_resource,
    },
)


local_mode = ModeDefinition(
    name='local',
    resources={
        'spark': spark_session_local,
        's3': s3_resource,
        'db_info': postgres_db_info_resource,
        'tempfile': tempfile_resource,
    },
)


prod_mode = ModeDefinition(
    name='prod',
    resources={
        'spark': spark_session_local,  # FIXME
        's3': s3_resource,
        'db_info': redshift_db_info_resource,
        'tempfile': tempfile_resource,
    },
)

process_on_time_data = CompositeSolidDefinition(
    name='process_on_time_data',
    solids=[s3_to_df, join_q2_data, load_data_to_database_from_spark],
    dependencies={
        SolidInstance('s3_to_df', alias='april_on_time_s3_to_df'): {},
        SolidInstance('s3_to_df', alias='may_on_time_s3_to_df'): {},
        SolidInstance('s3_to_df', alias='june_on_time_s3_to_df'): {},
        SolidInstance('s3_to_df', alias='master_cord_s3_to_df'): {},
        'join_q2_data': {
            'april_data': DependencyDefinition('april_on_time_s3_to_df'),
            'may_data': DependencyDefinition('may_on_time_s3_to_df'),
            'june_data': DependencyDefinition('june_on_time_s3_to_df'),
            'master_cord_data': DependencyDefinition('master_cord_s3_to_df'),
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_on_time_data'): {
            'data_frame': DependencyDefinition('join_q2_data')
        },
    },
)


def define_airline_demo_ingest_pipeline():
    solids = [
        download_from_s3_to_bytes,
        ingest_csv_to_spark,
        load_data_to_database_from_spark,
        process_on_time_data,
        process_sfo_weather_data,
        s3_to_dw_table,
    ]
    dependencies = {
        SolidInstance('s3_to_dw_table', alias='process_q2_coupon_data'): {},
        SolidInstance('s3_to_dw_table', alias='process_q2_market_data'): {},
        SolidInstance('s3_to_dw_table', alias='process_q2_ticket_data'): {},
        SolidInstance('download_from_s3_to_bytes', alias='download_q2_sfo_weather'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_sfo_weather'): {
            'input_csv_file': DependencyDefinition('download_q2_sfo_weather')
        },
        'process_sfo_weather_data': {
            'sfo_weather_data': DependencyDefinition('ingest_q2_sfo_weather')
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_sfo_weather'): {
            'data_frame': DependencyDefinition('process_sfo_weather_data')
        },
    }

    return PipelineDefinition(
        name="airline_demo_ingest_pipeline",
        solids=solids,
        dependencies=dependencies,
        mode_definitions=[test_mode, local_mode, prod_mode],
        preset_definitions=[
            PresetDefinition(
                name='local_fast',
                mode='local',
                environment_files=[
                    file_relative_path(__file__, 'environments/local_base.yaml'),
                    file_relative_path(__file__, 'environments/local_fast_ingest.yaml'),
                ],
            ),
            PresetDefinition(
                name='local_full',
                mode='local',
                environment_files=[
                    file_relative_path(__file__, 'environments/local_base.yaml'),
                    file_relative_path(__file__, 'environments/local_full_ingest.yaml'),
                ],
            ),
        ],
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
            tickets_with_destination,
            put_object_to_s3_bytes,
            westbound_delays,
        ],
        dependencies={
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
            'fares_vs_delays': {'table_name': DependencyDefinition('delays_vs_fares')},
            'sfo_delays_by_destination': {
                'table_name': DependencyDefinition('average_sfo_outbound_avg_delays_by_destination')
            },
            'delays_by_geography': {
                'eastbound_delays': DependencyDefinition('eastbound_delays'),
                'westbound_delays': DependencyDefinition('westbound_delays'),
            },
            SolidInstance('put_object_to_s3_bytes', alias='upload_outbound_avg_delay_pdf_plots'): {
                'file_obj': DependencyDefinition('sfo_delays_by_destination')
            },
            SolidInstance('put_object_to_s3_bytes', alias='upload_delays_vs_fares_pdf_plots'): {
                'file_obj': DependencyDefinition('fares_vs_delays')
            },
            SolidInstance('put_object_to_s3_bytes', alias='upload_delays_by_geography_pdf_plots'): {
                'file_obj': DependencyDefinition('delays_by_geography')
            },
        },
        mode_definitions=[test_mode, local_mode, prod_mode],
        preset_definitions=[
            PresetDefinition(
                name='local',
                mode='local',
                environment_files=[
                    file_relative_path(__file__, 'environments/local_base.yaml'),
                    file_relative_path(__file__, 'environments/local_warehouse.yaml'),
                ],
            )
        ],
    )
