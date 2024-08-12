from pathlib import Path
from typing import List

import pytest
from dagster import Definitions, multi_asset
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster_airlift.core.airflow_cacheable_assets_def import AirflowCacheableAssetsDefinition
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.basic_auth import BasicAuthBackend


# Dag dir override
@pytest.fixture(name="dags_dir")
def dag_dir_fixture() -> Path:
    return Path(__file__).parent / "transitive_asset_deps_dags"


def create_asset_for_task(task_id: str, dag_id: str, key: str, dep_keys: List[str] = []):
    @multi_asset(
        specs=[
            AssetSpec(
                key=AssetKey([key]),
                deps=[AssetSpec(key=AssetKey([dep_key])) for dep_key in dep_keys],
            )
        ],
        op_tags={"airlift/task_id": task_id, "airlift/dag_id": dag_id},
    )
    def the_asset():
        return 1

    return the_asset


def test_transitive_deps(airflow_instance: None) -> None:
    """Test that even with cross-dag transitive asset deps, the correct dependencies are generated for the asset graph."""
    instance = AirflowInstance(
        auth_backend=BasicAuthBackend(
            webserver_url="http://localhost:8080", username="admin", password="admin"
        ),
        name="airflow_instance",
    )
    cacheable_assets = AirflowCacheableAssetsDefinition(
        airflow_instance=instance,
        orchestrated_defs=Definitions(
            assets=[
                create_asset_for_task("one", "first", "first_one"),
                create_asset_for_task("two", "first", "first_two", dep_keys=["second_one"]),
                create_asset_for_task("three", "first", "first_three", dep_keys=["second_two"]),
                create_asset_for_task("one", "second", "second_one", dep_keys=["first_one"]),
                create_asset_for_task("two", "second", "second_two"),
            ]
        ),
        migration_state_override=None,
        poll_interval=1,
    )

    defs = Definitions(assets=[cacheable_assets])
    repository_def = defs.get_repository_def()
    assets_defs = repository_def.assets_defs_by_key
    assert len(assets_defs) == 7  # 5 tasks + 2 dags
    assert AssetKey(["airflow_instance", "dag", "first"]) in assets_defs
    dag_def = assets_defs[AssetKey(["airflow_instance", "dag", "first"])]
    spec = next(iter(dag_def.specs))
    deps_keys = {dep.asset_key for dep in spec.deps}
    assert deps_keys == {AssetKey(["first_two"]), AssetKey(["first_three"])}
    assert AssetKey(["airflow_instance", "dag", "second"]) in assets_defs
    dag_def = assets_defs[AssetKey(["airflow_instance", "dag", "second"])]
    spec = next(iter(dag_def.specs))
    deps_keys = {dep.asset_key for dep in spec.deps}
    assert deps_keys == {AssetKey(["second_one"]), AssetKey(["second_two"])}
