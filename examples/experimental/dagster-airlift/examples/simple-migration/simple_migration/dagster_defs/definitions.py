from dagster import AssetKey, AssetSpec
from dagster_airlift.core import (
    AirflowInstance,
    BasicAuthBackend,
    PythonDefs,
    build_defs_from_airflow_instance,
    defs_from_factories,
)

from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)

t1 = PythonDefs(
    name="simple__t2",
    specs=[AssetSpec(key=AssetKey(["a1"])), AssetSpec(key=AssetKey(["a2"]))],
    group="t2",
    python_fn=lambda: None,
)


defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance, orchestrated_defs=defs_from_factories(t1)
)
