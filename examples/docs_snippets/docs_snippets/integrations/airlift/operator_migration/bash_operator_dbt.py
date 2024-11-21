from airflow.operators.bash import BashOperator

run_dbt_model = BashOperator(task_id="build_dbt_models", bash_command="dbt run")
