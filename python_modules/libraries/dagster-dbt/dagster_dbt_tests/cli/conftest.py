import shutil
from pathlib import Path

import pytest

from dagster_dbt_tests.dbt_projects import test_jaffle_shop_path


@pytest.fixture(name="dbt_project_dir", scope="function")
def dbt_project_dir_fixture(tmp_path: Path) -> Path:
    dbt_project_dir = tmp_path.joinpath("test_jaffle_shop")
    shutil.copytree(
        src=test_jaffle_shop_path,
        dst=dbt_project_dir,
        # Ignore temporary files when copying the folder.
        ignore=shutil.ignore_patterns(
            "*.wal",
        ),
    )

    return dbt_project_dir
