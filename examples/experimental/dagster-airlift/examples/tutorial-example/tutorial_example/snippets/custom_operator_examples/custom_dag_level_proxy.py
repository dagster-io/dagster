from pathlib import Path

import requests
from airflow import DAG
from airflow.utils.context import Context
from dagster_airlift.in_airflow import BaseProxyDAGToDagsterOperator, proxying_to_dagster
from dagster_airlift.in_airflow.proxied_state import load_proxied_state_from_yaml


class CustomProxyToDagsterOperator(BaseProxyDAGToDagsterOperator):
    def get_dagster_session(self, context: Context) -> requests.Session:
        if "var" not in context:
            raise ValueError("No variables found in context")
        api_key = context["var"]["value"].get("my_api_key")
        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {api_key}"})
        return session

    def get_dagster_url(self, context: Context) -> str:
        return "https://dagster.example.com/"

    # This method controls how the operator is built from the dag.
    @classmethod
    def build_from_dag(cls, dag: DAG):
        return CustomProxyToDagsterOperator(dag=dag, task_id="OVERRIDDEN")


dag = DAG(
    dag_id="custom_dag_level_proxy_example",
)

# At the end of your dag file
proxying_to_dagster(
    global_vars=globals(),
    proxied_state=load_proxied_state_from_yaml(Path(__file__).parent / "proxied_state"),
    build_from_dag_fn=CustomProxyToDagsterOperator.build_from_dag,
)
