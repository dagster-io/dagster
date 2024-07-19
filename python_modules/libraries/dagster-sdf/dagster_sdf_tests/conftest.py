import os
from pathlib import Path

import pytest
from dagster_sdf.constants import DEFAULT_SDF_WORKSPACE_ENVIRONMENT
from dagster_sdf.resource import SdfCliInvocation, SdfCliResource

from .sdf_workspaces import moms_flower_shop_path


def _create_sdf_invocation(
    workspace_dir: Path,
    run_workspace: bool = False,
    environment: str = DEFAULT_SDF_WORKSPACE_ENVIRONMENT,
) -> SdfCliInvocation:
    sdf = SdfCliResource(
        workspace_dir=os.fspath(workspace_dir), global_config_flags=["--log-form=nested"]
    )

    sdf_invocation = sdf.cli(["compile"], environment=environment).wait()

    if run_workspace:
        sdf.cli(["run"], environment=environment, raise_on_error=False).wait()

    return sdf_invocation


@pytest.fixture(name="moms_flower_shop_target_dir", scope="function")
def test_moms_flower_shop_target_dir_fixture() -> Path:
    return _create_sdf_invocation(moms_flower_shop_path).target_dir
