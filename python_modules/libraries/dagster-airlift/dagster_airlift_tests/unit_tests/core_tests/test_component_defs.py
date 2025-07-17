import json
import tempfile
from collections.abc import Iterator
from pathlib import Path
from unittest import mock

import dagster_airlift.core as dg_airlift_core
import pytest
import yaml
from click.testing import CliRunner
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster._utils import pushd
from dagster_airlift.constants import (
    DAG_MAPPING_METADATA_KEY,
    SOURCE_CODE_METADATA_KEY,
    TASK_MAPPING_METADATA_KEY,
)
from dagster_airlift.core.components.airflow_instance.component import AirflowInstanceComponent
from dagster_airlift.test import make_instance
from dagster_airlift.test.test_utils import asset_spec, get_job_from_defs
from dagster_dg_cli.cli import cli

ensure_dagster_tests_import()
from dagster_tests.components_tests.utils import (
    build_component_defs_for_test,
    temp_code_location_bar,
)


@pytest.fixture
def temp_cwd() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as temp_dir:
        with pushd(temp_dir):
            yield Path.cwd()


@pytest.fixture
def component_for_test(temp_cwd: Path):
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
        component_type=component_for_test,
        attrs={
            "auth": {
                "type": "basic_auth",
                "webserver_url": "http://localhost:8080",
                "username": "admin",
                "password": "admin",
            },
            "name": "test_instance",
        },
        post_processing={
            "assets": [
                {
                    "target": "*",
                    "attributes": {
                        "metadata": {
                            "foo": "bar",
                        },
                    },
                }
            ]
        },
    )

    for asset_key in ["example1", "example2"]:
        keyed_spec = asset_spec(asset_key, defs)
        assert keyed_spec is not None
        assert keyed_spec.metadata["foo"] == "bar"

    assert defs.jobs
    assert len(list(defs.jobs)) == 3  # monitoring job + 2 dag jobs.
    for job_name in ["dag_1", "dag_2"]:
        job = get_job_from_defs(job_name, defs)
        assert job is not None
        assert isinstance(job, JobDefinition)
        assert job.metadata.get(SOURCE_CODE_METADATA_KEY) is not None


def _scaffold_airlift(scaffold_format: str):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "scaffold",
            "defs",
            "dagster_airlift.core.components.AirflowInstanceComponent",
            "qux",
            "--json-params",
            json.dumps({"name": "qux", "auth_type": "basic_auth"}),
            "--format",
            scaffold_format,
        ],
    )
    assert result.exit_code == 0


