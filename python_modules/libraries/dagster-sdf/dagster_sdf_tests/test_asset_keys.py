from pathlib import Path

from dagster import AssetKey
from dagster_sdf.asset_decorator import sdf_assets
from dagster_sdf.asset_utils import get_asset_key_for_table_id
from dagster_sdf.sdf_workspace import SdfWorkspace

from dagster_sdf_tests.sdf_workspaces import quoted_tables_path


def test_quoted_asset_keys(quoted_tables_target_dir: Path) -> None:
    @sdf_assets(
        workspace=SdfWorkspace(
            workspace_dir=quoted_tables_path, target_dir=quoted_tables_target_dir
        )
    )
    def quoted_tables_assets(): ...

    assert quoted_tables_assets.asset_deps == {
        AssetKey(["QUOTED_TABLES", "PUB", "2020_table_a"]): set(),
        AssetKey(["QUOTED_TABLES", "PUB", "2020_table_b"]): {
            AssetKey(["QUOTED_TABLES", "PUB", "2020_table_a"])
        },
    }

    asset_key = get_asset_key_for_table_id(
        [quoted_tables_assets], 'QUOTED_TABLES.PUB."2020_table_a"'
    )
    assert asset_key == AssetKey(["QUOTED_TABLES", "PUB", "2020_table_a"])
