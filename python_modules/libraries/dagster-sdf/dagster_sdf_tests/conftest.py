import os
from pathlib import Path
from typing import Optional

import pytest
from dagster_sdf.sdf_cli_resource import SdfCliResource, SdfCliInvocation

from .sdf_workspaces import test_csv_123_path


def _create_sdf_invocation(
    workspace_dir: Path, run_project: bool = False, environment: Optional[str] = None
) -> SdfCliInvocation:
    sdf = SdfCliResource(
        workspace_dir=os.fspath(workspace_dir), global_config_flags=["--show=none", "--log-level=info", "--log-form=nested"]
    )

    sdf_invocation = sdf.cli(["compile"], environment=environment).wait()

    if run_project:
        sdf.cli(["run"], environment=environment, raise_on_error=False).wait()

    return sdf_invocation


@pytest.fixture(name="test_csv_123_invocation", scope="function")
def test_csv_123_invocation_fixture() -> SdfCliInvocation:
    return _create_sdf_invocation(test_csv_123_path)

@pytest.fixture(name="test_csv_123_target_dir", scope="function")
def test_csv_123_target_dir_fixture(test_csv_123_invocation: SdfCliInvocation) -> Path:
    return test_csv_123_invocation.target_dir
