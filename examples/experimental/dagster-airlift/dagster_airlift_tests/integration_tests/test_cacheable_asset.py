from dagster import Definitions, multi_asset
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster_airlift.core.airflow_cacheable_assets_def import AirflowCacheableAssetsDefinition
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.basic_auth import BasicAuthBackend
from dagster_airlift.core.migration_state import (
    AirflowMigrationState,
    DagMigrationState,
    TaskMigrationState,
)


def test_cacheable_asset(airflow_instance: None) -> None:
    instance = AirflowInstance(
        auth_backend=BasicAuthBackend(
            webserver_url="http://localhost:8080", username="admin", password="admin"
        ),
        name="airflow_instance",
    )
    # Cacheable assets with just dag peering.
    cacheable_assets = AirflowCacheableAssetsDefinition(airflow_instance=instance, poll_interval=1)
    definitions = Definitions(assets=[cacheable_assets])
    repository_def = definitions.get_repository_def()

    assets_defs = repository_def.assets_defs_by_key
    assert len(assets_defs) == 1
    assets_def = assets_defs[AssetKey(["airflow_instance", "dag", "print_dag"])]
    specs = list(assets_def.specs)
    assert len(specs) == 1
    assert specs[0].key.path == ["airflow_instance", "dag", "print_dag"]
    assert specs[0].tags == {"dagster/compute_kind": "airflow", "airlift/dag_id": "print_dag"}
    spec_metadata = specs[0].metadata
    assert set(spec_metadata.keys()) == {"Dag Info (raw)", "Dag ID", "Link to DAG", "Source Code"}

    # Now, create a cacheable assets with a task peering.

    # Set task mapping via tag
    @multi_asset(
        specs=[AssetSpec(key=AssetKey(["some", "key"]))],
        op_tags={"airlift/task_id": "print_task", "airlift/dag_id": "print_dag"},
    )
    def first_asset():
        return 1

    # Set task mapping via node name
    @multi_asset(
        specs=[
            AssetSpec(
                key=AssetKey(["other", "key"]), deps=[AssetSpec(key=AssetKey(["some", "key"]))]
            )
        ]
    )
    def print_dag__downstream_print_task():
        return 1

    cacheable_assets = AirflowCacheableAssetsDefinition(
        airflow_instance=instance,
        orchestrated_defs=Definitions(
            assets=[
                first_asset,
                print_dag__downstream_print_task,
            ]
        ),
        migration_state_override=AirflowMigrationState(
            dags={
                "print_dag": DagMigrationState(
                    tasks={
                        "print_task": TaskMigrationState(migrated=False),
                        "downstream_print_task": TaskMigrationState(migrated=False),
                    }
                )
            }
        ),
        poll_interval=1,
    )

    defs = Definitions(assets=[cacheable_assets])
    repository_def = defs.get_repository_def()
    assets_defs = repository_def.assets_defs_by_key
    assert len(assets_defs) == 3
    assert AssetKey(["airflow_instance", "dag", "print_dag"]) in assets_defs
    assert AssetKey(["some", "key"]) in assets_defs
    assert AssetKey(["other", "key"]) in assets_defs
    some_key_def = assets_defs[AssetKey(["some", "key"])]
    assert len(list(some_key_def.specs)) == 1
    assert next(iter(some_key_def.specs)).metadata.keys() == {
        "Task Info (raw)",
        "Dag ID",
        "Link to Task",
        "Computed in Task ID",
    }
    assert next(iter(some_key_def.specs)).tags["airlift/task_id"] == "print_task"
    assert next(iter(some_key_def.specs)).tags["airlift/dag_id"] == "print_dag"

    other_key_def = assets_defs[AssetKey(["other", "key"])]
    assert len(list(other_key_def.specs)) == 1
    assert next(iter(other_key_def.specs)).metadata.keys() == {
        "Task Info (raw)",
        "Dag ID",
        "Link to Task",
        "Computed in Task ID",
    }
    assert next(iter(other_key_def.specs)).tags["airlift/task_id"] == "downstream_print_task"
    assert next(iter(other_key_def.specs)).tags["airlift/dag_id"] == "print_dag"
    assert next(iter(other_key_def.specs)).deps == [AssetDep(AssetKey(["some", "key"]))]
