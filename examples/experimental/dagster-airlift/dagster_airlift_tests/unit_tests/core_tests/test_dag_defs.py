from dagster import AssetKey, AssetSpec, Definitions, multi_asset
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from dagster_airlift.constants import TASK_MAPPING_METADATA_KEY
from dagster_airlift.core import assets_with_task_mappings, dag_defs, task_defs


def from_specs(*specs: AssetSpec) -> Definitions:
    return Definitions(assets=specs)


def asset_spec(defs: Definitions, key: CoercibleToAssetKey) -> AssetSpec:
    ak = AssetKey.from_coercible(key)
    return defs.get_assets_def(ak).get_asset_spec(ak)


def has_single_task_handle(spec: AssetSpec, dag_id: str, task_id: str) -> bool:
    assert len(spec.metadata[TASK_MAPPING_METADATA_KEY]) == 1
    task_handle_dict = next(iter(spec.metadata[TASK_MAPPING_METADATA_KEY]))
    return task_handle_dict["dag_id"] == dag_id and task_handle_dict["task_id"] == task_id


def test_dag_def_spec() -> None:
    defs = dag_defs(
        "dag_one",
        task_defs("task_one", from_specs(AssetSpec(key="asset_one"))),
    )
    assert has_single_task_handle(asset_spec(defs, "asset_one"), "dag_one", "task_one")


def test_task_mappings_spec() -> None:
    defs = Definitions(
        assets=assets_with_task_mappings(
            dag_id="dag_one",
            task_mappings={
                "task_one": [AssetSpec(key="asset_one")],
            },
        )
    )
    assert has_single_task_handle(asset_spec(defs, "asset_one"), "dag_one", "task_one")


def test_dag_def_multi_tasks_multi_specs() -> None:
    defs = dag_defs(
        "dag_one",
        task_defs("task_one", from_specs(AssetSpec(key="asset_one"))),
        task_defs("task_two", from_specs(AssetSpec(key="asset_two"), AssetSpec(key="asset_three"))),
    )
    assert has_single_task_handle(asset_spec(defs, "asset_one"), "dag_one", "task_one")
    assert has_single_task_handle(asset_spec(defs, "asset_two"), "dag_one", "task_two")
    assert has_single_task_handle(asset_spec(defs, "asset_three"), "dag_one", "task_two")


def test_task_mappings_multi_tasks_multi_specs() -> None:
    defs = Definitions(
        assets=assets_with_task_mappings(
            dag_id="dag_one",
            task_mappings={
                "task_one": [AssetSpec(key="asset_one")],
                "task_two": [AssetSpec(key="asset_two"), AssetSpec(key="asset_three")],
            },
        )
    )
    assert has_single_task_handle(asset_spec(defs, "asset_one"), "dag_one", "task_one")
    assert has_single_task_handle(asset_spec(defs, "asset_two"), "dag_one", "task_two")
    assert has_single_task_handle(asset_spec(defs, "asset_three"), "dag_one", "task_two")


def test_dag_def_assets_def() -> None:
    @multi_asset(specs=[AssetSpec(key="asset_one")])
    def an_asset() -> None: ...

    defs = dag_defs(
        "dag_one",
        task_defs("task_one", Definitions([an_asset])),
    )
    assert has_single_task_handle(asset_spec(defs, "asset_one"), "dag_one", "task_one")


def test_task_mappings_assets_def() -> None:
    @multi_asset(specs=[AssetSpec(key="asset_one")])
    def an_asset() -> None: ...

    defs = Definitions(
        assets=assets_with_task_mappings(
            dag_id="dag_one",
            task_mappings={"task_one": [an_asset]},
        )
    )
    assert has_single_task_handle(asset_spec(defs, "asset_one"), "dag_one", "task_one")
