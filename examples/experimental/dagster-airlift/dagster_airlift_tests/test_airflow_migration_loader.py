from pathlib import Path

from dagster import AssetDep, AssetKey, AssetsDefinition
from dagster_airlift import AirflowMigrationLoader


def test_migration_loader() -> None:
    from .fake_compute import compute_called

    migration_path = Path(__file__).parent / "airflow_migration_project" / "unmigrated.yaml"
    asset_spec_path = Path(__file__).parent / "airflow_migration_project" / "asset_specs"
    loader = AirflowMigrationLoader(
        migration_yaml_path=migration_path, asset_specs_path=asset_spec_path
    )
    defs = loader.load_defs()
    assert len(defs.assets) == 1  # type: ignore
    assets_def: AssetsDefinition = defs.assets[0]  # type: ignore
    assert len(assets_def.specs) == 1  # type: ignore
    assert assets_def.node_def.name == "test_dag__test_task"
    spec = list(assets_def.specs)[0]  # noqa
    assert spec.key == AssetKey(["my", "asset"])
    assert spec.deps == [AssetDep(asset=AssetKey(["upstream", "asset"]))]

    # attempt to materialize my/asset. It shouldn't call the compute function, since it's still unmigrated
    result = defs.get_implicit_global_asset_job_def().execute_in_process()
    assert result.success
    assert not compute_called[0]

    # Create another loader with the migrated task. It should now call the compute function
    migration_path = Path(__file__).parent / "airflow_migration_project" / "migrated.yaml"
    defs = AirflowMigrationLoader(
        migration_yaml_path=migration_path, asset_specs_path=asset_spec_path
    ).load_defs()

    result = defs.get_implicit_global_asset_job_def().execute_in_process()
    assert result.success
    assert compute_called[0]
