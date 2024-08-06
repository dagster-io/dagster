from typing import Optional

from dagster import Definitions

from dagster_airlift.core.sensor import build_airflow_polling_sensor

from .airflow_cacheable_assets_def import DEFAULT_POLL_INTERVAL, AirflowCacheableAssetsDefinition
from .airflow_instance import AirflowInstance
from .migration_state import AirflowMigrationState


def create_defs_from_airflow_instance(
    airflow_instance: AirflowInstance,
    cache_polling_interval: int = DEFAULT_POLL_INTERVAL,
    orchestrated_defs: Optional[Definitions] = None,
    # This parameter will go away once we can derive the migration state from airflow itself, using our built in utilities.
    # Alternatively, we can keep it around to let people override the migration state if they want.
    migration_state_override: Optional[AirflowMigrationState] = None,
) -> Definitions:
    assets_defs = AirflowCacheableAssetsDefinition(
        airflow_instance=airflow_instance,
        orchestrated_defs=orchestrated_defs,
        poll_interval=cache_polling_interval,
        migration_state_override=migration_state_override,
    )
    # Now, we construct the sensor that will poll airflow for dag runs.
    airflow_sensor = build_airflow_polling_sensor(
        airflow_instance=airflow_instance,
    )
    return Definitions(
        assets=[assets_defs],
        sensors=[airflow_sensor],
        resources=orchestrated_defs.resources if orchestrated_defs else None,
    )
