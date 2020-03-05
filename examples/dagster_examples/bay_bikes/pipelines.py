from dagster import ModeDefinition, PresetDefinition, file_relative_path, pipeline

from ..common.resources import postgres_db_info_resource
from .resources import credentials_vault, gcs_client, local_client, mount
from .solids import (
    produce_training_set,
    produce_trip_dataset,
    produce_weather_dataset,
    train_lstm_model,
    transform_into_traffic_dataset,
    trip_etl,
    upload_pickled_object_to_gcs_bucket,
    weather_etl,
)


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
            'produce_trip_dataset* produce_weather_dataset*',
            mode='development',
            environment_files=[
                file_relative_path(__file__, 'environments/dev_database_resources.yaml'),
                file_relative_path(__file__, 'environments/dev_file_system_resources.yaml'),
                file_relative_path(__file__, 'environments/credentials_vault.yaml'),
                file_relative_path(__file__, 'environments/training.yaml'),
            ],
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
        ),
    ],
)
def generate_training_set_and_train_model():
    upload_training_set_to_gcs = upload_pickled_object_to_gcs_bucket.alias(
        'upload_training_set_to_gcs'
    )
    return train_lstm_model(
        upload_training_set_to_gcs(
            produce_training_set(
                transform_into_traffic_dataset(produce_trip_dataset(trip_etl())),
                produce_weather_dataset(weather_etl()),
            )
        )
    )
