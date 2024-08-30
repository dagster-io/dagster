from dagster._core.definitions.utils import check_valid_name
from dagster_airlift.core.airflow_instance import DagInfo


def test_dag_info_asset_key() -> None:
    # Airflow allows "exclusively alphanumeric characters, dashes, dots and underscores (all ASCII)"
    dag_info_hyphen = DagInfo(webserver_url="", dag_id="my-test-dag-id", metadata={})
    assert check_valid_name(dag_info_hyphen.dag_asset_key.to_user_string().replace("/", "__"))

    dag_info_slash = DagInfo(webserver_url="", dag_id="my-test/dag-id", metadata={})
    assert check_valid_name(dag_info_slash.dag_asset_key.to_user_string().replace("/", "__"))

    dag_info_dot = DagInfo(webserver_url="", dag_id="my-test.dag-id", metadata={})
    assert check_valid_name(dag_info_dot.dag_asset_key.to_user_string().replace("/", "__"))
