from typing import Iterable, Sequence

from dagster import AssetsDefinition, Definitions, SensorDefinition
from dagster._core.definitions.asset_spec import replace_asset_attributes
from dagster_airlift.core import (
    AirflowBasicAuthBackend,
    AirflowInstance,
    build_defs_from_airflow_instance,
)

from .constants import LEGACY_FEDERATED_BASE_URL, LEGACY_FEDERATED_INSTANCE_NAME, PASSWORD, USERNAME
from .utils import all_assets_defs

airflow_instance = AirflowInstance(
    auth_backend=AirflowBasicAuthBackend(
        webserver_url=LEGACY_FEDERATED_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=LEGACY_FEDERATED_INSTANCE_NAME,
)


def get_federated_airflow_defs() -> Definitions:
    return build_defs_from_airflow_instance(airflow_instance=airflow_instance)


def federated_airflow_assets() -> Sequence[AssetsDefinition]:
    return all_assets_defs(get_federated_airflow_defs())


def get_legacy_instance_airflow_sensor() -> SensorDefinition:
    defs = get_federated_airflow_defs()
    assert defs.sensors
    return next(iter(defs.sensors))


def get_legacy_instance_airflow_assets() -> Iterable[AssetsDefinition]:
    return replace_asset_attributes(federated_airflow_assets(), group_name="legacy_airflow")
