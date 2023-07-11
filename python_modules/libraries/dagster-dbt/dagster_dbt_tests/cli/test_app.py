import shutil
from pathlib import Path
from typing import Optional

import pytest
from dagster_dbt.cli.app import app
from typer.testing import CliRunner

test_dagster_metadata_dbt_project_path = Path(__file__).parent.joinpath(
    "..", "dbt_projects", "test_dagster_metadata"
)

runner = CliRunner()


@pytest.fixture(name="tmp_dbt_project")
def tmp_dbt_project_fixture(tmp_path: Path) -> Path:
    shutil.copytree(test_dagster_metadata_dbt_project_path, tmp_path)

    return tmp_path


@pytest.mark.parametrize("project_name", [None, "test"])
def test_project_scaffold_command(tmp_dbt_project: Path, project_name: Optional[str]) -> None:
    dagster_dbt_project_dir = tmp_dbt_project.joinpath("dagster")

    assert not dagster_dbt_project_dir.exists()

    expected_project_name = project_name or "test_dagster_metadata"
    project_name_args = ["--project-name", project_name] if project_name else []

    result = runner.invoke(
        app,
        [
            "project",
            "scaffold",
            *project_name_args,
            "--dbt-project-dir",
            tmp_dbt_project.as_posix(),
        ],
    )

    assert result.exit_code == 0
    assert f"Initializing Dagster project {expected_project_name}" in result.stdout
    assert "Your Dagster project has been initialized" in result.stdout
    assert dagster_dbt_project_dir.exists()
