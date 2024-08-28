from typing import Callable, Sequence

from dagster import AssetSpec
from dagster_airlift.core import AirflowInstance, BasicAuthBackend, build_defs_from_airflow_instance
from dagster_airlift.core.dag_defs import TaskDefs, dag_defs, task_defs
from dagster_airlift.core.python_callable import defs_for_python_callable

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


def python_callable_defs_for_task(
    task_id: str, python_callable: Callable, asset_specs: Sequence[AssetSpec]
) -> TaskDefs:
    return task_defs(
        task_id, defs_for_python_callable(python_callable=python_callable, asset_specs=asset_specs)
    )


defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=dag_defs(
        "simple",
        python_callable_defs_for_task("t1", t1_work, [a1]),
        python_callable_defs_for_task("t2", t2_work, [a2, a3]),
        python_callable_defs_for_task("t3", t3_work, [a4]),
    ),
)
