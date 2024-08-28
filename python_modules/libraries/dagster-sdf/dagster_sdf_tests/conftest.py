import os
from pathlib import Path

import pytest
from dagster_sdf.constants import DEFAULT_SDF_WORKSPACE_ENVIRONMENT
from dagster_sdf.resource import SdfCliResource

from dagster_sdf_tests.sdf_workspaces import (
    lineage_asset_checks_path,
    lineage_upstream_path,
    moms_flower_shop_path,
    quoted_tables_path,
)


def _create_sdf_invocation(
    workspace_dir: Path,
    run_workspace: bool = False,
    environment: str = DEFAULT_SDF_WORKSPACE_ENVIRONMENT,
):
    sdf = SdfCliResource(workspace_dir=os.fspath(workspace_dir))

    sdf_invocation = sdf.cli(
        ["compile", "--save", "table-deps"], environment=environment, raise_on_error=False
    ).wait()

    if run_workspace:
        sdf.cli(
            ["run", "--save", "info-schema"], environment=environment, raise_on_error=True
        ).wait()

    return sdf_invocation


@pytest.fixture(name="moms_flower_shop_target_dir", scope="function")
def test_moms_flower_shop_target_dir_fixture() -> Path:
    return _create_sdf_invocation(moms_flower_shop_path).target_dir


@pytest.fixture(name="lineage_upstream_target_dir", scope="function")
def test_lineage_upstream_target_dir_fixture() -> Path:
    return _create_sdf_invocation(lineage_upstream_path).target_dir


@pytest.fixture(name="lineage_asset_checks_target_dir", scope="function")
def test_lineage_asset_checks_dir_fixture() -> Path:
    return _create_sdf_invocation(lineage_asset_checks_path).target_dir


@pytest.fixture(name="quoted_tables_target_dir", scope="function")
def test_quoted_tables_dir_fixture() -> Path:
    return _create_sdf_invocation(quoted_tables_path).target_dir
