from dagster import AssetSpec, Definitions
from dagster_airlift.core import AirflowInstance, BasicAuthBackend, build_defs_from_airflow_instance
from dagster_airlift.core.dag_defs import dag_defs, task_defs

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

defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=dag_defs(
        "simple",
        task_defs("t1", Definitions(assets=[a1])),
        task_defs("t2", Definitions(assets=[a2, a3])),
        task_defs("t3", Definitions(assets=[a4])),
    ),
)
