from airflow.operators.bash import BashOperator

execute_script = BashOperator(
    task_id="execute_script",
    bash_command="python /path/to/script.py",
)
