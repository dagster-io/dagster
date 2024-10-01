from pathlib import Path

import pytest
from dagster._check import CheckError
from dagster._core.test_utils import environ
from dagster_sdf.sdf_information_schema import SdfInformationSchema
from dagster_sdf.sdf_workspace import SdfWorkspace

from dagster_sdf_tests.sdf_workspaces import moms_flower_shop_path


def test_local_dev(tmp_path: Path) -> None:
    with pytest.raises(CheckError):
        workspace = SdfWorkspace(workspace_dir=moms_flower_shop_path, target_dir=tmp_path)
        info_schema = SdfInformationSchema(
            workspace_dir=workspace.workspace_dir, target_dir=workspace.target_dir
        )
    with environ({"DAGSTER_IS_DEV_CLI": "1"}):
        workspace = SdfWorkspace(workspace_dir=moms_flower_shop_path, target_dir=tmp_path)
        info_schema = SdfInformationSchema(
            workspace_dir=workspace.workspace_dir, target_dir=workspace.target_dir
        )
        assert info_schema.is_parsed()


def test_opt_in_env_var(tmp_path: Path) -> None:
    with pytest.raises(CheckError):
        workspace = SdfWorkspace(workspace_dir=moms_flower_shop_path, target_dir=tmp_path)
        info_schema = SdfInformationSchema(
            workspace_dir=workspace.workspace_dir, target_dir=workspace.target_dir
        )
    with environ({"DAGSTER_SDF_COMPILE_ON_LOAD": "1"}):
        workspace = SdfWorkspace(workspace_dir=moms_flower_shop_path, target_dir=tmp_path)
        info_schema = SdfInformationSchema(
            workspace_dir=workspace.workspace_dir, target_dir=workspace.target_dir
        )
        assert info_schema.is_parsed()
