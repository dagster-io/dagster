from dagster import AssetKey, AssetSpec, Definitions, multi_asset
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from dagster_airlift.constants import DAG_ID_METADATA_KEY, TASK_ID_METADATA_KEY
from dagster_airlift.core import dag_defs, task_defs


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
    assert asset_spec(defs, "asset_one").metadata[DAG_ID_METADATA_KEY] == "dag_one"
    assert asset_spec(defs, "asset_one").metadata[TASK_ID_METADATA_KEY] == "task_one"


def test_dag_def_multi_tasks_multi_specs() -> None:
    defs = dag_defs(
        "dag_one",
        task_defs("task_one", from_specs(AssetSpec(key="asset_one"))),
        task_defs("task_two", from_specs(AssetSpec(key="asset_two"), AssetSpec(key="asset_three"))),
    )
    assert asset_spec(defs, "asset_one").metadata[DAG_ID_METADATA_KEY] == "dag_one"
    assert asset_spec(defs, "asset_one").metadata[TASK_ID_METADATA_KEY] == "task_one"
    assert asset_spec(defs, "asset_two").metadata[DAG_ID_METADATA_KEY] == "dag_one"
    assert asset_spec(defs, "asset_two").metadata[TASK_ID_METADATA_KEY] == "task_two"
    assert asset_spec(defs, "asset_three").metadata[DAG_ID_METADATA_KEY] == "dag_one"
    assert asset_spec(defs, "asset_three").metadata[TASK_ID_METADATA_KEY] == "task_two"


def test_dag_def_assets_def() -> None:
    @multi_asset(specs=[AssetSpec(key="asset_one")])
    def an_asset() -> None: ...

    defs = dag_defs(
        "dag_one",
        task_defs("task_one", Definitions([an_asset])),
    )
    assert asset_spec(defs, "asset_one").metadata[DAG_ID_METADATA_KEY] == "dag_one"
    assert asset_spec(defs, "asset_one").metadata[TASK_ID_METADATA_KEY] == "task_one"


def test_dag_def_defs() -> None:
    @multi_asset(specs=[AssetSpec(key="asset_one")])
    def an_asset() -> None: ...

    defs = dag_defs(
        "dag_one",
        task_defs("task_one", Definitions(assets=[an_asset])),
    )
    assert asset_spec(defs, "asset_one").metadata[DAG_ID_METADATA_KEY] == "dag_one"
    assert asset_spec(defs, "asset_one").metadata[TASK_ID_METADATA_KEY] == "task_one"
