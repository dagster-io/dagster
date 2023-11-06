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

test_dagster_metadata_dbt_project_path = (
    Path(__file__).joinpath("..", "..", "dbt_projects", "test_dagster_metadata").resolve()
)

runner = CliRunner()


@pytest.fixture(name="disable_openblas_threading_affinity")
def disable_openblas_threading_affinity_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENBLAS_MAIN_FREE", "1")
    monkeypatch.setenv("GOTOBLAS_MAIN_FREE", "1")


@pytest.fixture(name="dbt_project_dir")
def dbt_project_dir_fixture(tmp_path: Path, disable_openblas_threading_affinity) -> Path:
    dbt_project_dir = tmp_path.joinpath("test_dagster_metadata")
    shutil.copytree(
        src=test_dagster_metadata_dbt_project_path,
        dst=dbt_project_dir,
    )

    return dbt_project_dir


def _assert_scaffold_invocation(
    project_name: str,
    dbt_project_dir: Path,
    dagster_project_dir: Path,
    use_dbt_project_package_data_dir: bool,
) -> None:
    result = runner.invoke(
        app,
        [
            "project",
            "scaffold",
            "--project-name",
            project_name,
            "--dbt-project-dir",
            os.fspath(dbt_project_dir),
            *(["--use-dbt-project-package-data-dir"] if use_dbt_project_package_data_dir else []),
        ],
    )

    assert result.exit_code == 0
    assert f"Initializing Dagster project {project_name}" in result.stdout
    assert "Your Dagster project has been initialized" in result.stdout
    assert dagster_project_dir.exists()
    assert dagster_project_dir.joinpath(project_name).exists()
    assert not any(path.suffix == ".jinja" for path in dagster_project_dir.glob("**/*"))
    assert "dbt-duckdb" in dagster_project_dir.joinpath("setup.py").read_text()


def _assert_scaffold_defs(project_name: str, dagster_project_dir: Path) -> None:
    schedules_py_path = dagster_project_dir.joinpath(project_name, "schedules.py")
    schedules_py_path.write_text(schedules_py_path.read_text().replace("# ", ""))

    scaffold_defs_module = importlib.import_module(f"{project_name}.{project_name}.definitions")
    defs: Definitions = getattr(scaffold_defs_module, "defs")

    materialize_dbt_models_job = defs.get_job_def("materialize_dbt_models")
    materialize_dbt_models_schedule = defs.get_schedule_def("materialize_dbt_models_schedule")

    result = materialize_dbt_models_job.execute_in_process()

    assert result.success
    assert materialize_dbt_models_schedule.cron_schedule == "0 0 * * *"


def _update_dbt_project_path(
    dbt_project_dir: Path,
    dagster_project_dir: Path,
    use_dbt_project_package_data_dir: bool,
) -> Path:
    if use_dbt_project_package_data_dir:
        dbt_project_dir = dagster_project_dir.joinpath("dbt-project")
        shutil.copytree(
            src=test_dagster_metadata_dbt_project_path,
            dst=dbt_project_dir,
        )

    return dbt_project_dir


@pytest.mark.parametrize("use_dbt_project_package_data_dir", [True, False])
def test_project_scaffold_command_with_precompiled_manifest(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    dbt_project_dir: Path,
    use_dbt_project_package_data_dir: bool,
) -> None:
    monkeypatch.chdir(tmp_path)

    project_name = f"test_dagster_scaffold_precompiled_manifest_{use_dbt_project_package_data_dir}"
    dagster_project_dir = tmp_path.joinpath(project_name)

    _assert_scaffold_invocation(
        project_name=project_name,
        dbt_project_dir=dbt_project_dir,
        dagster_project_dir=dagster_project_dir,
        use_dbt_project_package_data_dir=use_dbt_project_package_data_dir,
    )

    dbt_project_dir = _update_dbt_project_path(
        dbt_project_dir=dbt_project_dir,
        dagster_project_dir=dagster_project_dir,
        use_dbt_project_package_data_dir=use_dbt_project_package_data_dir,
    )

    subprocess.run(["dbt", "compile"], cwd=dbt_project_dir, check=True)

    assert dbt_project_dir.joinpath("target", "manifest.json").exists()

    monkeypatch.chdir(tmp_path)
    sys.path.append(os.fspath(tmp_path))

    _assert_scaffold_defs(project_name=project_name, dagster_project_dir=dagster_project_dir)


