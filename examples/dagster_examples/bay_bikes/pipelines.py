from dagster import ModeDefinition, PresetDefinition, file_relative_path, pipeline

from ..common.resources import postgres_db_info_resource
from .resources import credentials_vault, gcs_client, local_client, mount
from .solids import (
    compose_training_data,
    download_weather_report_from_weather_api,
    download_zipfile_from_url,
    insert_into_table,
    load_compressed_csv_file,
    train_lstm_model,
)


@pipeline(
    mode_defs=[
        ModeDefinition(
            name='development',
            resource_defs={
                'credentials_vault': credentials_vault,
                'postgres_db': postgres_db_info_resource,
            },
        ),
    ],
    preset_defs=[
        PresetDefinition.from_files(
            'development',
            mode='development',
            environment_files=[
                file_relative_path(__file__, 'environments/dev_database_resources.yaml'),
                file_relative_path(__file__, 'environments/weather.yaml'),
            ],
        ),
    ],
)
def extract_daily_weather_data_pipeline():
    insert_weather_report_into_table = insert_into_table.alias('insert_weather_report_into_table')
    insert_weather_report_into_table(download_weather_report_from_weather_api())


@pipeline(
    mode_defs=[
        ModeDefinition(
            name='development',
            resource_defs={'volume': mount, 'postgres_db': postgres_db_info_resource,},
        )
    ],
    preset_defs=[
        PresetDefinition.from_files(
            'development',
            mode='development',
            environment_files=[
                file_relative_path(__file__, 'environments/dev_database_resources.yaml'),
                file_relative_path(__file__, 'environments/dev_file_system_resources.yaml'),
                file_relative_path(__file__, 'environments/trips.yaml'),
            ],
        ),
    ],
)
def monthly_trip_pipeline():
    download_baybike_zipfile_from_url = download_zipfile_from_url.alias(
        'download_baybike_zipfile_from_url'
    )
    insert_trip_data_into_table = insert_into_table.alias('insert_trip_data_into_table')
    load_baybike_data_into_dataframe = load_compressed_csv_file.alias(
        'load_baybike_data_into_dataframe'
    )
    return insert_trip_data_into_table(
        load_baybike_data_into_dataframe(download_baybike_zipfile_from_url())
    )


@pipeline(
    mode_defs=[
        ModeDefinition(
            name='development',
            resource_defs={'postgres_db': postgres_db_info_resource, 'gcs_client': local_client},
            description='Mode to be used during local demo.',
        ),
        ModeDefinition(
            name='production',
            resource_defs={'postgres_db': postgres_db_info_resource, 'gcs_client': gcs_client},
            description='Mode to be used on a remote production server',
        ),
    ],
    preset_defs=[
        PresetDefinition.from_files(
            'development',
            mode='development',
            environment_files=[
                file_relative_path(__file__, 'environments/dev_database_resources.yaml'),
                file_relative_path(__file__, 'environments/training.yaml'),
            ],
        ),
    ],
)
def generate_training_set_and_train_model():
    train_lstm_model(compose_training_data())
