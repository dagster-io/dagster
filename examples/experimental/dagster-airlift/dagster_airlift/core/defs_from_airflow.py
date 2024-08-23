from typing import Optional

from dagster import Definitions

from dagster_airlift.core.sensor import build_airflow_polling_sensor

from ..migration_state import AirflowMigrationState
from .airflow_cacheable_assets_def import DEFAULT_POLL_INTERVAL, AirflowCacheableAssetsDefinition
from .airflow_instance import AirflowInstance


def build_defs_from_airflow_instance(
    airflow_instance: AirflowInstance,
    cache_polling_interval: int = DEFAULT_POLL_INTERVAL,
    defs: Optional[Definitions] = None,
    # This parameter will go away once we can derive the migration state from airflow itself, using our built in utilities.
    # Alternatively, we can keep it around to let people override the migration state if they want.
    migration_state_override: Optional[AirflowMigrationState] = None,
) -> Definitions:
    """From a provided airflow instance and a set of airflow-orchestrated dagster definitions, build a set of dagster definitions to peer and observe the airflow instance.

    Each airflow dag will be represented as a dagster asset, and each dag run will be represented as an asset materialization. A :py:class:`dagster.SensorDefinition` provided in the returned Definitions will be used to poll for dag runs.

    The provided orchestrated defs are expected to contain fully qualified :py:class:`dagster.AssetsDefinition` objects, each of which should be mapped to a task and dag in the provided airflow instance. Using the airflow instance,
    dagster will provide dependency information between the assets representing tasks, and the dags that they contain. The included :py:class:`dagster.SensorDefinition` will poll for dag runs and materialize runs including each task as an asset for that task.

    There are two ways that the mapping can be done on a provided definition:
    1. By using the `airlift/dag_id` and `airlift/task_id` op tags on the underlying :py:class:`dagster.NodeDefinition` for the asset.
    2. By using an opinionated naming format on the :py:class:`dagster.NodeDefinition` for the asset. The naming format is `dag_id__task_id`.

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
        airflow_instance=airflow_instance,
    )
    return Definitions(
        assets=[assets_defs],
        asset_checks=defs.asset_checks if defs else None,
        sensors=[airflow_sensor, *defs.sensors] if defs and defs.sensors else [airflow_sensor],
        schedules=defs.schedules if defs else None,
        jobs=defs.jobs if defs else None,
        executor=defs.executor if defs else None,
        loggers=defs.loggers if defs else None,
    )
