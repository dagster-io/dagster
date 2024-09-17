# ruff: noqa: T201
import time

# Start timing for imports
import_start_time = time.time()
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from dagster._time import get_current_datetime
from dagster_airlift.in_airflow import mark_as_dagster_migrating
from dagster_airlift.migration_state import load_migration_state_from_yaml

from perf_harness.shared.constants import get_num_dags, get_num_tasks

# End timing for imports
import_end_time = time.time()
import_time = import_end_time - import_start_time

# Start timing for DAG creation
dag_creation_start_time = time.time()

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": get_current_datetime(),
}
global_vars = globals()
for i in range(get_num_dags()):
    dag = DAG(
        dag_id=f"dag_{i}",
        default_args=default_args,
        is_paused_upon_creation=False,
    )
    for j in range(get_num_tasks()):
        global_vars[f"task_{i}_{j}"] = PythonOperator(
            python_callable=lambda: print(f"Task {i}_{j}"),
            task_id=f"task_{i}_{j}",
            dag=dag,
        )
    global_vars[f"dag_{i}"] = dag

# End timing for DAG creation
dag_creation_end_time = time.time()
dag_creation_time = dag_creation_end_time - dag_creation_start_time

# Start timing for mark_as_dagster_migrating
mark_as_dagster_start_time = time.time()

mark_as_dagster_migrating(
    global_vars=globals(),
    migration_state=load_migration_state_from_yaml(Path(__file__).parent / "migration_state"),
)

# End timing for mark_as_dagster_migrating
mark_as_dagster_end_time = time.time()
mark_as_dagster_time = mark_as_dagster_end_time - mark_as_dagster_start_time

# Calculate total time
total_time = mark_as_dagster_end_time - import_start_time
