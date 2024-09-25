from typing import List

from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster_airlift.constants import TASK_MAPPING_METADATA_KEY
from dagster_airlift.core.airflow_instance import DagInfo, TaskInfo
from dagster_airlift.core.serialization.compute import (
    FetchedAirflowData,
    TaskHandle,
    build_airlift_metadata_mapping_info,
    fetch_all_airflow_data,
)
from dagster_airlift.core.utils import metadata_for_task_mapping
from dagster_airlift.migration_state import (
    AirflowMigrationState,
    DagMigrationState,
    TaskMigrationState,
)
from dagster_airlift.test import AirflowInstanceFake


def ak(key: str) -> AssetKey:
    return AssetKey(key)


def airlift_asset_spec(key: CoercibleToAssetKey, dag_id: str, task_id: str) -> AssetSpec:
    return AssetSpec(key=key, metadata=metadata_for_task_mapping(task_id=task_id, dag_id=dag_id))


def airlift_multiple_task_asset_spec(
    key: CoercibleToAssetKey, handles: List[TaskHandle]
) -> AssetSpec:
    return AssetSpec(
        key=key, metadata={TASK_MAPPING_METADATA_KEY: [handle._asdict() for handle in handles]}
    )


def test_build_task_mapping_info_no_mapping() -> None:
    spec_mapping_info = build_airlift_metadata_mapping_info(
        defs=Definitions(assets=[AssetSpec("asset1"), AssetSpec("asset2")])
    )
    assert len(spec_mapping_info.dag_ids) == 0
    assert not (spec_mapping_info.asset_key_map)
    assert not (spec_mapping_info.task_handle_map)


def test_build_single_task_spec() -> None:
    spec_mapping_info = build_airlift_metadata_mapping_info(
        defs=Definitions(assets=[airlift_asset_spec("asset1", "dag1", "task1")])
    )
    assert spec_mapping_info.dag_ids == {"dag1"}
    assert spec_mapping_info.task_id_map == {"dag1": {"task1"}}
    assert spec_mapping_info.asset_keys_per_dag_id == {"dag1": {ak("asset1")}}
    assert spec_mapping_info.asset_key_map == {"dag1": {"task1": {ak("asset1")}}}
    assert spec_mapping_info.task_handle_map == {
        ak("asset1"): set([TaskHandle(dag_id="dag1", task_id="task1")])
    }


def test_task_with_multiple_assets() -> None:
    spec_mapping_info = build_airlift_metadata_mapping_info(
        defs=Definitions(
            assets=[
                airlift_asset_spec("asset1", "dag1", "task1"),
                airlift_asset_spec("asset2", "dag1", "task1"),
                airlift_asset_spec("asset3", "dag1", "task1"),
                airlift_asset_spec("asset4", "dag2", "task1"),
            ]
        )
    )

    assert spec_mapping_info.dag_ids == {"dag1", "dag2"}
    assert spec_mapping_info.task_id_map == {"dag1": {"task1"}, "dag2": {"task1"}}
    assert spec_mapping_info.asset_keys_per_dag_id == {
        "dag1": {ak("asset1"), ak("asset2"), ak("asset3")},
        "dag2": {ak("asset4")},
    }
    assert spec_mapping_info.asset_key_map == {
        "dag1": {"task1": {ak("asset1"), ak("asset2"), ak("asset3")}},
        "dag2": {"task1": {ak("asset4")}},
    }

    assert spec_mapping_info.task_handle_map == {
        ak("asset1"): set([TaskHandle(dag_id="dag1", task_id="task1")]),
        ak("asset2"): set([TaskHandle(dag_id="dag1", task_id="task1")]),
        ak("asset3"): set([TaskHandle(dag_id="dag1", task_id="task1")]),
        ak("asset4"): set([TaskHandle(dag_id="dag2", task_id="task1")]),
    }


def test_map_multiple_tasks_to_single_asset() -> None:
    spec_mapping_info = build_airlift_metadata_mapping_info(
        defs=Definitions(
            assets=[
                airlift_multiple_task_asset_spec(
                    "asset1",
                    [
                        TaskHandle(dag_id="dag1", task_id="task1"),
                        TaskHandle(dag_id="dag2", task_id="task1"),
                    ],
                ),
            ]
        )
    )

    assert spec_mapping_info.dag_ids == {"dag1", "dag2"}
    assert spec_mapping_info.task_id_map == {"dag1": {"task1"}, "dag2": {"task1"}}
    assert spec_mapping_info.asset_keys_per_dag_id == {
        "dag1": {ak("asset1")},
        "dag2": {ak("asset1")},
    }

    assert spec_mapping_info.asset_key_map == {
        "dag1": {"task1": {ak("asset1")}},
        "dag2": {"task1": {ak("asset1")}},
    }

    assert spec_mapping_info.task_handle_map == {
        ak("asset1"): set(
            [TaskHandle(dag_id="dag1", task_id="task1"), TaskHandle(dag_id="dag2", task_id="task1")]
        )
    }


def test_fetched_airflow_data() -> None:
    ws_url = "http://localhost:8080"

    fetched_airflow_data = FetchedAirflowData(
        dag_infos={
            "dag1": DagInfo(
                webserver_url=ws_url,
                dag_id="dag1",
                metadata={},
            )
        },
        task_info_map={
            "dag1": {
                "task1": TaskInfo(
                    webserver_url=ws_url, dag_id="dag1", task_id="task1", metadata={}
                ),
                "task2": TaskInfo(
                    webserver_url=ws_url, dag_id="dag1", task_id="task2", metadata={}
                ),
            }
        },
        migration_state=AirflowMigrationState(
            dags={
                "dag1": DagMigrationState(
                    {
                        "task1": TaskMigrationState(task_id="task1", migrated=True),
                        "task2": TaskMigrationState(task_id="task2", migrated=False),
                    }
                )
            },
        ),
        mapping_info=build_airlift_metadata_mapping_info(
            defs=Definitions(
                assets=[
                    airlift_asset_spec("asset1", "dag1", "task1"),
                    airlift_asset_spec("asset2", "dag1", "task2"),
                ]
            )
        ),
    )

    assert fetched_airflow_data.migration_state_map == {"dag1": {"task1": True, "task2": False}}

    airflow_data_by_key = fetched_airflow_data.airflow_data_by_key
    assert airflow_data_by_key.keys() == {ak("asset1"), ak("asset2")}

    assert "Dag ID" in fetched_airflow_data.airflow_data_by_key[ak("asset1")].additional_metadata


def test_produce_fetched_airflow_data() -> None:
    mapping_info = build_airlift_metadata_mapping_info(
        defs=Definitions(assets=[airlift_asset_spec("asset1", "dag1", "task1")])
    )

    instance = AirflowInstanceFake(
        dag_infos=[
            DagInfo(
                dag_id="dag1",
                metadata={"file_token": "dummy_file_token"},
                webserver_url="http://localhost:8080",
            )
        ],
        task_infos=[
            TaskInfo(
                dag_id="dag1",
                task_id="task1",
                metadata={},
                webserver_url="http://localhost:8080",
            )
        ],
        task_instances=[],
        dag_runs=[],
    )

    fetched_airflow_data = fetch_all_airflow_data(
        airflow_instance=instance,
        mapping_info=mapping_info,
    )

    assert len(fetched_airflow_data.mapping_info.mapped_asset_specs) == 1
