import os
import re
from pathlib import Path

from click.testing import CliRunner
from dagster import file_relative_path
from dagster._cli.project import (
    from_example_command,
    scaffold_code_location_command,
    scaffold_command,
    scaffold_repository_command,
)
from dagster._core.workspace.load_target import get_origins_from_toml
from dagster._generate.download import AVAILABLE_EXAMPLES, EXAMPLES_TO_IGNORE, _get_url_for_version
from dagster._generate.generate import _should_skip_file


def test_project_scaffold_command_fails_when_dir_path_exists():
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("existing_dir")
        result = runner.invoke(scaffold_command, ["--name", "existing_dir"])
        assert "The directory" in result.output
        assert "already exists" in result.output
        assert result.exit_code != 0


def test_project_scaffold_command_fails_on_package_conflict():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(scaffold_command, ["--name", "dagster"])
        assert "conflicts with an existing PyPI package" in result.output
        assert result.exit_code != 0

        result = runner.invoke(scaffold_command, ["--name", "dagster", "--ignore-package-conflict"])
        assert result.exit_code == 0


def test_project_scaffold_command_succeeds():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(scaffold_command, ["--name", "my_dagster_project"])
        assert result.exit_code == 0
        assert Path("my_dagster_project").exists()
        assert Path("my_dagster_project/my_dagster_project/__init__.py").exists()
        assert Path("my_dagster_project/my_dagster_project_tests/__init__.py").exists()
        assert Path("my_dagster_project/README.md").exists()
        assert Path("my_dagster_project/pyproject.toml").exists()

        # test target loadable
        origins = get_origins_from_toml("my_dagster_project/pyproject.toml")
        assert len(origins) == 1
        assert origins[0].loadable_target_origin.module_name == "my_dagster_project.definitions"


def test_project_scaffold_command_excludes_succeeds():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            scaffold_command,
            ["--name", "diet_dagster", "--excludes", "setup", "--excludes", "tests"],
        )
        assert result.exit_code == 0
        assert Path("diet_dagster/pyproject.toml").exists()
        assert Path("diet_dagster/README.md").exists()
        assert not Path("diet_dagster/diet_dagster_tests/__init__.py").exists()
        assert not Path("diet_dagster/setup.cfg").exists()
        assert not Path("diet_dagster/setup.py").exists()


def test_project_scaffold_command_excludes_fails_on_required_files():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            scaffold_command,
            ["--name", "diet_dagster", "--excludes", "pyproject"],
        )
        assert result.exit_code != 0


def test_from_example_command_fails_when_example_not_available():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            from_example_command, ["--name", "my_dagster_project", "--example", "foo"]
        )
        assert re.match(r"Example .* not available", result.output)
        assert result.exit_code != 0


def test_from_example_command_succeeds():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            from_example_command,
            ["--name", "my_dagster_project", "--example", "assets_dbt_python"],
        )
        assert result.exit_code == 0
        assert Path("my_dagster_project").exists()
        assert Path("my_dagster_project/assets_dbt_python").exists()
        assert Path("my_dagster_project/assets_dbt_python_tests").exists()
        # ensure we filter out tox.ini because it's used in our own CI
        assert not Path("my_dagster_project/tox.ini").exists()


def test_from_example_command_versioned_succeeds():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            from_example_command,
            [
                "--name",
                "my_dagster_project",
                "--example",
                "assets_dbt_python",
                "--version",
                "1.3.11",
            ],
        )
        assert result.exit_code == 0
        assert Path("my_dagster_project").exists()
        assert Path("my_dagster_project/assets_dbt_python").exists()
        assert Path("my_dagster_project/assets_dbt_python_tests").exists()
        # ensure we filter out tox.ini because it's used in our own CI
        assert not Path("my_dagster_project/tox.ini").exists()


def test_from_example_command_default_name():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            from_example_command,
            ["--name", "assets_dbt_python", "--example", "assets_dbt_python"],
        )
        assert result.exit_code == 0
        assert Path("assets_dbt_python").exists()
        assert Path("assets_dbt_python/assets_dbt_python").exists()
        assert Path("assets_dbt_python/assets_dbt_python_tests").exists()
        # ensure we filter out tox.ini because it's used in our own CI
        assert not Path("assets_dbt_python/tox.ini").exists()


def test_available_examples_in_sync_with_example_folder():
    # ensure the list of AVAILABLE_EXAMPLES is in sync with the example folder minus EXAMPLES_TO_IGNORE
    example_folder = Path(file_relative_path(__file__, "../../../../examples"))
    available_examples_in_folder = [
        e
        for e in os.listdir(example_folder)
        if (
            Path(example_folder / e).exists()
            and e not in EXAMPLES_TO_IGNORE
            and not _should_skip_file(e)
        )
    ]
    assert set(available_examples_in_folder) == set(AVAILABLE_EXAMPLES)


#####################
# `dagster project scaffold-code-location` command is deprecated.


def test_scaffold_code_location_deprecation():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(scaffold_code_location_command, ["--name", "my_dagster_project"])
        assert re.match(
            "WARNING: command is deprecated. Use `dagster project scaffold --excludes readme` instead.",
            result.output.lstrip(),
        )


def test_scaffold_code_location_scaffold_command_fails_when_dir_path_exists():
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("existing_dir")
        result = runner.invoke(scaffold_code_location_command, ["--name", "existing_dir"])
        assert "The directory" in result.output
        assert "already exists" in result.output
        assert result.exit_code != 0


def test_scaffold_code_location_command_succeeds():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(scaffold_code_location_command, ["--name", "my_dagster_code"])
        assert result.exit_code == 0
        assert Path("my_dagster_code").exists()
        assert Path("my_dagster_code/my_dagster_code/__init__.py").exists()
        assert Path("my_dagster_code/my_dagster_code_tests/__init__.py").exists()
        assert Path("my_dagster_code/pyproject.toml").exists()

        # test target loadable
        origins = get_origins_from_toml("my_dagster_code/pyproject.toml")
        assert len(origins) == 1
        assert origins[0].loadable_target_origin.module_name == "my_dagster_code.definitions"


# `dagster project scaffold-repository` command is deprecated.
# We're keeping the tests below for backcompat.


def test_scaffold_repository_deprecation():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(scaffold_repository_command, ["--name", "my_dagster_project"])
        assert re.match(
            "WARNING: command is deprecated. Use `dagster project scaffold --excludes readme` instead.",
            result.output,
        )


def test_scaffold_repository_scaffold_command_fails_when_dir_path_exists():
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("existing_dir")
        result = runner.invoke(scaffold_repository_command, ["--name", "existing_dir"])
        assert re.match(r"The directory .* already exists", result.output)
        assert result.exit_code != 0


def test_scaffold_repository_command_succeeds():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(scaffold_repository_command, ["--name", "my_dagster_repo"])
        assert result.exit_code == 0
        assert Path("my_dagster_repo").exists()
        assert Path("my_dagster_repo/my_dagster_repo").exists()
        assert Path("my_dagster_repo/my_dagster_repo_tests").exists()
        assert not Path("my_dagster_repo/workspace.yaml").exists()


def test_versioned_download():
    assert _get_url_for_version("1.3.3").endswith("1.3.3")
    assert _get_url_for_version("1!0+dev").endswith("master")
