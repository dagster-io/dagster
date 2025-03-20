import tempfile
from pathlib import Path
from typing import Any, Callable

import dagster_airlift.core as dg_airlift_core
import pytest
import yaml
from click.testing import CliRunner
from dagster import AssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster_airlift.test import make_instance
from dagster_components.cli import cli
from dagster_components.components.airflow_instance.component import (
    AirflowInstanceComponent,
    AirflowInstanceModel,
)
from dagster_components.core.component_decl_builder import ComponentFileModel
from dagster_components.core.component_defs_builder import YamlComponentDecl
from dagster_components.utils import ensure_dagster_components_tests_import

ensure_dagster_components_tests_import()

from dagster_components_tests.utils import script_load_context, temp_code_location_bar


@pytest.fixture
def component_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def debug_airflow_component_type():
    airflow_instance = make_instance(
        {"dag_1": ["dag_1_task_1", "dag_1_task_2"], "dag_2": ["dag_2_task_1", "dag_2_task_2"]}
    )

    class DebugAirflowInstanceComponent(AirflowInstanceComponent):
        def _get_instance(self) -> dg_airlift_core.AirflowInstance:
            return airflow_instance

    return DebugAirflowInstanceComponent


@pytest.fixture(name="defs_for_airflow_asset")
def defs_for_airflow_asset_fixture(
    debug_airflow_component_type: type[AirflowInstanceComponent], component_dir: Path
) -> Callable[[dict[str, Any]], Definitions]:
    def _defs_for_airflow_asset(attrs: dict[str, Any]) -> Definitions:
        decl_node = YamlComponentDecl(
            path=component_dir,
            component_file_model=ComponentFileModel(
                type="debug_sling_replication",
                attributes=attrs,
            ),
        )
        context = script_load_context(decl_node)
        attributes = decl_node.get_attributes(AirflowInstanceModel)
        component_inst = debug_airflow_component_type.load(attributes=attributes, context=context)
        return component_inst.build_defs(context)

    return _defs_for_airflow_asset


def test_load_dags_basic(defs_for_airflow_asset: Callable[[dict[str, Any]], Definitions]) -> None:
    defs = defs_for_airflow_asset(
        {
            "auth": {
                "type": "basic_auth",
                "webserver_url": "http://localhost:8080",
                "username": "admin",
                "password": "admin",
            },
            "name": "test_instance",
        },
    )

    assert defs.get_asset_graph().get_all_asset_keys() == {
        AssetKey(["test_instance", "dag", "dag_1"]),
        AssetKey(["test_instance", "dag", "dag_2"]),
    }


def test_load_dags_filter(defs_for_airflow_asset: Callable[[dict[str, Any]], Definitions]) -> None:
    defs = defs_for_airflow_asset(
        {
            "auth": {
                "type": "basic_auth",
                "webserver_url": "http://localhost:8080",
                "username": "admin",
                "password": "admin",
            },
            "name": "test_instance",
            "dags_to_load": {"dag_ids": ["dag_1"]},
        },
    )

    assert defs.get_asset_graph().get_all_asset_keys() == {
        AssetKey(["test_instance", "dag", "dag_1"])
    }


def test_load_dags_dag_mapping(
    defs_for_airflow_asset: Callable[[dict[str, Any]], Definitions],
) -> None:
    defs = defs_for_airflow_asset(
        {
            "auth": {
                "type": "basic_auth",
                "webserver_url": "http://localhost:8080",
                "username": "admin",
                "password": "admin",
            },
            "name": "test_instance",
            "dag_mappings": [
                {
                    "dag_id": "dag_1",
                    "asset_specs": [{"key": "dag_1_asset_1"}, {"key": "dag_1_asset_2"}],
                },
            ],
        },
    )

    assert defs.get_asset_graph().get_all_asset_keys() == {
        AssetKey(["dag_1_asset_1"]),
        AssetKey(["dag_1_asset_2"]),
        AssetKey(["test_instance", "dag", "dag_1"]),
        AssetKey(["test_instance", "dag", "dag_2"]),
    }
    defs = defs_for_airflow_asset(
        {
            "auth": {
                "type": "basic_auth",
                "webserver_url": "http://localhost:8080",
                "username": "admin",
                "password": "admin",
            },
            "name": "test_instance",
            "dag_mappings": [
                {
                    "dag_id": "dag_1",
                    "asset_specs": [{"key": "dag_1_asset_1"}, {"key": "dag_1_asset_2"}],
                },
                {
                    "dag_id": "dag_2",
                    "asset_specs": [{"key": "dag_2_asset_1"}, {"key": "dag_2_asset_2"}],
                },
            ],
        },
    )

    assert defs.get_asset_graph().get_all_asset_keys() == {
        AssetKey(["dag_1_asset_1"]),
        AssetKey(["dag_1_asset_2"]),
        AssetKey(["dag_2_asset_1"]),
        AssetKey(["dag_2_asset_2"]),
        AssetKey(["test_instance", "dag", "dag_1"]),
        AssetKey(["test_instance", "dag", "dag_2"]),
    }


