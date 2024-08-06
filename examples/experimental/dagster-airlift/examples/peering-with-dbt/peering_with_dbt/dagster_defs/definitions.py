from typing import Union

from dagster import Definitions
from dagster_airlift import (
    AirflowInstance,
    BasicAuthBackend,
    PythonDefs,
    create_defs_from_airflow_instance,
    load_defs_from_yaml,
    load_migration_state_from_yaml,
)
from dagster_airlift.dbt import DbtProjectDefs

from .constants import (
    AIRFLOW_BASE_URL,
    AIRFLOW_INSTANCE_NAME,
    ASSETS_PATH,
    MIGRATION_STATE_PATH,
    PASSWORD,
    USERNAME,
)

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)

defs = create_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    orchestrated_defs=Definitions.merge(
        load_defs_from_yaml(
            yaml_path=ASSETS_PATH,
            defs_cls=Union[PythonDefs, DbtProjectDefs],
        ),
    ),
    migration_state_override=load_migration_state_from_yaml(
        migration_yaml_path=MIGRATION_STATE_PATH
    ),
)
