from dagster import ModeDefinition, PresetDefinition, file_relative_path, pipeline

from .resources import (
    credentials_vault,
    local_transporter,
    mount,
    production_transporter,
    temporary_directory_mount,
)
from .solids import (
    consolidate_csv_files,
    download_weather_report_from_weather_api,
    download_zipfiles_from_urls,
    produce_training_set,
    produce_trip_dataset,
    produce_weather_dataset,
    train_lstm_model,
    transform_into_traffic_dataset,
    unzip_files,
    upload_file_to_bucket,
)


@pipeline(
    mode_defs=[
        ModeDefinition(
            name='local',
            resource_defs={'transporter': local_transporter, 'volume': temporary_directory_mount},
        ),
        ModeDefinition(
            name='production',
            resource_defs={'transporter': production_transporter, 'volume': mount},
        ),
    ],
    preset_defs=[
        PresetDefinition.from_files(
            'dev',
            mode='local',
            environment_files=[
                file_relative_path(__file__, 'environments/bay_bike_pipeline_base.yaml'),
                file_relative_path(__file__, 'environments/bay_bike_pipeline_dev.yaml'),
            ],
        ),
        PresetDefinition.from_files(
            'production',
            mode='production',
            environment_files=[
                file_relative_path(__file__, 'environments/bay_bike_pipeline_base.yaml'),
                file_relative_path(__file__, 'environments/bay_bike_pipeline_production.yaml'),
            ],
        ),
    ],
)
def extract_monthly_bay_bike_pipeline():
    upload_consolidated_csv = upload_file_to_bucket.alias('upload_consolidated_csv')
    upload_consolidated_csv(consolidate_csv_files(unzip_files(download_zipfiles_from_urls())))


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


@pipeline(
    mode_defs=[
        ModeDefinition(
            name='local',
            resource_defs={'transporter': local_transporter, 'volume': temporary_directory_mount},
        ),
        ModeDefinition(
            name='production',
            resource_defs={'transporter': production_transporter, 'volume': mount},
        ),
    ],
    preset_defs=[
        PresetDefinition.from_files(
            'dev',
            mode='local',
            environment_files=[
                file_relative_path(__file__, 'environments/feature_transformation_base.yaml'),
                file_relative_path(__file__, 'environments/feature_transformation_dev.yaml'),
            ],
        ),
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
