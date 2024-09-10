from typing import List, Sequence, Tuple
from dagster import AssetKey, AssetSpec, Definitions, multi_asset, JsonMetadataValue
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from dagster_airlift.constants import AIRFLOW_MAPPING_METADATA_KEY
from dagster_airlift.core import dag_defs, task_defs

def build_valid_task_metadata(dag_and_tasks: List[Tuple[str, str]]) -> JsonMetadataValue:
    return JsonMetadataValue(
        [{"type": "task", "dag_id": dag_id, "task_id": task_id} for (dag_id, task_id) in dag_and_tasks]
    )

def build_valid_dag_metadata(dag_ids: Sequence[str]) -> JsonMetadataValue:
    return JsonMetadataValue(
        [{"type": "dag", "dag_id": dag_id} for dag_id in dag_ids]
    )

def from_specs(*specs: AssetSpec) -> Definitions:
    return Definitions(assets=specs)


def asset_spec(defs: Definitions, key: CoercibleToAssetKey) -> AssetSpec:
    ak = AssetKey.from_coercible(key)
    return defs.get_assets_def(ak).get_asset_spec(ak)


def test_dag_def_spec() -> None:
    defs = dag_defs(
        "dag_one",
        task_defs("task_one", from_specs(AssetSpec(key="asset_one"))),
    )
    assert asset_spec(defs, "asset_one").metadata[AIRFLOW_MAPPING_METADATA_KEY] == build_valid_task_metadata([("dag_one", "task_one")])


def test_dag_def_multi_tasks_multi_specs() -> None:
    defs = dag_defs(
        "dag_one",
        task_defs("task_one", from_specs(AssetSpec(key="asset_one"))),
        task_defs("task_two", from_specs(AssetSpec(key="asset_two"), AssetSpec(key="asset_three"))),
    )
    assert asset_spec(defs, "asset_one").metadata[AIRFLOW_MAPPING_METADATA_KEY] == build_valid_task_metadata([("dag_one", "task_one")])
    assert asset_spec(defs, "asset_two").metadata[AIRFLOW_MAPPING_METADATA_KEY] == build_valid_task_metadata([("dag_one", "task_two")]) 
    assert asset_spec(defs, "asset_three").metadata[AIRFLOW_MAPPING_METADATA_KEY] == build_valid_task_metadata([("dag_one", "task_two")])


def test_dag_def_assets_def() -> None:
    @multi_asset(specs=[AssetSpec(key="asset_one")])
    def an_asset() -> None: ...

    defs = dag_defs(
        "dag_one",
        task_defs("task_one", Definitions([an_asset])),
    )
    assert asset_spec(defs, "asset_one").metadata[AIRFLOW_MAPPING_METADATA_KEY] == build_valid_task_metadata([("dag_one", "task_one")])
    assert asset_spec(defs, "asset_one").metadata[AIRFLOW_MAPPING_METADATA_KEY] == build_valid_task_metadata([("dag_one", "task_one")])


def test_dag_def_defs() -> None:
    @multi_asset(specs=[AssetSpec(key="asset_one")])
    def an_asset() -> None: ...

    defs = dag_defs(
        "dag_one",
        task_defs("task_one", Definitions(assets=[an_asset])),
    )
    assert asset_spec(defs, "asset_one").metadata[AIRFLOW_MAPPING_METADATA_KEY] == build_valid_task_metadata([("dag_one", "task_one")])
    assert asset_spec(defs, "asset_one").metadata[AIRFLOW_MAPPING_METADATA_KEY] == build_valid_task_metadata([("dag_one", "task_one")])


def test_dag_def_spec_override() -> None:
    dag_spec = AssetSpec(key="dag_spec", metadata={"other": "metadata"})
    defs = dag_defs(
        "dag_one",
        spec=dag_spec,
    )
    assert defs.assets
    assert len(list(defs.assets)) == 1
    assert asset_spec(defs, "dag_spec").metadata["other"] == "metadata"
    assert asset_spec(defs, "dag_spec").metadata[AIRFLOW_MAPPING_METADATA_KEY] == build_valid_dag_metadata(["dag_one"])

def test_diff_tasks_same_spec() -> None:
    """Test that when two tasks have the same AssetSpec, we combine the metadata to represent both tasks."""
    defs = dag_defs(
        "dag_one",
        task_defs("task_one", from_specs(AssetSpec(key="asset_one"))),
        task_defs("task_two", from_specs(AssetSpec(key="asset_one"))),
    )
    assert asset_spec(defs, "asset_one").metadata[AIRFLOW_MAPPING_METADATA_KEY] == build_valid_task_metadata([("dag_one", "task_one"), ("dag_one", "task_two")])
