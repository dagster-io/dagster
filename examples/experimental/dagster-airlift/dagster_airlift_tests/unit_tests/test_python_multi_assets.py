from pathlib import Path

from dagster import AssetDep, AssetKey, AssetsDefinition
from dagster_airlift import PythonDefs, load_defs_from_yaml


def test_load_defs_from_yaml() -> None:
    from .multi_asset_python import compute_called

    assert not compute_called[0]
    multi_asset_dir = Path(__file__).parent / "python_multi_assets_yaml"
    defs = load_defs_from_yaml(multi_asset_dir, defs_cls=PythonDefs)
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
