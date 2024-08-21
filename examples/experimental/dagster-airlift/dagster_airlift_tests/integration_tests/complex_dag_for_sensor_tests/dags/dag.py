# Create a dag with complex dependencies for testing the polling sensor.
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime   
import time
from typing import List

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 0,
}

dag = DAG(
    dag_id="complex_dag",
)
# Dag structure should be a diamond with a single task at the top, two tasks in the middle, and a single task, then fan out to two other tasks again.
# It looks like this:
#         top_task
#        /        \
# middle_task_1 middle_task_2
#        \        /
#       middle2_task
#        /        \
# bottom_task_1 bottom_task_2
def build_task(task_id: str, upstream_tasks: List[PythonOperator]) -> PythonOperator:
    task =  PythonOperator(
        task_id=task_id,
        python_callable=lambda: time.sleep(0.1),
        dag=dag,
    )
    for upstream_task in upstream_tasks:
        task.set_upstream(upstream_task)

    return task


top_task = build_task("top_task", [])

middle_task_1 = build_task("middle_task_1", [top_task])
middle_task_2 = build_task("middle_task_2", [top_task])

middle2_task = build_task("middle2_task", [middle_task_1, middle_task_2])

bottom_task_1 = build_task("bottom_task_1", [middle2_task])
bottom_task_2 = build_task("bottom_task_2", [middle2_task])

