from typing import cast

from dagster._core.definitions.assets import AssetsDefinition
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


def test_configure_dag_list_limit(airflow_instance: None) -> None:
    """Test that batch instance logic correctly retrieves all dags when over batch limit."""
    af_instance = AirflowInstance(
        auth_backend=AirflowBasicAuthBackend(
            webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
        ),
        name=AIRFLOW_INSTANCE_NAME,
        # Set low list limit, force batched retrieval.
        dag_list_limit=1,
    )
    assert len(af_instance.list_dags()) == 16


def change_dag_limit_source_code(limit: int) -> None:
    import dagster_airlift.core.serialization.compute

    dagster_airlift.core.serialization.compute.MAX_NUM_DAGS_SOURCE_CODE_RETRIEVAL = limit


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
