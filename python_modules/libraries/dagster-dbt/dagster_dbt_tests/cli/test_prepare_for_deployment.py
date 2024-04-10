import importlib
import os
import shutil
import sys
from pathlib import Path
from typing import cast

import pytest
from dagster import AssetsDefinition, materialize
from dagster_dbt.cli.app import app
from dagster_dbt.core.resources_v2 import DbtCliResource
from dagster_dbt.dbt_project import DbtProject
from typer.testing import CliRunner

runner = CliRunner()


@pytest.mark.parametrize("use_dbt_project_package_data_dir", [True, False])
def test_prepare_for_deployment(
    monkeypatch: pytest.MonkeyPatch, dbt_project_dir: Path, use_dbt_project_package_data_dir: bool
) -> None:
    monkeypatch.chdir(dbt_project_dir)

    project_name = "jaffle_dagster"
    dagster_project_dir = dbt_project_dir.joinpath(project_name)

    result = runner.invoke(
        app,
        [
            "project",
            "scaffold",
            "--project-name",
            project_name,
            "--dbt-project-dir",
            os.fspath(dbt_project_dir),
            *(
                ["--use-dbt-project-package-data-dir"]
                if use_dbt_project_package_data_dir
                else ["--use-experimental-dbt-project"]
            ),
        ],
    )

    assert result.exit_code == 0

    manifest_path = dbt_project_dir.joinpath("target", "manifest.json")
    packaged_project_dir = (
        dagster_project_dir.joinpath("dbt-project") if use_dbt_project_package_data_dir else None
    )

    assert not manifest_path.exists()
    assert not packaged_project_dir or not packaged_project_dir.exists()

    result = runner.invoke(
        app,
        [
            "project",
            "prepare-for-deployment",
            "--file",
            os.fspath(dagster_project_dir.joinpath(project_name, "project.py")),
        ],
    )

    assert result.exit_code == 0
    assert manifest_path.exists()
    assert not packaged_project_dir or packaged_project_dir.exists()


def test_prepare_for_deployment_with_state(
    monkeypatch: pytest.MonkeyPatch, dbt_project_dir: Path
) -> None:
    monkeypatch.setenv("DAGSTER_DBT_JAFFLE_SCHEMA", "prod")
    monkeypatch.chdir(dbt_project_dir)
    sys.path.append(os.fspath(dbt_project_dir))

    project_name = "jaffle_dagster"
    dagster_project_dir = dbt_project_dir.joinpath(project_name)
    dbt_project_file_path = dagster_project_dir.joinpath(project_name, "project.py")

    result = runner.invoke(
        app,
        [
            "project",
            "scaffold",
            "--project-name",
            project_name,
            "--dbt-project-dir",
            os.fspath(dbt_project_dir),
            "--use-experimental-dbt-state",
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        app,
        ["project", "prepare-for-deployment", "--file", os.fspath(dbt_project_file_path)],
    )
    assert result.exit_code == 0

    scaffold_defs_module = importlib.import_module(f"{project_name}.{project_name}.definitions")
    my_dbt_assets = cast(AssetsDefinition, getattr(scaffold_defs_module, "jaffle_shop_dbt_assets"))
    project = cast(DbtProject, getattr(scaffold_defs_module, "jaffle_shop_project"))
    dbt = DbtCliResource(project_dir=project)

    assert dbt.state_path

    # Running in production produces all the assets.
    result = materialize([my_dbt_assets], resources={"dbt": dbt})
    assert result.success

    # Running in staging should fail because the state directory is empty, so there is no --defer.
    monkeypatch.setenv("DAGSTER_DBT_JAFFLE_SCHEMA", "staging")
    result = materialize(
        [my_dbt_assets], selection="orders", resources={"dbt": dbt}, raise_on_error=False
    )
    assert not result.success

    # Once the state directory is populated, the subselected asset can be produced.
    Path(dbt.state_path).mkdir(exist_ok=True)
    shutil.copyfile(project.manifest_path, Path(dbt.state_path).joinpath("manifest.json"))

    result = runner.invoke(
        app,
        ["project", "prepare-for-deployment", "--file", os.fspath(dbt_project_file_path)],
    )
    assert result.exit_code == 0

    result = materialize([my_dbt_assets], selection="orders", resources={"dbt": dbt})
    assert result.success
