from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List

from airflow import DAG
from airflow.operators.python import PythonOperator

if TYPE_CHECKING:
    from airflow.models.operator import BaseOperator


def build_dags_dict_given_structure(structure: Dict[str, Dict[str, List[str]]]) -> Dict[str, DAG]:
    """Given a structure of dags and their tasks, build a dictionary of dags."""
    return_dict = {}
    tasks_per_dag: Dict[str, Dict[str, "BaseOperator"]] = defaultdict(dict)
    for dag_id, task_structure in structure.items():
        dag = DAG(
            dag_id,
            default_args={
                "owner": "airflow",
                "depends_on_past": False,
                "start_date": datetime(2023, 1, 1),
                "retries": 1,
            },
            schedule_interval=None,
            is_paused_upon_creation=False,
        )
        for task_id in task_structure.keys():
            tasks_per_dag[dag_id][task_id] = PythonOperator(
                task_id=task_id,
                python_callable=lambda: None,
                dag=dag,
            )
        return_dict[dag_id] = dag

    # Do another pass to build out dependencies
    for dag_id, task_structure in structure.items():
        for task_id, deps in task_structure.items():
            for dep in deps:
                tasks_per_dag[dag_id][task_id].set_upstream(tasks_per_dag[dag_id][dep])
    return return_dict
