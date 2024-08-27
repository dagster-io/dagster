from typing import Sequence

from dagster import AssetKey, AssetSpec, Definitions, asset, multi_asset
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster_airlift.core import dag_defs, task_defs
from dagster_airlift.core.utils import DAG_ID_TAG, TASK_ID_TAG


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
    assert asset_spec(defs, "asset_one").tags[DAG_ID_TAG] == "dag_one"
    assert asset_spec(defs, "asset_one").tags[TASK_ID_TAG] == "task_one"


def test_dag_def_multi_tasks_multi_specs() -> None:
    defs = dag_defs(
        "dag_one",
        task_defs("task_one", from_specs(AssetSpec(key="asset_one"))),
        task_defs("task_two", from_specs(AssetSpec(key="asset_two"), AssetSpec(key="asset_three"))),
    )
    assert asset_spec(defs, "asset_one").tags[DAG_ID_TAG] == "dag_one"
    assert asset_spec(defs, "asset_one").tags[TASK_ID_TAG] == "task_one"
    assert asset_spec(defs, "asset_two").tags[DAG_ID_TAG] == "dag_one"
    assert asset_spec(defs, "asset_two").tags[TASK_ID_TAG] == "task_two"
    assert asset_spec(defs, "asset_three").tags[DAG_ID_TAG] == "dag_one"
    assert asset_spec(defs, "asset_three").tags[TASK_ID_TAG] == "task_two"


def test_dag_def_assets_def() -> None:
    @multi_asset(specs=[AssetSpec(key="asset_one")])
    def an_asset() -> None: ...

    defs = dag_defs(
        "dag_one",
        task_defs("task_one", Definitions([an_asset])),
    )
    assert asset_spec(defs, "asset_one").tags[DAG_ID_TAG] == "dag_one"
    assert asset_spec(defs, "asset_one").tags[TASK_ID_TAG] == "task_one"


def test_dag_def_defs() -> None:
    @multi_asset(specs=[AssetSpec(key="asset_one")])
    def an_asset() -> None: ...

    defs = dag_defs(
        "dag_one",
        task_defs("task_one", Definitions(assets=[an_asset])),
    )
    assert asset_spec(defs, "asset_one").tags[DAG_ID_TAG] == "dag_one"
    assert asset_spec(defs, "asset_one").tags[TASK_ID_TAG] == "task_one"


class DummyCacheableAssetsDefinition(CacheableAssetsDefinition):
    def __init__(self, asset_key: CoercibleToAssetKey) -> None:
        super().__init__(unique_id="unique_id")
        self.asset_key = AssetKey.from_coercible(asset_key)

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        return []

    def build_definitions(
        self, data: Sequence[AssetsDefinitionCacheableData]
    ) -> Sequence[AssetsDefinition]:
        @asset(key=self.asset_key)
        def an_asset() -> None: ...

        return [an_asset]


def test_dag_defs_cacheable_assets() -> None:
    defs = dag_defs(
        "dag1",
        task_defs("task1", Definitions(assets=[DummyCacheableAssetsDefinition("asset_1")])),
        task_defs("task2", Definitions(assets=[DummyCacheableAssetsDefinition("asset_2")])),
    )

    assets_def_asset_1 = defs.get_asset_graph().assets_def_for_key(AssetKey("asset_1"))

    assert isinstance(assets_def_asset_1, AssetsDefinition)
    assert assets_def_asset_1.key == AssetKey("asset_1")
    assert assets_def_asset_1.specs_by_key[AssetKey("asset_1")].tags == {
        "airlift/dag_id": "dag1",
        "airlift/task_id": "task1",
    }

    assets_def_asset_2 = defs.get_asset_graph().assets_def_for_key(AssetKey("asset_2"))
    assert assets_def_asset_2.key == AssetKey("asset_2")
    assert assets_def_asset_2.specs_by_key[AssetKey("asset_2")].tags == {
        "airlift/dag_id": "dag1",
        "airlift/task_id": "task2",
    }
