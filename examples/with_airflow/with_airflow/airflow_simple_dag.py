# pyright: reportUnusedExpression=none

# Type errors ignored because some of these imports target deprecated modules for compatibility with
# airflow 1.x and 2.x.
from airflow import models
from airflow.operators.bash_operator import BashOperator  # type: ignore
from airflow.operators.dummy_operator import DummyOperator  # type: ignore
from airflow.utils.dates import days_ago

args = {
    "start_date": days_ago(2),
}

simple_dag = models.DAG(dag_id="simple_dag", default_args=args, schedule_interval="0 0 * * *")

run_this_last = DummyOperator(
    task_id="sink_task_foo",
    dag=simple_dag,
)

also_run_this_last = DummyOperator(
    task_id="sink_task_bar",
    dag=simple_dag,
)


get_date = BashOperator(
    task_id="get_date",
    bash_command='echo "execution_date={{ execution_date }} | ts={{ ts }}"',
    dag=simple_dag,
)

get_date >> run_this_last
get_date >> also_run_this_last


for i in range(3):
    task = BashOperator(
        task_id="get_task_instance_" + str(i),
        bash_command='echo "{{ task_instance_key_str }}" && sleep 1',
        dag=simple_dag,
    )
    for y in range(3):
        other_task = BashOperator(
            task_id="get_task_instance_" + str(i) + "_" + str(y),
            bash_command='echo "{{ task_instance_key_str }}" && sleep 1',
            dag=simple_dag,
        )
        other_task >> task
        get_date >> other_task
    task >> run_this_last
