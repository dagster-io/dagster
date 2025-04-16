import dagster_airlift.core as dg_airlift_core
import pytest
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster_airlift.core.components.airflow_instance.component import AirflowInstanceComponent
from dagster_airlift.test import make_instance
from dagster_airlift.test.test_utils import asset_spec

ensure_dagster_tests_import()
from dagster_tests.components_tests.utils import build_component_defs_for_test


@pytest.fixture
def component_for_test():
    airflow_instance = make_instance(
        {"dag_1": ["dag_1_task_1", "dag_1_task_2"], "dag_2": ["dag_2_task_1", "dag_2_task_2"]},
        dataset_construction_info=[
            {
                "uri": "s3://dataset-bucket/example1.csv",
                "producing_tasks": [
                    {"dag_id": "dag_1", "task_id": "dag_1_task_1"},
                ],
                "consuming_dags": ["dag_2"],
            },
            {
                "uri": "s3://dataset-bucket/example2.csv",
                "producing_tasks": [
                    {"dag_id": "dag_2", "task_id": "dag_2_task_1"},
                ],
                "consuming_dags": [],
            },
        ],
    )

    class DebugAirflowInstanceComponent(AirflowInstanceComponent):
        def _get_instance(self) -> dg_airlift_core.AirflowInstance:
            return airflow_instance

    return DebugAirflowInstanceComponent


def test_load_dags_basic(component_for_test: type[AirflowInstanceComponent]) -> None:
    defs = build_component_defs_for_test(
        component_for_test,
        {
            "auth": {
                "type": "basic_auth",
                "webserver_url": "http://localhost:8080",
                "username": "admin",
                "password": "admin",
            },
            "name": "test_instance",
            "asset_post_processors": [
                {
                    "target": "*",
                    "attributes": {
                        "metadata": {
                            "foo": "bar",
                        },
                    },
                }
            ],
        },
    )

    for asset_key in ["example1", "example2"]:
        keyed_spec = asset_spec(asset_key, defs)
        assert keyed_spec is not None
        assert keyed_spec.metadata["foo"] == "bar"

    assert len(defs.jobs) == 3  # monitoring job + 2 dag jobs.
