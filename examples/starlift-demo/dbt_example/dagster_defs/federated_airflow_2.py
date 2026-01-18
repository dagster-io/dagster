from collections.abc import Sequence

from dagster import AssetsDefinition, Definitions, SensorDefinition
from dagster_airlift.core import (
    AirflowBasicAuthBackend,
    AirflowInstance,
    build_defs_from_airflow_instance,
)

from .constants import LEGACY_FEDERATED_BASE_URL, LEGACY_FEDERATED_INSTANCE_NAME, PASSWORD, USERNAME
from .utils import with_group

airflow_instance = AirflowInstance(
    auth_backend=AirflowBasicAuthBackend(
        webserver_url=LEGACY_FEDERATED_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=LEGACY_FEDERATED_INSTANCE_NAME,
)


def get_federated_airflow_defs() -> Definitions:
    return build_defs_from_airflow_instance(airflow_instance=airflow_instance)


def get_legacy_instance_airflow_sensor() -> SensorDefinition:
    defs = get_federated_airflow_defs()
    assert defs.sensors
    return next(iter(defs.sensors))


def get_legacy_instance_airflow_assets() -> Sequence[AssetsDefinition]:
    defs = get_federated_airflow_defs()
    return [
        with_group(assets_def, "legacy_airflow")
        for assets_def in defs.get_repository_def().assets_defs_by_key.values()
    ]
