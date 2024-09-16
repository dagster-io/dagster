from typing import Optional

from dagster import Definitions
from dagster._utils.warnings import suppress_dagster_warnings

from dagster_airlift.core.sensor import (
    DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
    build_airflow_polling_sensor,
)
from dagster_airlift.migration_state import AirflowMigrationState

from .airflow_cacheable_assets_def import DEFAULT_POLL_INTERVAL, AirflowCacheableAssetsDefinition
from .airflow_instance import AirflowInstance


@suppress_dagster_warnings
def build_defs_from_airflow_instance(
    airflow_instance: AirflowInstance,
    cache_polling_interval: int = DEFAULT_POLL_INTERVAL,
    defs: Optional[Definitions] = None,
    # This parameter will go away once we can derive the migration state from airflow itself, using our built in utilities.
    # Alternatively, we can keep it around to let people override the migration state if they want.
    migration_state_override: Optional[AirflowMigrationState] = None,
    sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
) -> Definitions:
    """From a provided airflow instance and a set of airflow-orchestrated dagster definitions, build a set of dagster definitions to peer and observe the airflow instance.

    Each airflow dag will be represented as a dagster asset, and each dag run will be represented as an asset materialization. A :py:class:`dagster.SensorDefinition` provided in the returned Definitions will be used to poll for dag runs.


    Args:
        airflow_instance (AirflowInstance): The airflow instance to peer with.
        cache_polling_interval (int, optional): The interval at which to poll for updated assets from airflow. Defaults to 60 seconds.
        defs (Optional[Definitions], optional): Additional definitions to pass to the overall created Definitions object. Assets provided here can be mapped to specific tasks and dags within the provided airflow instance. Defaults to None.
        migration_state_override (Optional[AirflowMigrationState], optional): The migration state to use for the provided orchestrated defs. Defaults to None.

    Returns:
        Definitions: The definitions to use for the provided airflow instance. Contains an asset per dag, an asset per task in the provided orchestrated defs, all resources provided in the orchestrated defs, and a sensor to poll for airflow dag runs.

    """
    assets_defs = AirflowCacheableAssetsDefinition(
        airflow_instance=airflow_instance,
        defs=defs,
        poll_interval=cache_polling_interval,
        migration_state_override=migration_state_override,
    )
    # Now, we construct the sensor that will poll airflow for dag runs.
    airflow_sensor = build_airflow_polling_sensor(
        airflow_instance=airflow_instance, minimum_interval_seconds=sensor_minimum_interval_seconds
    )
    return Definitions(
        assets=[assets_defs],
        asset_checks=defs.asset_checks if defs else None,
        sensors=[airflow_sensor, *defs.sensors] if defs and defs.sensors else [airflow_sensor],
        schedules=defs.schedules if defs else None,
        jobs=defs.jobs if defs else None,
        executor=defs.executor if defs else None,
        loggers=defs.loggers if defs else None,
        resources=defs.resources if defs else None,
    )
