from pathlib import Path

import requests
from airflow import DAG
from airflow.utils.context import Context
from dagster_airlift.in_airflow import BaseProxyTaskToDagsterOperator, proxying_to_dagster
from dagster_airlift.in_airflow.proxied_state import load_proxied_state_from_yaml


class CustomProxyToDagsterOperator(BaseProxyTaskToDagsterOperator):
    def get_dagster_session(self, context: Context) -> requests.Session:
        if "var" not in context:
            raise ValueError("No variables found in context")
        api_key = context["var"]["value"].get("my_api_key")
        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {api_key}"})
        return session

    def get_dagster_url(self, context: Context) -> str:
        return "https://dagster.example.com/"


dag = DAG(
    dag_id="custom_proxy_example",
)

# At the end of your dag file
proxying_to_dagster(
    global_vars=globals(),
    proxied_state=load_proxied_state_from_yaml(Path(__file__).parent / "proxied_state"),
    dagster_operator_klass=CustomProxyToDagsterOperator,
)
