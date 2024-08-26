from dagster import (
    AssetDep,
    AssetKey,
    AssetsDefinition,
    AssetSpec,
    _check as check,
)
from dagster_airlift.core.python_callable import defs_for_python_callable

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

    defs = defs_for_python_callable(
        name="test_task", asset_specs=[asset_spec], python_callable=compute_fn
    )

    assets = check.is_list(defs.assets, of_type=AssetsDefinition)
    assert len(assets) == 1
    assets_def: AssetsDefinition = assets[0]
    assert assets_def.is_executable
    assert len(list(assets_def.specs)) == 1
    assert assets_def.node_def.name == "test_task"
    spec = next(iter(assets_def.specs))
    assert spec.key == AssetKey(["my", "asset"])
    assert spec.deps == [AssetDep(asset=AssetKey(["upstream", "asset"]))]
    result = defs.get_implicit_global_asset_job_def().execute_in_process()
    assert result.success
    assert compute_called[0]
