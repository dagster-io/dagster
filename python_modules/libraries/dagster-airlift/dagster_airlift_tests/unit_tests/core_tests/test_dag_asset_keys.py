from dagster._core.definitions.utils import check_valid_name
from dagster_airlift.core.airflow_instance import DagInfo
from dagster_airlift.core.serialization.defs_construction import make_default_dag_asset_key

INSTANCE_NAME = "airflow_instance"


def produce_valid_name(dag_info: DagInfo) -> str:
    return (
        make_default_dag_asset_key("airflow_instance", dag_info.dag_id)
        .to_user_string()
        .replace("/", "__")
    )


def test_dag_info_asset_key() -> None:
    # Airflow allows "exclusively alphanumeric characters, dashes, dots and underscores (all ASCII)"
    dag_info_hyphen = DagInfo(webserver_url="", dag_id="my-test-dag-id", metadata={})
    assert check_valid_name(produce_valid_name(dag_info_hyphen))

    dag_info_slash = DagInfo(webserver_url="", dag_id="my-test/dag-id", metadata={})
    assert check_valid_name(produce_valid_name(dag_info_slash))

    dag_info_dot = DagInfo(webserver_url="", dag_id="my-test.dag-id", metadata={})
    assert check_valid_name(produce_valid_name(dag_info_dot))
