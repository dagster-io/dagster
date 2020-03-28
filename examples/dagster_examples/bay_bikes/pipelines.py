from dagster import ModeDefinition, PresetDefinition, file_relative_path, pipeline

from ..common.resources import postgres_db_info_resource
from .resources import credentials_vault, gcs_client, local_client, mount
from .solids import train_daily_bike_supply_model, trip_etl, weather_etl

MODES = [
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
]

WEATHER_INGEST_PRESETS = [
    PresetDefinition.from_files(
        'dev_weather_etl',
        mode='development',
        environment_files=[
            file_relative_path(__file__, 'environments/dev_credentials_vault.yaml'),
            file_relative_path(__file__, 'environments/dev_database_resources.yaml'),
            file_relative_path(__file__, 'environments/file_system_resources.yaml'),
            file_relative_path(__file__, 'environments/weather.yaml'),
        ],
        solid_subset=['weather_etl'],
    ),
    PresetDefinition.from_files(
        'prod_weather_etl',
        mode='production',
        environment_files=[
            file_relative_path(__file__, 'environments/prod_credentials_vault.yaml'),
            file_relative_path(__file__, 'environments/prod_database_resources.yaml'),
            file_relative_path(__file__, 'environments/file_system_resources.yaml'),
            file_relative_path(__file__, 'environments/weather.yaml'),
        ],
        solid_subset=['weather_etl'],
    ),
]

TRIP_INGEST_PRESETS = [
    PresetDefinition.from_files(
        'dev_trip_etl',
        mode='development',
        environment_files=[
            file_relative_path(__file__, 'environments/dev_credentials_vault.yaml'),
            file_relative_path(__file__, 'environments/dev_database_resources.yaml'),
            file_relative_path(__file__, 'environments/file_system_resources.yaml'),
            file_relative_path(__file__, 'environments/trips.yaml'),
        ],
        solid_subset=['trip_etl'],
    ),
    PresetDefinition.from_files(
        'prod_trip_etl',
        mode='production',
        environment_files=[
            file_relative_path(__file__, 'environments/prod_credentials_vault.yaml'),
            file_relative_path(__file__, 'environments/prod_database_resources.yaml'),
            file_relative_path(__file__, 'environments/file_system_resources.yaml'),
            file_relative_path(__file__, 'environments/trips.yaml'),
        ],
        solid_subset=['trip_etl'],
    ),
]

TRAINING_PRESETS = [
    PresetDefinition.from_files(
        'dev_train_daily_bike_supply_model',
        mode='development',
        environment_files=[
            file_relative_path(__file__, 'environments/dev_credentials_vault.yaml'),
            file_relative_path(__file__, 'environments/dev_database_resources.yaml'),
            file_relative_path(__file__, 'environments/file_system_resources.yaml'),
            file_relative_path(__file__, 'environments/training.yaml'),
        ],
        solid_subset=['train_daily_bike_supply_model'],
    ),
    PresetDefinition.from_files(
        'prod_train_daily_bike_supply_model',
        mode='production',
        environment_files=[
            file_relative_path(__file__, 'environments/prod_credentials_vault.yaml'),
            file_relative_path(__file__, 'environments/prod_database_resources.yaml'),
            file_relative_path(__file__, 'environments/file_system_resources.yaml'),
            file_relative_path(__file__, 'environments/training.yaml'),
        ],
        solid_subset=['train_daily_bike_supply_model'],
    ),
]


@pipeline(
    mode_defs=MODES, preset_defs=WEATHER_INGEST_PRESETS + TRIP_INGEST_PRESETS + TRAINING_PRESETS,
)
def generate_training_set_and_train_model():
    return train_daily_bike_supply_model(weather_etl(), trip_etl())


@pipeline(
    mode_defs=MODES, preset_defs=WEATHER_INGEST_PRESETS,
)
def daily_weather_pipeline():
    return weather_etl()
