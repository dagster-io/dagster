import os
from pathlib import Path
from typing import Optional

import pytest
from dagster_sdf.resource import SdfCliInvocation, SdfCliResource

from .sdf_workspaces import lineage_path, moms_flower_shop_path


def _create_sdf_invocation(
    workspace_dir: Path, run_workspace: bool = False, environment: Optional[str] = None
) -> SdfCliInvocation:
    sdf = SdfCliResource(
        workspace_dir=os.fspath(workspace_dir), global_config_flags=["--log-form=nested"]
    )

    sdf_invocation = sdf.cli(["compile"], environment=environment).wait()

    if run_workspace:
        sdf.cli(["run"], environment=environment, raise_on_error=False).wait()

    return sdf_invocation


@pytest.fixture(name="lineage_invocation", scope="function")
def lineage_invocation_fixture() -> SdfCliInvocation:
    return _create_sdf_invocation(lineage_path)


@pytest.fixture(name="moms_flower_shop_invocation", scope="function")
def moms_flower_shop_invocation_fixture() -> SdfCliInvocation:
    return _create_sdf_invocation(moms_flower_shop_path)


@pytest.fixture(name="lineage_target_dir", scope="function")
def test_lineage_target_dir_fixture(lineage_invocation: SdfCliInvocation) -> Path:
    return lineage_invocation.target_dir


@pytest.fixture(name="moms_flower_shop_target_dir", scope="function")
def test_moms_flower_shop_target_dir_fixture(moms_flower_shop_invocation: SdfCliInvocation) -> Path:
    return moms_flower_shop_invocation.target_dir
