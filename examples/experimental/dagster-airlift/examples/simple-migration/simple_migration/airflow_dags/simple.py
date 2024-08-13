from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from dagster_airlift.in_airflow import mark_as_dagster_migrating
from dagster_airlift.migration_state import load_migration_state_from_yaml
from simple_migration.shared import t1_work, t2_work, t3_work

MIGRATION_YAML_DIR = Path(__file__).parent / "dagster_migration"


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
}

dag = DAG(
    "simple", default_args=default_args, schedule_interval=None, is_paused_upon_creation=False
)
t1 = PythonOperator(task_id="t1", python_callable=t1_work, dag=dag)
t2 = PythonOperator(task_id="t2", python_callable=t2_work, dag=dag)
t3 = PythonOperator(task_id="t3", python_callable=t3_work, dag=dag)
t1.set_downstream(t2)
t2.set_downstream(t3)
# Graph looks like this: t1 -> t2 -> t3
# Uncomment the line below to mark the dag as migrating
mark_as_dagster_migrating(
    migration_state=load_migration_state_from_yaml(MIGRATION_YAML_DIR), global_vars=globals()
)
