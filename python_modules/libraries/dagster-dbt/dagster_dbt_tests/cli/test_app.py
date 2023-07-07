import shutil
from pathlib import Path

from dagster_dbt.cli.app import app
from typer.testing import CliRunner

test_dagster_metadata_dbt_project_path = Path(__file__).parent.joinpath(
    "..", "dbt_projects", "test_dagster_metadata"
)

runner = CliRunner()


def test_project_scaffold_command(tmp_path: Path) -> None:
    shutil.copytree(test_dagster_metadata_dbt_project_path, tmp_path)

    dagster_dbt_project_dir = tmp_path.joinpath("dagster")

    assert not dagster_dbt_project_dir.exists()

    result = runner.invoke(
        app,
        [
            "project",
            "scaffold",
            "--project-name",
            "test",
            "--dbt-project-dir",
            tmp_path.as_posix(),
        ],
    )

    assert result.exit_code == 0
    assert "Your Dagster project has been initialized" in result.stdout
    assert dagster_dbt_project_dir.exists()
