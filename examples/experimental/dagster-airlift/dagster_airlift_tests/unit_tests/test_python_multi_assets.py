from dagster import AssetDep, AssetKey, AssetsDefinition, AssetSpec
from dagster_airlift.core import PythonDefs

from dagster_airlift_tests.unit_tests.multi_asset_python import compute_fn


def ak(key: str) -> AssetKey:
    return AssetKey.from_user_string(key)


def test_python_multi_asset_factory() -> None:
    from .multi_asset_python import compute_called

    assert not compute_called[0]
    asset_spec = AssetSpec(
        key=ak("my/asset"),
        deps=[AssetDep(ak("upstream/asset"))],
    )
    defs = PythonDefs(
        specs=[asset_spec],
        python_fn=compute_fn,
        name="test_dag__test_task",
    ).build_defs()

    assert len(defs.assets) == 1  # type: ignore
    assets_def: AssetsDefinition = defs.assets[0]  # type: ignore
    assert assets_def.is_executable
    assert len(assets_def.specs) == 1  # type: ignore
    assert assets_def.node_def.name == "test_dag__test_task"
    spec = list(assets_def.specs)[0]  # noqa
    assert spec.key == AssetKey(["my", "asset"])
    assert spec.deps == [AssetDep(asset=AssetKey(["upstream", "asset"]))]
    result = defs.get_implicit_global_asset_job_def().execute_in_process()
    assert result.success
    assert compute_called[0]
