from typing import Iterable

from dagster import AssetsDefinition, Definitions, SensorDefinition
from dagster._core.definitions.asset_spec import replace_asset_attributes
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
from .utils import all_assets_defs

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


def get_other_team_airflow_assets() -> Iterable[AssetsDefinition]:
    assets_defs = all_assets_defs(get_federated_airflow_defs())
    return replace_asset_attributes(assets=assets_defs, group_name="upstream_team_airflow")
