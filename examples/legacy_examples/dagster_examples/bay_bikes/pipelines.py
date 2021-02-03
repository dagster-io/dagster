from dagster import ModeDefinition, PresetDefinition, pipeline

from ..common.resources import postgres_db_info_resource
from .resources import credentials_vault, gcs_client, local_client, mount
from .solids import train_daily_bike_supply_model, trip_etl, weather_etl

MODES = [
    ModeDefinition(
        name="development",
        resource_defs={
            "postgres_db": postgres_db_info_resource,
            "gcs_client": local_client,
            "credentials_vault": credentials_vault,
            "volume": mount,
        },
        description="Mode to be used during local demo.",
    ),
    ModeDefinition(
        name="production",
        resource_defs={
            "postgres_db": postgres_db_info_resource,
            "gcs_client": gcs_client,
            "credentials_vault": credentials_vault,
            "volume": mount,
        },
        description="Mode to be used on a remote production server",
    ),
]

WEATHER_INGEST_PRESETS = [
    PresetDefinition.from_pkg_resources(
        "dev_weather_etl",
        mode="development",
        pkg_resource_defs=[
            ("dagster_examples.bay_bikes.environments", "dev_credentials_vault.yaml"),
            ("dagster_examples.bay_bikes.environments", "dev_database_resources.yaml"),
            ("dagster_examples.bay_bikes.environments", "file_system_resources.yaml"),
            ("dagster_examples.bay_bikes.environments", "weather.yaml"),
        ],
        solid_selection=["weather_etl"],
    ),
    PresetDefinition.from_pkg_resources(
        "prod_weather_etl",
        mode="production",
        pkg_resource_defs=[
            ("dagster_examples.bay_bikes.environments", "prod_credentials_vault.yaml"),
            ("dagster_examples.bay_bikes.environments", "prod_database_resources.yaml"),
            ("dagster_examples.bay_bikes.environments", "file_system_resources.yaml"),
            ("dagster_examples.bay_bikes.environments", "weather.yaml"),
        ],
        solid_selection=["weather_etl"],
    ),
]

TRIP_INGEST_PRESETS = [
    PresetDefinition.from_pkg_resources(
        "dev_trip_etl",
        mode="development",
        pkg_resource_defs=[
            ("dagster_examples.bay_bikes.environments", "dev_credentials_vault.yaml"),
            ("dagster_examples.bay_bikes.environments", "dev_database_resources.yaml"),
            ("dagster_examples.bay_bikes.environments", "file_system_resources.yaml"),
            ("dagster_examples.bay_bikes.environments", "trips.yaml"),
        ],
        solid_selection=["trip_etl"],
    ),
    PresetDefinition.from_pkg_resources(
        "prod_trip_etl",
        mode="production",
        pkg_resource_defs=[
            ("dagster_examples.bay_bikes.environments", "prod_credentials_vault.yaml"),
            ("dagster_examples.bay_bikes.environments", "prod_database_resources.yaml"),
            ("dagster_examples.bay_bikes.environments", "file_system_resources.yaml"),
            ("dagster_examples.bay_bikes.environments", "trips.yaml"),
        ],
        solid_selection=["trip_etl"],
    ),
]

TRAINING_PRESETS = [
    PresetDefinition.from_pkg_resources(
        "dev_train_daily_bike_supply_model",
        mode="development",
        pkg_resource_defs=[
            ("dagster_examples.bay_bikes.environments", "dev_credentials_vault.yaml"),
            ("dagster_examples.bay_bikes.environments", "dev_database_resources.yaml"),
            ("dagster_examples.bay_bikes.environments", "file_system_resources.yaml"),
            ("dagster_examples.bay_bikes.environments", "training.yaml"),
        ],
        solid_selection=["train_daily_bike_supply_model"],
    ),
    PresetDefinition.from_pkg_resources(
        "prod_train_daily_bike_supply_model",
        mode="production",
        pkg_resource_defs=[
            ("dagster_examples.bay_bikes.environments", "prod_credentials_vault.yaml"),
            ("dagster_examples.bay_bikes.environments", "prod_database_resources.yaml"),
            ("dagster_examples.bay_bikes.environments", "file_system_resources.yaml"),
            ("dagster_examples.bay_bikes.environments", "training.yaml"),
        ],
        solid_selection=["train_daily_bike_supply_model"],
    ),
]


@pipeline(
    mode_defs=MODES,
    preset_defs=WEATHER_INGEST_PRESETS + TRIP_INGEST_PRESETS + TRAINING_PRESETS,
)
def generate_training_set_and_train_model():
    train_daily_bike_supply_model(weather_etl(), trip_etl())


@pipeline(
    mode_defs=MODES,
    preset_defs=WEATHER_INGEST_PRESETS,
)
def daily_weather_pipeline():
    weather_etl()
