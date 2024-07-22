from pathlib import Path

import pytest
from dagster._check import CheckError
from dagster._core.test_utils import environ
from dagster_sdf.information_schema import SdfInformationSchema

from .sdf_workspaces import moms_flower_shop_path


def test_local_dev(tmp_path: Path) -> None:
    with pytest.raises(CheckError):
        _ = SdfInformationSchema(workspace_dir=moms_flower_shop_path, target_dir=tmp_path)
    with environ({"DAGSTER_IS_DEV_CLI": "1"}):
        info_schema = SdfInformationSchema(workspace_dir=moms_flower_shop_path, target_dir=tmp_path)
        assert info_schema.information_schema_dir.exists()


def test_opt_in_env_var(tmp_path: Path) -> None:
    with pytest.raises(CheckError):
        _ = SdfInformationSchema(workspace_dir=moms_flower_shop_path, target_dir=tmp_path)
    with environ({"DAGSTER_SDF_COMPILE_ON_LOAD": "1"}):
        info_schema = SdfInformationSchema(workspace_dir=moms_flower_shop_path, target_dir=tmp_path)
        assert info_schema.information_schema_dir.exists()
