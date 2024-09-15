from dagster import AssetKey, AssetSpec, Definitions, multi_asset
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from dagster_airlift.constants import AIRFLOW_COUPLING_METADATA_KEY
from dagster_airlift.core import DagDefs, dag_defs, mark_as_shared, task_defs
from dagster_airlift.core.dag_defs import resolve_defs


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
