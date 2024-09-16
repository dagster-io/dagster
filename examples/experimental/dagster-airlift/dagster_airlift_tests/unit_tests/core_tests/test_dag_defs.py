# ruff: noqa: SLF001

from dagster import AssetKey, AssetSpec, Definitions, multi_asset
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.cacheable_assets import PrefixOrGroupWrappedCacheableAssetsDefinition
from dagster_airlift.constants import AIRFLOW_COUPLING_METADATA_KEY, DAG_ID_METADATA_KEY
from dagster_airlift.core import DagDefs, dag_defs, mark_as_shared, task_defs
from dagster_airlift.core.dag_defs import resolve_defs

from dagster_airlift_tests.unit_tests.conftest import dag_defs_with_override


def from_specs(*specs: AssetSpec) -> Definitions:
    return Definitions(assets=specs)


def asset_spec(defs: DagDefs, key: CoercibleToAssetKey) -> AssetSpec:
    ak = AssetKey.from_coercible(key)
    return resolve_defs([defs], {}).get_assets_def(ak).get_asset_spec(ak)


def asset_spec_from_defs(definitions: Definitions, key: CoercibleToAssetKey) -> AssetSpec:
    ak = AssetKey.from_coercible(key)
    return definitions.get_assets_def(ak).get_asset_spec(ak)


def test_dag_def_spec() -> None:
    defs = dag_defs(
        "dag_one",
        [
            task_defs("task_one", from_specs(AssetSpec(key="asset_one"))),
        ],
    )
    assert asset_spec(defs, "asset_one").metadata[AIRFLOW_COUPLING_METADATA_KEY].value == [
        ("dag_one", "task_one")
    ]


def test_dag_def_multi_tasks_multi_specs() -> None:
    defs = dag_defs(
        "dag_one",
        [
            task_defs("task_one", from_specs(AssetSpec(key="asset_one"))),
            task_defs(
                "task_two", from_specs(AssetSpec(key="asset_two"), AssetSpec(key="asset_three"))
            ),
        ],
    )
    assert asset_spec(defs, "asset_one").metadata[AIRFLOW_COUPLING_METADATA_KEY].value == [
        ("dag_one", "task_one")
    ]
    assert asset_spec(defs, "asset_two").metadata[AIRFLOW_COUPLING_METADATA_KEY].value == [
        ("dag_one", "task_two")
    ]
    assert asset_spec(defs, "asset_three").metadata[AIRFLOW_COUPLING_METADATA_KEY].value == [
        ("dag_one", "task_two")
    ]


def test_dag_def_assets_def() -> None:
    @multi_asset(specs=[AssetSpec(key="asset_one")])
    def an_asset() -> None: ...

    defs = dag_defs(
        "dag_one",
        [
            task_defs("task_one", Definitions([an_asset])),
        ],
    )
    assert asset_spec(defs, "asset_one").metadata[AIRFLOW_COUPLING_METADATA_KEY].value == [
        ("dag_one", "task_one")
    ]


def test_dag_def_defs() -> None:
    @multi_asset(specs=[AssetSpec(key="asset_one")])
    def an_asset() -> None: ...

    defs = dag_defs(
        "dag_one",
        [
            task_defs("task_one", Definitions(assets=[an_asset])),
        ],
    )
    assert asset_spec(defs, "asset_one").metadata[AIRFLOW_COUPLING_METADATA_KEY].value == [
        ("dag_one", "task_one")
    ]


def test_dag_defs_task_refs() -> None:
    """Test that we can sub in a sentinel instead of task defs, and that they can be correctly resolved."""
    defs_one = dag_defs(
        "dag_one",
        [
            task_defs("shared", mark_as_shared("my_key")),
            task_defs("not_shared", from_specs(AssetSpec(key="not_shared_key"))),
        ],
    )
    defs_two = dag_defs(
        "dag_two",
        [
            task_defs("also_shared", mark_as_shared("my_key")),
        ],
    )
    definitions = resolve_defs([defs_one, defs_two], {"my_key": from_specs(AssetSpec(key="foo"))})
    assert definitions.assets is not None
    assert len(list(definitions.assets)) == 2
    assert {a.key for a in definitions.assets} == {AssetKey("foo"), AssetKey("not_shared_key")}  # type: ignore
    assert asset_spec_from_defs(definitions, "foo").metadata[
        AIRFLOW_COUPLING_METADATA_KEY
    ].value == [
        ("dag_one", "shared"),
        ("dag_two", "also_shared"),
    ]


def test_provide_override() -> None:
    """Test that overridden assets are correctly tagged with the DAG ID."""
    defs = dag_defs_with_override()
    transformed_defs = defs.construct_dag_level_defs()
    assert transformed_defs.assets is not None
    assert len(list(transformed_defs.assets)) == 3
    a_asset = next(
        iter(
            asset
            for asset in transformed_defs.assets
            if isinstance(asset, AssetSpec) and asset.key == AssetKey("a")
        )
    )
    assert a_asset.metadata[DAG_ID_METADATA_KEY] == "dag_one"

    # Expect that b_asset should be transformed to an AssetsDefinition, and that it should be tagged with the DAG ID.
    b_asset = next(
        iter(
            asset
            for asset in transformed_defs.assets
            if isinstance(asset, AssetsDefinition) and asset.key == AssetKey("b")
        )
    )
    assert len(list(b_asset.specs)) == 1
    b_spec = next(iter(spec for spec in b_asset.specs if spec.key == AssetKey("b")))
    assert b_spec.metadata[DAG_ID_METADATA_KEY] == "dag_one"

    # Expect that the cacheable assets definition should be transformed to a PrefixOrGroupWrappedCacheableAssetsDefinition, and that it should be tagged with the DAG ID.
    cache_asset = next(
        iter(
            asset
            for asset in transformed_defs.assets
            if isinstance(asset, PrefixOrGroupWrappedCacheableAssetsDefinition)
            and asset._wrapped.unique_id == "c"
        )
    )
    assert cache_asset._metadata_for_all_assets is not None
    assert cache_asset._metadata_for_all_assets[DAG_ID_METADATA_KEY] == "dag_one"
