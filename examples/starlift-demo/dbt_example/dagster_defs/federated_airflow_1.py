from collections.abc import Sequence

from dagster import AssetsDefinition, Definitions, SensorDefinition
from dagster_airlift.core import (
    AirflowBasicAuthBackend,
    AirflowInstance,
    build_defs_from_airflow_instance,
)

from .constants import (
    OTHER_TEAM_FEDERATED_BASE_URL,
    OTHER_TEAM_FEDERATED_INSTANCE_NAME,
    PASSWORD,
    USERNAME,
)
from .utils import with_group

airflow_instance = AirflowInstance(
    auth_backend=AirflowBasicAuthBackend(
        webserver_url=OTHER_TEAM_FEDERATED_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=OTHER_TEAM_FEDERATED_INSTANCE_NAME,
)


def get_federated_airflow_defs() -> Definitions:
    return build_defs_from_airflow_instance(airflow_instance=airflow_instance)


def get_other_team_airflow_sensor() -> SensorDefinition:
    defs = get_federated_airflow_defs()
    assert defs.sensors
    return next(iter(defs.sensors))


def get_other_team_airflow_assets() -> Sequence[AssetsDefinition]:
    defs = get_federated_airflow_defs()
    return [
        with_group(assets_def, "upstream_team_airflow")
        for assets_def in defs.get_repository_def().assets_defs_by_key.values()
    ]
