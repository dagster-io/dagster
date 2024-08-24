from dagster import AssetSpec
from dagster_airlift.core import (
    AirflowInstance,
    BasicAuthBackend,
    PythonDefs,
    defs_from_factories,
    sync_build_defs_from_airflow_instance,
)

from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)

# Asset graph
a1 = AssetSpec(key="a1")
a2 = AssetSpec(key="a2", deps=[a1])
a3 = AssetSpec(key="a3", deps=[a1])
a4 = AssetSpec(key="a4", deps=[a2, a3])

# Factory instance per airflow task
t1 = PythonDefs(name="simple__t1", specs=[a1])
t2 = PythonDefs(name="simple__t2", specs=[a2, a3])
t3 = PythonDefs(name="simple__t3", specs=[a4])


defs = sync_build_defs_from_airflow_instance(
    airflow_instance=airflow_instance, defs=defs_from_factories(t1, t2, t3)
)
