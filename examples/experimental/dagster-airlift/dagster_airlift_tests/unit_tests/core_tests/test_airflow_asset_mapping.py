from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster_airlift.constants import DAG_ID_METADATA_KEY, TASK_ID_METADATA_KEY
from dagster_airlift.core.serialization.compute import build_task_spec_mapping_info


def ak(key: str) -> AssetKey:
    return AssetKey(key)


def airlift_asset_spec(key: CoercibleToAssetKey, dag_id: str, task_id: str) -> AssetSpec:
    return AssetSpec(key=key, metadata={DAG_ID_METADATA_KEY: dag_id, TASK_ID_METADATA_KEY: task_id})


def test_build_task_spec_mapping_info_no_mapping() -> None:
    spec_mapping_info = build_task_spec_mapping_info(
        defs=Definitions(assets=[AssetSpec("asset1"), AssetSpec("asset2")])
    )
    assert len(spec_mapping_info.asset_keys) == 2
    assert len(spec_mapping_info.dag_ids) == 0
    assert not (spec_mapping_info.asset_key_map)


def test_build_single_task_spec() -> None:
    spec_mapping_info = build_task_spec_mapping_info(
        defs=Definitions(assets=[airlift_asset_spec("asset1", "dag1", "task1")])
    )
    assert spec_mapping_info.dag_ids == {"dag1"}
    assert spec_mapping_info.task_id_map == {"dag1": {"task1"}}
    assert spec_mapping_info.asset_keys_per_dag_id == {"dag1": {ak("asset1")}}
    assert spec_mapping_info.asset_key_map == {"dag1": {"task1": {ak("asset1")}}}


def test_task_with_multiple_assets() -> None:
    spec_mapping_info = build_task_spec_mapping_info(
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
