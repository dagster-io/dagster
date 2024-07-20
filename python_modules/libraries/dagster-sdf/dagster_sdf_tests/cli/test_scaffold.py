import os
import subprocess
import sys
from pathlib import Path

import pytest
from dagster_sdf.cli.app import app
from typer.testing import CliRunner

runner = CliRunner()


def _assert_scaffold_invocation(
    project_name: str,
    sdf_workspace_dir: Path,
    dagster_project_dir: Path,
) -> None:
    result = runner.invoke(
        app,
        [
            "workspace",
            "scaffold",
            "--project-name",
            project_name,
            "--sdf-workspace-dir",
            os.fspath(sdf_workspace_dir),
        ],
    )

    assert result.exit_code == 0
    assert f"Initializing Dagster project {project_name}" in result.stdout
    assert "Your Dagster project has been initialized" in result.stdout
    assert dagster_project_dir.exists()
    assert dagster_project_dir.joinpath(project_name).exists()
    assert not any(path.suffix == ".jinja" for path in dagster_project_dir.glob("**/*"))
    assert "dagster-sdf" in dagster_project_dir.joinpath("setup.py").read_text()


def test_project_scaffold_command(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sdf_workspace_dir: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    project_name = "test_dagster_scaffold"
    dagster_project_dir = tmp_path.joinpath(project_name)

    _assert_scaffold_invocation(
        project_name=project_name,
        sdf_workspace_dir=sdf_workspace_dir,
        dagster_project_dir=dagster_project_dir,
    )

    subprocess.run(["sdf", "compile"], cwd=sdf_workspace_dir, check=True)

    assert sdf_workspace_dir.joinpath("sdftarget", "dbg").exists()

    monkeypatch.chdir(tmp_path)
    sys.path.append(os.fspath(tmp_path))


def test_project_scaffold_command_on_invalid_dagster_project_name(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, sdf_workspace_dir: Path
) -> None:
    monkeypatch.chdir(tmp_path)

    project_name = "test-dagster-scaffold-invalid-dagster-project-name"
    dagster_project_dir = tmp_path.joinpath(project_name)

    result = runner.invoke(
        app,
        [
            "workspace",
            "scaffold",
            "--project-name",
            project_name,
            "--sdf-workspace-dir",
            os.fspath(sdf_workspace_dir),
        ],
    )

    assert result.exit_code != 0
    assert not dagster_project_dir.exists()


def test_project_scaffold_command_on_invalid_sdf_project_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)

    project_name = "test_dagster_scaffold_invalid_sdf_project"
    dagster_project_dir = tmp_path.joinpath(project_name)

    result = runner.invoke(
        app,
        [
            "workspace",
            "scaffold",
            "--project-name",
            project_name,
            "--sdf-workspace-dir",
            os.fspath(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert not dagster_project_dir.exists()


@pytest.mark.parametrize("project_name", ["dagster", "dagster_sdf"])
def test_project_scaffold_command_on_package_conflict(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, sdf_workspace_dir: Path, project_name: str
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "workspace",
            "scaffold",
            "--project-name",
            project_name,
            "--sdf-workspace-dir",
            os.fspath(sdf_workspace_dir),
        ],
    )

    assert result.exit_code != 0

    result = runner.invoke(
        app,
        [
            "workspace",
            "scaffold",
            "--project-name",
            project_name,
            "--sdf-workspace-dir",
            os.fspath(sdf_workspace_dir),
            "--ignore-package-conflict",
        ],
    )

    assert result.exit_code == 0
