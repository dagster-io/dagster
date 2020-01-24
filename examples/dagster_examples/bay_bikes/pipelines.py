from dagster import ModeDefinition, PresetDefinition, file_relative_path, pipeline

from ..common.resources import postgres_db_info_resource
from .resources import credentials_vault, mount, production_transporter
from .solids import (
    download_weather_report_from_weather_api,
    insert_row_into_table,
    produce_training_set,
    produce_trip_dataset,
    produce_weather_dataset,
    train_lstm_model,
    transform_into_traffic_dataset,
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
                file_relative_path(__file__, 'environments/dev_resources.yaml'),
                file_relative_path(__file__, 'environments/weather.yaml'),
            ],
        ),
    ],
)
def extract_daily_weather_data_pipeline():
    insert_weather_report_into_table = insert_row_into_table.alias(
        'insert_weather_report_into_table'
    )
    insert_weather_report_into_table(download_weather_report_from_weather_api())


# TODO: Add Local Mode when tests are written
@pipeline(
    mode_defs=[
        ModeDefinition(
            name='production',
            resource_defs={'transporter': production_transporter, 'volume': mount},
        ),
    ],
    preset_defs=[
        PresetDefinition.from_files(
            'production',
            mode='production',
            environment_files=[
                file_relative_path(__file__, 'environments/feature_transformation_base.yaml'),
                file_relative_path(__file__, 'environments/feature_transformation_production.yaml'),
            ],
        ),
    ],
)
def model_training_pipeline():
    train_lstm_model(
        produce_training_set(
            transform_into_traffic_dataset(produce_trip_dataset()), produce_weather_dataset(),
        )
    )
