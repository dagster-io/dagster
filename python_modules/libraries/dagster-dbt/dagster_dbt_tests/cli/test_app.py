import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from dagster_dbt.cli.app import app
from typer.testing import CliRunner

if TYPE_CHECKING:
    from dagster import Definitions

pytest.importorskip("dbt.version", minversion="1.4")

test_dagster_metadata_dbt_project_path = Path(__file__).parent.joinpath(
    "..", "dbt_projects", "test_dagster_metadata"
)

runner = CliRunner()


@pytest.fixture(name="dbt_project_dir")
def dbt_project_dir_fixture(tmp_path: Path) -> Path:
    dbt_project_dir = tmp_path.joinpath("test_dagster_metadata")
    shutil.copytree(
        src=test_dagster_metadata_dbt_project_path,
        dst=dbt_project_dir,
    )

    return dbt_project_dir


def test_project_scaffold_command_with_precompiled_manifest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, dbt_project_dir: Path
) -> None:
    monkeypatch.chdir(tmp_path)

    project_name = "test_dagster_scaffold"
    dagster_project_dir = tmp_path.joinpath(project_name)

    result = runner.invoke(
        app,
        [
            "project",
            "scaffold",
            "--project-name",
            project_name,
            "--dbt-project-dir",
            os.fspath(dbt_project_dir),
        ],
    )

    assert result.exit_code == 0
    assert f"Initializing Dagster project {project_name}" in result.stdout
    assert "Your Dagster project has been initialized" in result.stdout
    assert dagster_project_dir.exists()
    assert dagster_project_dir.joinpath(project_name).exists()
    assert not any(path.suffix == ".jinja" for path in dagster_project_dir.glob("**/*"))
    assert "dbt-duckdb" in dagster_project_dir.joinpath("setup.py").read_text()

    subprocess.run(["dbt", "compile"], cwd=dbt_project_dir, check=True)

    assert dbt_project_dir.joinpath("target", "manifest.json").exists()

    monkeypatch.chdir(tmp_path)
    sys.path.append(os.fspath(tmp_path))

    defs: Definitions = getattr(
        importlib.import_module(f"{project_name}.{project_name}.definitions"),
        "defs",
    )

    materialize_dbt_models_job = defs.get_job_def("materialize_dbt_models")
    materialize_dbt_models_schedule = defs.get_schedule_def("materialize_dbt_models_schedule")

    result = materialize_dbt_models_job.execute_in_process()

    assert result.success
    assert materialize_dbt_models_schedule.cron_schedule == "0 0 * * *"


def test_project_scaffold_command_with_runtime_manifest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, dbt_project_dir: Path
) -> None:
    monkeypatch.chdir(tmp_path)

    project_name = "test_dagster_scaffold_runtime_manifest"
    dagster_project_dir = tmp_path.joinpath(project_name)

    result = runner.invoke(
        app,
        [
            "project",
            "scaffold",
            "--project-name",
            project_name,
            "--dbt-project-dir",
            os.fspath(dbt_project_dir),
        ],
    )

    assert result.exit_code == 0
    assert f"Initializing Dagster project {project_name}" in result.stdout
    assert "Your Dagster project has been initialized" in result.stdout
    assert dagster_project_dir.exists()
    assert dagster_project_dir.joinpath(project_name).exists()
    assert not any(path.suffix == ".jinja" for path in dagster_project_dir.glob("**/*"))
    assert not dbt_project_dir.joinpath("target", "manifest.json").exists()
    assert "dbt-duckdb" in dagster_project_dir.joinpath("setup.py").read_text()

    monkeypatch.chdir(tmp_path)
    sys.path.append(os.fspath(tmp_path))

    with pytest.raises(FileNotFoundError):
        monkeypatch.delenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD", raising=False)
        getattr(
            importlib.import_module(f"{project_name}.{project_name}.definitions"),
            "defs",
        )

    monkeypatch.setenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD", "1")

    defs: Definitions = getattr(
        importlib.import_module(f"{project_name}.{project_name}.definitions"),
        "defs",
    )

    materialize_dbt_models_job = defs.get_job_def("materialize_dbt_models")
    materialize_dbt_models_schedule = defs.get_schedule_def("materialize_dbt_models_schedule")

    result = materialize_dbt_models_job.execute_in_process()

    assert result.success
    assert materialize_dbt_models_schedule.cron_schedule == "0 0 * * *"


def test_project_scaffold_command_on_invalid_dbt_project(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)

    project_name = "test_dagster_scaffold_invalid_dbt_project"
    dagster_project_dir = tmp_path.joinpath(project_name)

    result = runner.invoke(
        app,
        [
            "project",
            "scaffold",
            "--project-name",
            project_name,
            "--dbt-project-dir",
            os.fspath(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert not dagster_project_dir.exists()