def test_scaffold_airlift_yaml():
    with temp_code_location_bar():
        _scaffold_airlift("yaml")
        assert Path("bar/defs/qux/defs.yaml").exists()
        with open("bar/defs/qux/defs.yaml") as f:
            assert yaml.safe_load(f) == {
                "type": "dagster_airlift.core.components.AirflowInstanceComponent",
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
        assert Path("bar/defs/qux/component.py").exists()
        with open("bar/defs/qux/component.py") as f:
            file_contents = f.read()
            assert file_contents == (
                """from dagster import component_instance, ComponentLoadContext
from dagster_airlift.core.components import AirflowInstanceComponent

@component_instance
def load(context: ComponentLoadContext) -> AirflowInstanceComponent: ...
"""
            )


@pytest.mark.skip("Figure out how to model this test with new tree system")
def test_mapped_assets(component_for_test: type[AirflowInstanceComponent], temp_cwd: Path):
    # Add a sub-dir with an asset that will be task mapped.
    (temp_cwd / "my_asset").mkdir()
    with open(temp_cwd / "my_asset" / "defs.yaml", "w") as f:
        f.write(
            yaml.dump(
                {
                    "type": "dagster_airlift.test.test_utils.BasicAssetComponent",
                    "attributes": {
                        "key": "my_asset",
                    },
                }
            )
        )

    # Add a sub-dir with an asset that will be dag mapped.
    (temp_cwd / "my_asset_2").mkdir()
    with open(temp_cwd / "my_asset_2" / "defs.yaml", "w") as f:
        f.write(
            yaml.dump(
                {
                    "type": "dagster_airlift.test.test_utils.BasicAssetComponent",
                    "attributes": {
                        "key": "my_asset_2",
                    },
                }
            )
        )

    # Next, add an airlift component which references the asset
    defs = build_component_defs_for_test(
        component_type=component_for_test,
        attrs={
            "auth": {
                "type": "basic_auth",
                "webserver_url": "http://localhost:8080",
                "username": "admin",
                "password": "admin",
            },
            "name": "test_instance",
            "mappings": [
                {
                    "dag_id": "dag_1",
                    "task_mappings": [
                        {
                            "task_id": "dag_1_task_1",
                            "assets": [{"by_key": "my_asset"}, {"spec": {"key": "my_ext_asset_1"}}],
                        }
                    ],
                    "assets": [{"by_key": "my_asset_2"}, {"spec": {"key": "my_ext_asset_2"}}],
                }
            ],
        },
        post_processing={
            "assets": [
                {
                    "target": "*",
                    "attributes": {"metadata": {"foo": "bar"}},
                }
            ]
        },
    )

    assert defs.assets is not None
    assert len(list(defs.assets)) == 6

    my_asset_def = next(
        a
        for a in defs.assets
        if isinstance(a, AssetsDefinition) and a.key.to_user_string() == "my_asset"
    )
    my_asset_spec = next(iter(my_asset_def.specs))
    assert my_asset_spec.metadata[TASK_MAPPING_METADATA_KEY] == [
        {
            "dag_id": "dag_1",
            "task_id": "dag_1_task_1",
        }
    ]
    assert DAG_MAPPING_METADATA_KEY not in my_asset_spec.metadata

    my_asset_2_def = next(
        a
        for a in defs.assets
        if isinstance(a, AssetsDefinition) and a.key.to_user_string() == "my_asset_2"
    )
    my_asset_2_spec = next(iter(my_asset_2_def.specs))
    assert my_asset_2_spec.metadata[DAG_MAPPING_METADATA_KEY] == [
        {
            "dag_id": "dag_1",
        }
    ]
    assert TASK_MAPPING_METADATA_KEY not in my_asset_2_spec.metadata

    my_ext_asset_1_spec = next(
        a
        for a in defs.assets
        if isinstance(a, AssetSpec) and a.key.to_user_string() == "my_ext_asset_1"
    )
    assert my_ext_asset_1_spec.metadata[TASK_MAPPING_METADATA_KEY] == [
        {
            "dag_id": "dag_1",
            "task_id": "dag_1_task_1",
        }
    ]
    assert DAG_MAPPING_METADATA_KEY not in my_ext_asset_1_spec.metadata

    my_ext_asset_2_spec = next(
        a
        for a in defs.assets
        if isinstance(a, AssetSpec) and a.key.to_user_string() == "my_ext_asset_2"
    )
    assert my_ext_asset_2_spec.metadata[DAG_MAPPING_METADATA_KEY] == [
        {
            "dag_id": "dag_1",
        }
    ]

    # Datasets should be there too
    assert asset_spec("example1", defs) is not None
    assert asset_spec("example2", defs) is not None


def test_mwaa_auth(component_for_test: type[AirflowInstanceComponent]):
    # mock boto3
    with mock.patch("boto3.Session"):
        defs = build_component_defs_for_test(
            component_for_test,
            {
                "auth": {
                    "type": "mwaa",
                    "env_name": "test_env",
                    "region_name": "test_region",
                    "profile_name": "test_profile",
                },
                "name": "test_instance",
            },
        )
        assert defs.jobs
        assert len(list(defs.jobs)) == 3  # monitoring job + 2 dag jobs.


def test_source_code_retrieval_disabled(
    component_for_test: type[AirflowInstanceComponent], temp_cwd: Path
):
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
            "source_code_retrieval_enabled": False,
        },
    )
    assert defs.jobs
    dag1_job = get_job_from_defs("dag_1", defs)
    assert dag1_job is not None
    assert isinstance(dag1_job, JobDefinition)
    assert dag1_job.metadata.get(SOURCE_CODE_METADATA_KEY) is None


def test_airflow_filter(component_for_test: type[AirflowInstanceComponent], temp_cwd: Path):
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
            "filter": {
                "dag_id_ilike": "dag_1",
            },
        },
    )
    assert defs.jobs
    dag1_job = get_job_from_defs("dag_1", defs)
    assert dag1_job is not None

    dag2_job = get_job_from_defs("dag_2", defs)
    assert dag2_job is None