@pytest.mark.parametrize("use_dbt_project_package_data_dir", [True, False])
def test_project_scaffold_command_with_runtime_manifest(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    dbt_project_dir: Path,
    use_dbt_project_package_data_dir: bool,
) -> None:
    monkeypatch.chdir(tmp_path)

    project_name = f"test_dagster_scaffold_runtime_manifest_{use_dbt_project_package_data_dir}"
    dagster_project_dir = tmp_path.joinpath(project_name)

    _assert_scaffold_invocation(
        project_name=project_name,
        dbt_project_dir=dbt_project_dir,
        dagster_project_dir=dagster_project_dir,
        use_dbt_project_package_data_dir=use_dbt_project_package_data_dir,
    )

    dbt_project_dir = _update_dbt_project_path(
        dbt_project_dir=dbt_project_dir,
        dagster_project_dir=dagster_project_dir,
        use_dbt_project_package_data_dir=use_dbt_project_package_data_dir,
    )

    monkeypatch.setenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD", "1")
    monkeypatch.chdir(tmp_path)
    sys.path.append(os.fspath(tmp_path))

    _assert_scaffold_defs(project_name=project_name, dagster_project_dir=dagster_project_dir)


@pytest.mark.parametrize("use_dbt_project_package_data_dir", [True, False])
def test_project_scaffold_command_with_runtime_manifest_without_env_var(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    dbt_project_dir: Path,
    use_dbt_project_package_data_dir: bool,
) -> None:
    monkeypatch.chdir(tmp_path)

    project_name = f"test_scaffold_runtime_without_env_var_{use_dbt_project_package_data_dir}"
    dagster_project_dir = tmp_path.joinpath(project_name)

    _assert_scaffold_invocation(
        project_name=project_name,
        dbt_project_dir=dbt_project_dir,
        dagster_project_dir=dagster_project_dir,
        use_dbt_project_package_data_dir=use_dbt_project_package_data_dir,
    )

    dbt_project_dir = _update_dbt_project_path(
        dbt_project_dir=dbt_project_dir,
        dagster_project_dir=dagster_project_dir,
        use_dbt_project_package_data_dir=use_dbt_project_package_data_dir,
    )

    monkeypatch.chdir(tmp_path)
    sys.path.append(os.fspath(tmp_path))

    with pytest.raises(FileNotFoundError):
        monkeypatch.delenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD", raising=False)
        importlib.import_module(f"{project_name}.{project_name}.definitions")


def test_project_scaffold_command_on_invalid_dagster_project_name(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, dbt_project_dir: Path
) -> None:
    monkeypatch.chdir(tmp_path)

    project_name = "test-dagster-scaffold-invalid-dagster-project-name"
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

    assert result.exit_code != 0
    assert not dagster_project_dir.exists()


def test_project_scaffold_command_on_invalid_dbt_project_dir(
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


@pytest.mark.parametrize("project_name", ["dagster", "dagster_dbt"])
def test_project_scaffold_command_on_package_conflict(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, dbt_project_dir: Path, project_name: str
) -> None:
    monkeypatch.chdir(tmp_path)

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

    assert result.exit_code != 0

    result = runner.invoke(
        app,
        [
            "project",
            "scaffold",
            "--project-name",
            project_name,
            "--dbt-project-dir",
            os.fspath(dbt_project_dir),
            "--ignore-package-conflict",
        ],
    )

    assert result.exit_code == 0
