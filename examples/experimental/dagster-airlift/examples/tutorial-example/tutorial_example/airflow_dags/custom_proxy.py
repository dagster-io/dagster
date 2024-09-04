import requests
from airflow.utils.context import Context
from dagster_airlift.in_airflow import BaseProxyToDagsterOperator, mark_as_dagster_migrating


class CustomProxyToDagsterOperator(BaseProxyToDagsterOperator):
    def get_dagster_session(self, context: Context) -> requests.Session:
        if "var" not in context:
            raise ValueError("No variables found in context")
        api_key = context["var"]["value"].get("my_api_key")
        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {api_key}"})
        return session

    def get_dagster_url(self, context: Context) -> str:
        return "https://dagster.example.com/"


...

# At the end of your dag file
mark_as_dagster_migrating(
    global_vars=globals(), migration_state=..., dagster_operator_klass=CustomProxyToDagsterOperator
)
