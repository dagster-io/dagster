import os
import subprocess
from collections.abc import Generator, Sequence

import pytest
import requests
from dagster import Definitions
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.run_request import SensorResult
from dagster._core.definitions.sensor_definition import build_sensor_context
from dagster._core.test_utils import environ, instance_for_test
from dagster_airlift.constants import PEERED_DAG_MAPPING_METADATA_KEY, SOURCE_CODE_METADATA_KEY
from dagster_airlift.core import build_defs_from_airflow_instance
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.basic_auth import AirflowBasicAuthBackend
from dagster_airlift.core.filter import AirflowFilter
from dagster_airlift.core.serialization.serialized_data import Dataset
from dagster_airlift.core.top_level_dag_def_api import assets_with_dag_mappings
from dagster_airlift.test.shared_fixtures import stand_up_airflow
from dagster_airlift.test.test_utils import asset_spec
from kitchen_sink.airflow_instance import (
    AIRFLOW_BASE_URL,
    AIRFLOW_INSTANCE_NAME,
    EXPECTED_NUM_DAGS,
    PASSWORD,
    USERNAME,
    local_airflow_instance,
)
from pytest_mock import MockFixture

from kitchen_sink_tests.integration_tests.conftest import makefile_dir

# Override conftest fixtures to function-scope for test_api.py. Tests in this module check DAG run
# counts via sensors, so they need a fresh Airflow instance per test to avoid cross-test state
# (e.g. test_sensor_iteration_multiple_batches creates runs that would be visible to
# test_sensor_explicitly_mapped_assets if they shared an Airflow).


@pytest.fixture(name="local_env")
def local_env_fixture() -> Generator[None, None, None]:
    subprocess.run(["make", "setup_local_env"], cwd=makefile_dir(), check=True)
    with environ(
        {
            "AIRFLOW_HOME": str(makefile_dir() / ".airflow_home"),
            "DAGSTER_HOME": str(makefile_dir() / ".dagster_home"),
        }
    ):
        yield

    subprocess.run(
        ["make", "wipe"],
        cwd=makefile_dir(),
        check=False,
    )


@pytest.fixture(name="expected_num_dags")
def expected_num_dags_fixture() -> int:
    return EXPECTED_NUM_DAGS


@pytest.fixture(name="airflow_instance")
def airflow_instance_fixture(
    local_env: None, expected_num_dags: int
) -> Generator[subprocess.Popen, None, None]:
    with stand_up_airflow(
        airflow_cmd=["make", "run_airflow"],
        env=os.environ,
        cwd=makefile_dir(),
        expected_num_dags=expected_num_dags,
    ) as process:
        yield process


def test_configure_dag_list_limit(airflow_instance: None, mocker: MockFixture) -> None:
    """Test that batch instance logic correctly retrieves all dags when over batch limit."""
    spy = mocker.spy(requests.Session, "get")
    af_instance = AirflowInstance(
        auth_backend=AirflowBasicAuthBackend(
            webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
        ),
        name=AIRFLOW_INSTANCE_NAME,
        # Set low list limit, force batched retrieval.
        dag_list_limit=1,
    )
    assert len(af_instance.list_dags(AirflowFilter())) == EXPECTED_NUM_DAGS
    # EXPECTED_NUM_DAGS with actual results, 1 with no results
    assert spy.call_count == EXPECTED_NUM_DAGS + 1


def test_airflow_filter(airflow_instance: None) -> None:
    """Test that airflow filter correctly filters dags."""
    af_instance = AirflowInstance(
        auth_backend=AirflowBasicAuthBackend(
            webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
        ),
        name=AIRFLOW_INSTANCE_NAME,
    )
    dags = af_instance.list_dags(AirflowFilter(dag_id_ilike="simple"))
    assert len(dags) == 1
    assert dags[0].dag_id == "simple_unproxied_dag"

    dags = af_instance.list_dags(AirflowFilter(airflow_tags=["example"]))
    assert len(dags) == 1
    assert dags[0].dag_id == "simple_unproxied_dag"


def change_dag_limit_source_code(limit: int) -> None:
    import dagster_airlift.core.serialization.compute

    dagster_airlift.core.serialization.compute.DEFAULT_MAX_NUM_DAGS_SOURCE_CODE_RETRIEVAL = limit  # ty: ignore[invalid-assignment]


def test_disable_source_code_retrieval_at_scale(airflow_instance: None) -> None:
    """Test that source code retrieval is disabled at scale."""
    change_dag_limit_source_code(1)
    af_instance = local_airflow_instance()
    defs = build_defs_from_airflow_instance(airflow_instance=af_instance)
    all_specs = defs.resolve_all_asset_specs()
    assert all_specs
    for spec in all_specs:
        metadata = spec.metadata
        assert SOURCE_CODE_METADATA_KEY not in metadata

    change_dag_limit_source_code(200)
    # Also force re-retrieval of state by giving the airflow instance a different name.
    af_instance = local_airflow_instance(name="different_name")
    defs = build_defs_from_airflow_instance(airflow_instance=af_instance)
    all_specs = defs.resolve_all_asset_specs()
    assert all_specs
    for spec in all_specs:
        metadata = spec.metadata
        if PEERED_DAG_MAPPING_METADATA_KEY not in metadata:
            continue
        assert SOURCE_CODE_METADATA_KEY in metadata

    # If source code retrieval is explicitly enabled, we don't use the limit.
    change_dag_limit_source_code(1)
    af_instance = local_airflow_instance(name="different_name")
    defs = build_defs_from_airflow_instance(
        airflow_instance=af_instance, source_code_retrieval_enabled=True
    )
    all_specs = defs.resolve_all_asset_specs()
    assert all_specs
    for spec in all_specs:
        metadata = spec.metadata
        if PEERED_DAG_MAPPING_METADATA_KEY not in metadata:
            continue
        assert SOURCE_CODE_METADATA_KEY in metadata


