from dagster import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.loadable import DefLoadingContext
from dagster_airlift.core import AirflowInstance, BasicAuthBackend, PythonDefs, defs_from_factories
from dagster_airlift.core.defs_from_airflow import load_defs_from_airflow_instance

from simple_migration.shared import t1_work, t2_work, t3_work

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
t1 = PythonDefs(name="simple__t1", specs=[a1], python_fn=t1_work)
t2 = PythonDefs(name="simple__t2", specs=[a2, a3], python_fn=t2_work)
t3 = PythonDefs(name="simple__t3", specs=[a4], python_fn=t3_work)


def defs(context: DefLoadingContext) -> Definitions:
    return load_defs_from_airflow_instance(
        context,
        airflow_instance=airflow_instance,
        defs=defs_from_factories(t1, t2, t3),
    )