def test_load_dags_task_mapping(
    defs_for_airflow_asset: Callable[[dict[str, Any]], Definitions],
) -> None:
    defs = defs_for_airflow_asset(
        {
            "auth": {
                "type": "basic_auth",
                "webserver_url": "http://localhost:8080",
                "username": "admin",
                "password": "admin",
            },
            "name": "test_instance",
            "dag_mappings": [
                {
                    "dag_id": "dag_1",
                    "task_mappings": [
                        {
                            "task_id": "dag_1_task_1",
                            "asset_specs": [{"key": "dag_1_task_1_asset_1"}],
                        },
                        {
                            "task_id": "dag_1_task_2",
                            "asset_specs": [{"key": "dag_1_task_2_asset_1"}],
                        },
                    ],
                },
            ],
        },
    )

    assert defs.get_asset_graph().get_all_asset_keys() == {
        AssetKey(["dag_1_task_1_asset_1"]),
        AssetKey(["dag_1_task_2_asset_1"]),
        AssetKey(["test_instance", "dag", "dag_1"]),
        AssetKey(["test_instance", "dag", "dag_2"]),
    }


def test_load_dags_dag_and_task_mapping_complex(
    defs_for_airflow_asset: Callable[[dict[str, Any]], Definitions],
) -> None:
    defs = defs_for_airflow_asset(
        {
            "auth": {
                "type": "basic_auth",
                "webserver_url": "http://localhost:8080",
                "username": "admin",
                "password": "admin",
            },
            "name": "test_instance",
            "dag_mappings": [
                {
                    "dag_id": "dag_1",
                    "asset_specs": [{"key": "dag_1_asset_1"}, {"key": "dag_1_asset_2"}],
                    "task_mappings": [
                        {
                            "task_id": "dag_1_task_1",
                            "asset_specs": [
                                {
                                    "key": "dag_1_task_1_asset_1",
                                    "tags": {"foo": "bar"},
                                    "description": "foo",
                                }
                            ],
                        },
                        {
                            "task_id": "dag_1_task_2",
                            "asset_specs": [{"key": "dag_1_task_2_asset_1"}],
                        },
                    ],
                },
            ],
        },
    )

    assert defs.get_asset_graph().get_all_asset_keys() == {
        AssetKey(["dag_1_asset_1"]),
        AssetKey(["dag_1_asset_2"]),
        AssetKey(["dag_1_task_1_asset_1"]),
        AssetKey(["dag_1_task_2_asset_1"]),
        AssetKey(["test_instance", "dag", "dag_1"]),
        AssetKey(["test_instance", "dag", "dag_2"]),
    }
    dag_1_task_1_asset_1_spec = defs.get_assets_def(
        AssetKey(["dag_1_task_1_asset_1"])
    ).specs_by_key[AssetKey(["dag_1_task_1_asset_1"])]
    assert dag_1_task_1_asset_1_spec.tags["foo"] == "bar"
    assert dag_1_task_1_asset_1_spec.description == "foo"


def test_scaffold_airlift():
    runner = CliRunner()

    with temp_code_location_bar():
        result = runner.invoke(
            cli,
            [
                "scaffold",
                "component",
                "dagster_components.dagster_airlift.AirflowInstanceComponent",
                "bar/components/qux",
            ],
        )
        assert result.exit_code == 0
        assert Path("bar/components/qux/component.yaml").exists()
        with open("bar/components/qux/component.yaml") as f:
            assert yaml.safe_load(f) == {
                "type": "dagster_components.dagster_airlift.AirflowInstanceComponent",
                "attributes": {
                    "name": "qux",
                    "auth": {
                        "type": "basic_auth",
                        "webserver_url": None,
                        "username": None,
                        "password": None,
                    },
                },
            }