def test_sensor_iteration_multiple_batches(airflow_instance: None, mocker: MockFixture) -> None:
    """Test that sensor iteration correctly retrieves all runs when over batch limit."""
    spy = mocker.spy(AirflowInstance, "get_dag_runs_batch")
    af_instance = AirflowInstance(
        auth_backend=AirflowBasicAuthBackend(
            webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
        ),
        name=AIRFLOW_INSTANCE_NAME,
        # Set low list limit, force batched retrieval.
        batch_dag_runs_limit=1,
    )
    defs = build_defs_from_airflow_instance(airflow_instance=af_instance)
    # create a bunch of runs
    for i in range(2):
        run_id = af_instance.trigger_dag("simple_unproxied_dag")
        af_instance.wait_for_run_completion(dag_id="simple_unproxied_dag", run_id=run_id)

    assert defs.sensors
    sensor_def = next(iter(defs.sensors))
    with instance_for_test() as instance:
        ctx = build_sensor_context(instance=instance, definitions=defs)
        result = sensor_def(ctx)
        assert isinstance(result, SensorResult)
        assert len(result.asset_events) == 2
        assert spy.call_count == 2


def test_sensor_explicitly_mapped_assets(airflow_instance: None, mocker: MockFixture) -> None:
    """Test that sensor iteration correctly retrieves all runs even when assets are explicitly mapped."""
    af_instance = AirflowInstance(
        auth_backend=AirflowBasicAuthBackend(
            webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
        ),
        name=AIRFLOW_INSTANCE_NAME,
    )
    # explicitly map an asset to a dag. This forces the set of dag_ids passed to the rest API to be nonzero.
    defs = build_defs_from_airflow_instance(
        airflow_instance=af_instance,
        defs=Definitions(assets=assets_with_dag_mappings({"print_dag": [AssetSpec("my_asset")]})),
    )
    # create a bunch of runs for an unrelated "peer only" dag
    for i in range(2):
        run_id = af_instance.trigger_dag("simple_unproxied_dag")
        af_instance.wait_for_run_completion(dag_id="simple_unproxied_dag", run_id=run_id)

    assert defs.sensors
    sensor_def = next(iter(defs.sensors))
    with instance_for_test() as instance:
        ctx = build_sensor_context(instance=instance, definitions=defs)
        result = sensor_def(ctx)
        assert isinstance(result, SensorResult)
        assert len(result.asset_events) == 2


def dataset_with_uri(datasets: Sequence[Dataset], uri: str) -> Dataset:
    return next(dataset for dataset in datasets if dataset.uri == uri)


def test_datasets(airflow_instance: None) -> None:
    """Test that we can correctly retrieve datasets from Airflow."""
    af_instance = local_airflow_instance()
    datasets = af_instance.get_all_datasets()
    assert len(datasets) == 2
    assert {d.uri for d in datasets} == {
        "s3://dataset-bucket/example1.csv",
        "s3://dataset-bucket/example2.csv",
    }
    example1_dataset = dataset_with_uri(datasets, "s3://dataset-bucket/example1.csv")
    assert {t.task_id for t in example1_dataset.producing_tasks} == {"print_task"}
    assert {d.dag_id for d in example1_dataset.consuming_dags} == {"example1_consumer"}
    assert example1_dataset.is_produced_by_task(task_id="print_task", dag_id="dataset_producer")

    example2_dataset = dataset_with_uri(datasets, "s3://dataset-bucket/example2.csv")
    assert {t.task_id for t in example2_dataset.producing_tasks} == {"print_task"}
    assert {d.dag_id for d in example2_dataset.consuming_dags} == {"example2_consumer"}
    assert example2_dataset.is_produced_by_task(task_id="print_task", dag_id="dataset_producer")

    # Apply a filter to the dataset
    datasets = af_instance.get_all_datasets(
        retrieval_filter=AirflowFilter(dataset_uri_ilike="example1")
    )
    assert len(datasets) == 1

    defs = build_defs_from_airflow_instance(airflow_instance=af_instance)
    assert asset_spec("example1", defs)
    assert asset_spec("example2", defs)

    # Apply a dag filter that does not include the producing dag. The datasets should not be
    # included in the definitions.
    defs = build_defs_from_airflow_instance(
        airflow_instance=af_instance,
        retrieval_filter=AirflowFilter(dag_id_ilike="print_dag"),
    )
    assert not asset_spec("example1", defs)
    assert not asset_spec("example2", defs)


def test_log_retrieval(airflow_instance: None) -> None:
    af_instance = local_airflow_instance()
    run_id = af_instance.trigger_dag("dataset_producer")
    af_instance.wait_for_run_completion(dag_id="dataset_producer", run_id=run_id)
    logs = af_instance.get_task_instance_logs(
        dag_id="dataset_producer", task_id="print_task", run_id=run_id, try_number=1
    )
    assert logs
    assert "DAGSTER_START" in logs
    assert "DAGSTER_END" in logs
