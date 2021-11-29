# pylint: disable=pointless-statement

from airflow import models
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago

args = {
    "start_date": days_ago(2),
}

simple_dag = models.DAG(dag_id="simple_dag", default_args=args, schedule_interval=None)

run_this_last = DummyOperator(
    task_id="sink_task",
    dag=simple_dag,
)

for i in range(3):
    task = BashOperator(
        task_id="get_task_instance_" + str(i),
        bash_command='echo "{{ task_instance_key_str }}" && sleep 1',
        dag=simple_dag,
    )
    task >> run_this_last

also_run_this = BashOperator(
    task_id="get_date",
    bash_command='echo "execution_date={{ execution_date }} | ts={{ ts }}"',
    dag=simple_dag,
)

also_run_this >> run_this_last
