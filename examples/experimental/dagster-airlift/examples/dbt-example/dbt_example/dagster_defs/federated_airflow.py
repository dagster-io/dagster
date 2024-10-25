from typing import Sequence

from dagster import AssetsDefinition, Definitions, SensorDefinition
from dagster_airlift.core import AirflowInstance, BasicAuthBackend, build_defs_from_airflow_instance

from .constants import FEDERATED_BASE_URL, FEDERATED_INSTANCE_NAME, PASSWORD, USERNAME

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=FEDERATED_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=FEDERATED_INSTANCE_NAME,
)


def get_federated_airflow_defs() -> Definitions:
    return build_defs_from_airflow_instance(airflow_instance=airflow_instance)


def get_federated_airflow_sensor() -> SensorDefinition:
    defs = get_federated_airflow_defs()
    assert defs.sensors
    return next(iter(defs.sensors))


def get_federated_airflow_assets() -> Sequence[AssetsDefinition]:
    defs = get_federated_airflow_defs()
    return list(defs.get_repository_def().assets_defs_by_key.values())
