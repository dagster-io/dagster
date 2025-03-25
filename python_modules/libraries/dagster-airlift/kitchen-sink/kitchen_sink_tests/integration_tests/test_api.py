from typing import cast

import pytest
import requests
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.run_request import SensorResult
from dagster._core.definitions.sensor_definition import build_sensor_context
from dagster._core.test_utils import instance_for_test
from dagster_airlift.constants import SOURCE_CODE_METADATA_KEY
from dagster_airlift.core import build_defs_from_airflow_instance
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.basic_auth import AirflowBasicAuthBackend
from kitchen_sink.airflow_instance import (
    AIRFLOW_BASE_URL,
    AIRFLOW_INSTANCE_NAME,
    PASSWORD,
    USERNAME,
    local_airflow_instance,
)
from pytest_mock import MockFixture


@pytest.fixture
def expected_num_dags() -> int:
    return 16


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
    assert len(af_instance.list_dags()) == 16
    # 16 with actual results, 1 with no results
    assert spy.call_count == 17


def change_dag_limit_source_code(limit: int) -> None:
    import dagster_airlift.core.serialization.compute

    dagster_airlift.core.serialization.compute.DEFAULT_MAX_NUM_DAGS_SOURCE_CODE_RETRIEVAL = limit


def test_disable_source_code_retrieval_at_scale(airflow_instance: None) -> None:
    """Test that source code retrieval is disabled at scale."""
    change_dag_limit_source_code(1)
    af_instance = local_airflow_instance()
    defs = build_defs_from_airflow_instance(airflow_instance=af_instance)
    assert defs.assets
    for assets_def in defs.assets:
        metadata = next(iter(cast(AssetsDefinition, assets_def).specs)).metadata
        assert SOURCE_CODE_METADATA_KEY not in metadata

    change_dag_limit_source_code(200)
    # Also force re-retrieval of state by giving the airflow instance a different name.
    af_instance = local_airflow_instance(name="different_name")
    defs = build_defs_from_airflow_instance(airflow_instance=af_instance)
    assert defs.assets
    for assets_def in defs.assets:
        metadata = next(iter(cast(AssetsDefinition, assets_def).specs)).metadata
        assert SOURCE_CODE_METADATA_KEY in metadata

    # If source code retrieval is explicitly enabled, we don't use the limit.
    change_dag_limit_source_code(1)
    af_instance = local_airflow_instance(name="different_name")
    defs = build_defs_from_airflow_instance(
        airflow_instance=af_instance, source_code_retrieval_enabled=True
    )
    assert defs.assets
    for assets_def in defs.assets:
        metadata = next(iter(cast(AssetsDefinition, assets_def).specs)).metadata
        assert SOURCE_CODE_METADATA_KEY in metadata


def test_sensor_iteration_multiple_batches(airflow_instance: None, mocker: MockFixture) -> None:
    """Test that sensor iteration correctly retrieves all sensors when over batch limit."""
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
