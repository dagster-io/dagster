"""Pipeline definitions for the airline_demo."""

from dagster import (
    ModeDefinition,
    OutputDefinition,
    PresetDefinition,
    String,
    composite_solid,
    pipeline,
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


@composite_solid(outputs=[OutputDefinition(name='table_name', dagster_type=String)])
def process_on_time_data(context):
    return load_data_to_database_from_spark.alias('load_q2_on_time_data')(
        data_frame=join_q2_data(
            context,
            april_data=s3_to_df.alias('april_on_time_s3_to_df')(),
            may_data=s3_to_df.alias('may_on_time_s3_to_df')(),
            june_data=s3_to_df.alias('june_on_time_s3_to_df')(),
            master_cord_data=s3_to_df.alias('master_cord_s3_to_df')(),
        )
    )


@composite_solid(outputs=[OutputDefinition(name='table_name', dagster_type=String)])
def sfo_weather_data(context):
    return load_data_to_database_from_spark.alias('load_q2_sfo_weather')(
        process_sfo_weather_data(
            context,
            ingest_csv_to_spark.alias('ingest_q2_sfo_weather')(
                download_from_s3_to_bytes.alias('download_q2_sfo_weather')()
            ),
        )
    )


@pipeline(
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
def airline_demo_ingest_pipeline(context):
    process_on_time_data(context)
    sfo_weather_data(context)
    for data_type in ['coupon', 'market', 'ticket']:
        s3_to_dw_table.alias('process_q2_{}_data'.format(data_type))(context)


def define_airline_demo_ingest_pipeline():
    return airline_demo_ingest_pipeline


@composite_solid(
    outputs=[
        OutputDefinition(name='bucket', dagster_type=String),
        OutputDefinition(name='key', dagster_type=String),
    ]
)
def process_delays_by_geo(_context):
    return put_object_to_s3_bytes.alias('upload_delays_by_geography_pdf_plots')(
        delays_by_geography(
            westbound_delays=westbound_delays(), eastbound_delays=eastbound_delays()
        )
    )


@pipeline(
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
def airline_demo_warehouse_pipeline(context):
    process_delays_by_geo(context)

    outbound_delays = average_sfo_outbound_avg_delays_by_destination(q2_sfo_outbound_flights())

    put_object_to_s3_bytes.alias('upload_delays_vs_fares_pdf_plots')(
        delays_vs_fares_nb.alias('fares_vs_delays')(
            delays_vs_fares(
                tickets_with_destination=tickets_with_destination(),
                average_sfo_outbound_avg_delays_by_destination=outbound_delays,
            )
        )
    )

    put_object_to_s3_bytes.alias('upload_outbound_avg_delay_pdf_plots')(
        sfo_delays_by_destination(outbound_delays)
    )


def define_airline_demo_warehouse_pipeline():
    return airline_demo_warehouse_pipeline
