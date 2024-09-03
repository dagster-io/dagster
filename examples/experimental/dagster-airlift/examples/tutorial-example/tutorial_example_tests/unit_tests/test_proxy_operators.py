from tutorial_example.airflow_dags.custom_proxy import CustomProxyToDagsterOperator
from tutorial_example.airflow_dags.plus_proxy_operator import DagsterCloudProxyOperator


def test_dagster_cloud_proxy_operator() -> None:
    operator = DagsterCloudProxyOperator(task_id="test_task")
    assert (
        operator.get_dagster_url(
            {  # type: ignore
                "var": {
                    "value": {
                        "dagster_plus_organization_name": "test_org",
                        "dagster_plus_deployment_name": "test_deployment",
                    }
                }
            }
        )
        == "https://test_org.dagster.plus/test_deployment"
    )
    assert (
        operator.get_variable(
            {"var": {"value": {"dagster_cloud_user_token": "test_token"}}},  # type: ignore
            "dagster_cloud_user_token",
        )
        == "test_token"
    )


def test_custom_proxy_operator() -> None:
    operator = CustomProxyToDagsterOperator(task_id="test_task")
    assert (
        operator.get_dagster_url({"var": {"value": {"my_api_key": "test_key"}}})  # type: ignore
        == "https://dagster.example.com/"
    )
    session = operator.get_dagster_session({"var": {"value": {"my_api_key": "test_key"}}})  # type: ignore
    assert session.headers["Authorization"] == "Bearer test_key"
