from dagster import ModeDefinition, PresetDefinition, file_relative_path, pipeline

from .resources import (
    credentials_vault,
    local_transporter,
    mount,
    production_transporter,
    temporary_directory_mount,
)
from .solids import (
    download_weather_report_from_weather_api,
    produce_training_set,
    produce_trip_dataset,
    produce_weather_dataset,
    train_lstm_model,
    transform_into_traffic_dataset,
    upload_file_to_bucket,
)


@pipeline(
    mode_defs=[
        ModeDefinition(
            name='local',
            resource_defs={
                'credentials_vault': credentials_vault,
                'transporter': local_transporter,
                'volume': temporary_directory_mount,
            },
        ),
        ModeDefinition(
            name='production',
            resource_defs={
                'credentials_vault': credentials_vault,
                'transporter': production_transporter,
                'volume': mount,
            },
        ),
    ],
    preset_defs=[
        PresetDefinition.from_files(
            'dev',
            mode='local',
            environment_files=[
                file_relative_path(__file__, 'environments/weather_base.yaml'),
                file_relative_path(__file__, 'environments/weather_dev.yaml'),
            ],
        ),
        PresetDefinition.from_files(
            'production',
            mode='production',
            environment_files=[
                file_relative_path(__file__, 'environments/weather_base.yaml'),
                file_relative_path(__file__, 'environments/weather_production.yaml'),
            ],
        ),
    ],
)
def extract_daily_weather_data_pipeline():
    upload_weather_report = upload_file_to_bucket.alias('upload_weather_report')
    upload_weather_report(download_weather_report_from_weather_api())


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
