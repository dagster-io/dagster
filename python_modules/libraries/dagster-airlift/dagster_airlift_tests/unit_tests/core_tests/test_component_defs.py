import json
from pathlib import Path

import dagster_airlift.core as dg_airlift_core
import pytest
import yaml
from click.testing import CliRunner
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster.components.cli import cli
from dagster_airlift.core.components.airflow_instance.component import AirflowInstanceComponent
from dagster_airlift.test import make_instance
from dagster_airlift.test.test_utils import asset_spec

ensure_dagster_tests_import()
from dagster_tests.components_tests.utils import (
    build_component_defs_for_test,
    temp_code_location_bar,
)


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

    assert defs.jobs
    assert len(defs.jobs) == 3  # type: ignore # monitoring job + 2 dag jobs.


def _scaffold_airlift(scaffold_format: str):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "scaffold",
            "object",
            "dagster_airlift.core.components.airflow_instance.component.AirflowInstanceComponent",
            "bar/components/qux",
            "--json-params",
            json.dumps({"name": "qux", "auth_type": "basic_auth"}),
            "--scaffold-format",
            scaffold_format,
        ],
    )
    assert result.exit_code == 0


def test_scaffold_airlift_yaml():
    with temp_code_location_bar():
        _scaffold_airlift("yaml")
        assert Path("bar/components/qux/component.yaml").exists()
        with open("bar/components/qux/component.yaml") as f:
            assert yaml.safe_load(f) == {
                "type": "dagster_airlift.core.components.airflow_instance.component.AirflowInstanceComponent",
                "attributes": {
                    "name": "qux",
                    "auth": {
                        "type": "basic_auth",
                        "webserver_url": '{{ env("AIRFLOW_WEBSERVER_URL") }}',
                        "username": '{{ env("AIRFLOW_USERNAME") }}',
                        "password": '{{ env("AIRFLOW_PASSWORD") }}',
                    },
                },
            }


def test_scaffold_airlift_python():
    with temp_code_location_bar():
        _scaffold_airlift("python")
        assert Path("bar/components/qux/component.py").exists()
        with open("bar/components/qux/component.py") as f:
            file_contents = f.read()
            assert file_contents == (
                """from dagster.components import component, ComponentLoadContext
from dagster_airlift.core.components.airflow_instance.component import AirflowInstanceComponent

@component
def load(context: ComponentLoadContext) -> AirflowInstanceComponent: ...
"""
            )
