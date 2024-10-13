import datetime
from typing import List

from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster_airlift.constants import TASK_MAPPING_METADATA_KEY
from dagster_airlift.core.airflow_defs_data import AirflowDefinitionsData
from dagster_airlift.core.airflow_instance import DagInfo
from dagster_airlift.core.load_defs import build_full_automapped_dags_from_airflow_instance
from dagster_airlift.core.serialization.compute import (
    FetchedAirflowData,
    TaskHandle,
    build_airlift_metadata_mapping_info,
    fetch_all_airflow_data,
)
from dagster_airlift.core.serialization.serialized_data import TaskInfo
from dagster_airlift.core.utils import metadata_for_task_mapping
from dagster_airlift.test import AirflowInstanceFake
from dagster_airlift.test.airflow_test_instance import make_dag_run, make_instance


def ak(key: str) -> AssetKey:
    return AssetKey.from_user_string(key)


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
        mapping_info=build_airlift_metadata_mapping_info(
            defs=Definitions(
                assets=[
                    airlift_asset_spec("asset1", "dag1", "task1"),
                    airlift_asset_spec("asset2", "dag1", "task2"),
                ]
            )
        ),
    )

    all_mapped_tasks = fetched_airflow_data.all_mapped_tasks
    assert all_mapped_tasks.keys() == {ak("asset1"), ak("asset2")}
    assert all_mapped_tasks[ak("asset1")] == {TaskHandle(dag_id="dag1", task_id="task1")}


def test_produce_fetched_airflow_data() -> None:
    mapping_info = build_airlift_metadata_mapping_info(
        defs=Definitions(
            assets=[
                airlift_asset_spec("asset1", "dag1", "task1"),
                AssetSpec("asset2", deps=[ak("asset1")]),
            ]
        )
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
    assert len(fetched_airflow_data.mapping_info.asset_specs) == 2
    assert fetched_airflow_data.mapping_info.downstream_deps == {ak("asset1"): {ak("asset2")}}


def test_automapped_loaded_data() -> None:
    airflow_instance = make_instance(
        dag_and_task_structure={"dag1": ["task1", "task2"]},
        dag_runs=[
            make_dag_run(
                dag_id="dag1",
                run_id="run1",
                start_date=datetime.datetime.now(),
                end_date=datetime.datetime.now(),
            ),
        ],
        task_deps={"task1": ["task2"]},
        instance_name="test_instance",
    )

    defs = build_full_automapped_dags_from_airflow_instance(
        airflow_instance=airflow_instance,
    )

    airflow_data = AirflowDefinitionsData(airflow_instance=airflow_instance, mapped_defs=defs)

    assert airflow_data.task_ids_in_dag("dag1") == {"task1", "task2"}
