from dagster import ModeDefinition, PresetDefinition, file_relative_path, pipeline

from ..common.resources import postgres_db_info_resource
from .resources import credentials_vault, gcs_client, local_client, mount
from .solids import train_daily_bike_supply_model, trip_etl, weather_etl


@pipeline(
    mode_defs=[
        ModeDefinition(
            name='development',
            resource_defs={
                'postgres_db': postgres_db_info_resource,
                'gcs_client': local_client,
                'credentials_vault': credentials_vault,
                'volume': mount,
            },
            description='Mode to be used during local demo.',
        ),
        ModeDefinition(
            name='production',
            resource_defs={
                'postgres_db': postgres_db_info_resource,
                'gcs_client': gcs_client,
                'credentials_vault': credentials_vault,
                'volume': mount,
            },
            description='Mode to be used on a remote production server',
        ),
    ],
    preset_defs=[
        PresetDefinition.from_files(
            'train_daily_bike_supply_model',
            mode='development',
            environment_files=[
                file_relative_path(__file__, 'environments/dev_database_resources.yaml'),
                file_relative_path(__file__, 'environments/dev_file_system_resources.yaml'),
                file_relative_path(__file__, 'environments/credentials_vault.yaml'),
                file_relative_path(__file__, 'environments/training.yaml'),
            ],
            solid_subset=['train_daily_bike_supply_model'],
        ),
        PresetDefinition.from_files(
            'weather_etl',
            mode='development',
            environment_files=[
                file_relative_path(__file__, 'environments/dev_database_resources.yaml'),
                file_relative_path(__file__, 'environments/credentials_vault.yaml'),
                file_relative_path(__file__, 'environments/dev_file_system_resources.yaml'),
                file_relative_path(__file__, 'environments/weather.yaml'),
            ],
            solid_subset=['weather_etl'],
        ),
        PresetDefinition.from_files(
            'trip_etl',
            mode='development',
            environment_files=[
                file_relative_path(__file__, 'environments/dev_database_resources.yaml'),
                file_relative_path(__file__, 'environments/credentials_vault.yaml'),
                file_relative_path(__file__, 'environments/dev_file_system_resources.yaml'),
                file_relative_path(__file__, 'environments/trips.yaml'),
            ],
            solid_subset=['trip_etl'],
        ),
    ],
)
def generate_training_set_and_train_model():
    return train_daily_bike_supply_model(weather_etl(), trip_etl())


@pipeline(
    mode_defs=[
        ModeDefinition(
            name='development',
            resource_defs={
                'postgres_db': postgres_db_info_resource,
                'gcs_client': local_client,
                'credentials_vault': credentials_vault,
                'volume': mount,
            },
            description='Mode to be used during local demo.',
        )
    ],
    preset_defs=[
        PresetDefinition.from_files(
            'weather_etl',
            mode='development',
            environment_files=[
                file_relative_path(__file__, 'environments/dev_database_resources.yaml'),
                file_relative_path(__file__, 'environments/credentials_vault.yaml'),
                file_relative_path(__file__, 'environments/dev_file_system_resources.yaml'),
                file_relative_path(__file__, 'environments/weather.yaml'),
            ],
        )
    ],
)
def daily_weather_pipeline():
    return weather_etl()
