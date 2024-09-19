import shutil
from pathlib import Path

import pytest

from dagster_sdf_tests.sdf_workspaces import moms_flower_shop_path


@pytest.fixture(name="sdf_workspace_dir", scope="function")
def sdf_workspace_dir_fixture(tmp_path: Path) -> Path:
    sdf_workspace_dir = tmp_path.joinpath("test_moms_flower_shop")
    shutil.copytree(
        src=moms_flower_shop_path,
        dst=sdf_workspace_dir,
        # Ignore temporary files when copying the folder.
        ignore=shutil.ignore_patterns(
            "*.wal",
        ),
    )
    return sdf_workspace_dir
