import requests
from airflow.utils.context import Context
from dagster_airlift.in_airflow import BaseProxyTaskToDagsterOperator


class DagsterCloudProxyOperator(BaseProxyTaskToDagsterOperator):
    def get_variable(self, context: Context, var_name: str) -> str:
        if "var" not in context:
            raise ValueError("No variables found in context")
        return context["var"]["value"][var_name]

    def get_dagster_session(self, context: Context) -> requests.Session:
        dagster_cloud_user_token = self.get_variable(context, "dagster_cloud_user_token")
        session = requests.Session()
        session.headers.update({"Dagster-Cloud-Api-Token": dagster_cloud_user_token})
        return session

    def get_dagster_url(self, context: Context) -> str:
        org_name = self.get_variable(context, "dagster_plus_organization_name")
        deployment_name = self.get_variable(context, "dagster_plus_deployment_name")
        return f"https://{org_name}.dagster.plus/{deployment_name}"
