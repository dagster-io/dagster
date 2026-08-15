import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import ANY, patch

import dagster as dg
import pytest
from dagster._core.definitions.definitions_load_context import DefinitionsLoadType
from dagster._core.definitions.repository_definition.repository_definition import RepositoryLoadData
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.instance_for_test import instance_for_test
from dagster._utils.env import environ
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.testing import create_defs_folder_sandbox
from dagster_dbt import DbtProjectComponent
from dagster_dbt.dbt_project_manager import (
    _GIT_CLONE_TIMEOUT_SECONDS,
    RemoteGitDbtProjectManager,
    _shallow_clone,
)

_SHALLOW_CLONE = "dagster_dbt.dbt_project_manager._shallow_clone"
_SUBPROCESS_RUN = "dagster_dbt.dbt_project_manager.subprocess.run"

# Path to the jaffle shop test project
STUB_LOCATION_PATH = Path(__file__).parent / "code_locations" / "dbt_project_location"
JAFFLE_SHOP_DBT_PROJECT = STUB_LOCATION_PATH / "defs/jaffle_shop_dbt/jaffle_shop"


@pytest.fixture(scope="module")
def dbt_project_dir() -> Iterator[Path]:
    """Create a dbt project that we'll copy from for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_project = Path(temp_dir) / "jaffle_shop"
        shutil.copytree(JAFFLE_SHOP_DBT_PROJECT, temp_project)
        yield temp_project


def mock_git_clone(dbt_project_dir: Path):
    """Create a mock function that simulates git clone by copying the prepared project."""

    def _clone(repo_url: str, dest: Path, **_kwargs):
        # we expect dest to be an empty directory
        assert dest.exists()
        assert dest.is_dir()
        assert not any(dest.iterdir())
        # Instead of actually cloning, copy our prepared test project
        shutil.copytree(dbt_project_dir, dest, dirs_exist_ok=True)

    return _clone


def test_remote_dbt_project_dev_mode_calls_fetch(dbt_project_dir: Path) -> None:
    """Test that loading with DAGSTER_IS_DEV_CLI=1 calls fetch and loads assets."""
    repo_url = "https://github.com/fake/repo.git"

    with (
        instance_for_test(),
        create_defs_folder_sandbox() as sandbox,
        patch(_SHALLOW_CLONE) as mock_clone,
        environ({"DAGSTER_IS_DEV_CLI": "1"}),
    ):
        mock_clone.side_effect = mock_git_clone(dbt_project_dir)

        defs_path = sandbox.scaffold_component(
            component_cls=DbtProjectComponent,
            defs_yaml_contents={
                "type": "dagster_dbt.DbtProjectComponent",
                "attributes": {
                    "project": {
                        "repo_url": repo_url,
                        "repo_relative_path": ".",
                    },
                },
            },
            defs_path="remote_dbt",
        )

        with (
            scoped_definitions_load_context() as load_context,
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            assert isinstance(component, DbtProjectComponent)
            assert isinstance(component.project, RemoteGitDbtProjectManager)

            # In dev mode, should automatically fetch and have assets
            specs = defs.resolve_all_asset_specs()
            assert len(specs) > 0

            # Verify we have the expected assets from jaffle_shop
            asset_keys = {spec.key for spec in specs}
            assert dg.AssetKey("customers") in asset_keys
            assert dg.AssetKey("orders") in asset_keys

            # fetch should have been called once in dev mode
            mock_clone.assert_called_once()

            # Verify the state key was accessed
            assert load_context.accessed_defs_state_info is not None

            expected_key = f"DbtProjectComponent[{repo_url}]"
            assert expected_key in load_context.accessed_defs_state_info.info_mapping


def test_remote_dbt_project_reconstruction_mode_no_fetch(dbt_project_dir: Path) -> None:
    """Test that loading in RECONSTRUCTION mode with state doesn't call fetch again."""
    with (
        instance_for_test(),
        create_defs_folder_sandbox() as sandbox,
        patch(_SHALLOW_CLONE) as mock_clone,
    ):
        mock_clone.side_effect = mock_git_clone(dbt_project_dir)

        defs_path = sandbox.scaffold_component(
            component_cls=DbtProjectComponent,
            defs_yaml_contents={
                "type": "dagster_dbt.DbtProjectComponent",
                "attributes": {
                    "project": {
                        "repo_url": "https://github.com/fake/repo.git",
                        "repo_relative_path": ".",
                    },
                },
            },
            defs_path="remote_dbt",
        )

        # First, do a dev mode load to populate the state
        with (
            environ({"DAGSTER_IS_DEV_CLI": "1"}),
            scoped_definitions_load_context() as first_load_context,
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            specs = defs.resolve_all_asset_specs()
            assert len(specs) > 0

            # Should have been called once during dev mode load
            assert mock_clone.call_count == 1

            # Get the state info for reconstruction
            state_info = first_load_context.accessed_defs_state_info
            assert state_info is not None

        # Reset the mock to verify it's not called again
        mock_clone.reset_mock()

        # Now load in RECONSTRUCTION mode with the state
        with (
            scoped_definitions_load_context(
                load_type=DefinitionsLoadType.RECONSTRUCTION,
                repository_load_data=RepositoryLoadData(
                    cacheable_asset_data={},
                    reconstruction_metadata={},
                    defs_state_info=state_info,
                ),
            ) as reconstruction_context,
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            assert isinstance(component, DbtProjectComponent)
            assert isinstance(component.project, RemoteGitDbtProjectManager)

            # Should still have assets from the state
            specs = defs.resolve_all_asset_specs()
            assert len(specs) > 0

            # Verify we have the expected assets
            asset_keys = {spec.key for spec in specs}
            assert dg.AssetKey("customers") in asset_keys
            assert dg.AssetKey("orders") in asset_keys

            # fetch should NOT have been called again in reconstruction mode
            mock_clone.assert_not_called()

            # Verify the state key was accessed
            assert reconstruction_context.accessed_defs_state_info is not None


def test_remote_dbt_project_with_profile_and_repo_relative_path(
    dbt_project_dir: Path,
) -> None:
    """Test RemoteGitDbtProject with repo_relative_path configured."""
    repo_url = "https://github.com/fake/repo2.git"

    with (
        instance_for_test(),
        create_defs_folder_sandbox() as sandbox,
        patch(_SHALLOW_CLONE) as mock_clone,
        environ({"DAGSTER_IS_DEV_CLI": "1"}),
    ):
        mock_clone.side_effect = mock_git_clone(dbt_project_dir)

        defs_path = sandbox.scaffold_component(
            component_cls=DbtProjectComponent,
            defs_yaml_contents={
                "type": "dagster_dbt.DbtProjectComponent",
                "attributes": {
                    "project": {
                        "repo_url": repo_url,
                        "repo_relative_path": ".",
                    },
                },
            },
            defs_path="remote_dbt",
        )

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            assert isinstance(component, DbtProjectComponent)
            assert isinstance(component.project, RemoteGitDbtProjectManager)
            assert component.project.repo_relative_path == "."

            # Should have assets
            specs = defs.resolve_all_asset_specs()
            assert len(specs) > 0

            # fetch should have been called in dev mode
            mock_clone.assert_called_once()


def test_remote_dbt_project_with_token(dbt_project_dir: Path) -> None:
    """Test RemoteGitDbtProject with authentication token."""
    repo_url = "https://github.com/fake/repo3.git"
    repo_url_with_token = "https://fake_token_12345@github.com/fake/repo3.git"

    with (
        instance_for_test(),
        create_defs_folder_sandbox() as sandbox,
        patch(_SHALLOW_CLONE) as mock_clone,
        environ({"DAGSTER_IS_DEV_CLI": "1"}),
    ):
        mock_clone.side_effect = mock_git_clone(dbt_project_dir)

        defs_path = sandbox.scaffold_component(
            component_cls=DbtProjectComponent,
            defs_yaml_contents={
                "type": "dagster_dbt.DbtProjectComponent",
                "attributes": {
                    "project": {
                        "repo_url": repo_url,
                        "token": "fake_token_12345",
                        "repo_relative_path": ".",
                    },
                },
            },
            defs_path="remote_dbt",
        )

        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            assert isinstance(component, DbtProjectComponent)
            assert isinstance(component.project, RemoteGitDbtProjectManager)
            assert component.project.token == "fake_token_12345"

            # Should have assets in dev mode
            specs = defs.resolve_all_asset_specs()
            assert len(specs) > 0

            # fetch should have been called
            mock_clone.assert_called_once_with(repo_url_with_token, ANY, display_url=repo_url)


@pytest.mark.parametrize("project_path", [None, "."])
def test_scaffold_component_with_git_url_params(
    dbt_project_dir: Path, project_path: str | None
) -> None:
    """Test that the scaffolder creates a loadable component when invoked with git_url params."""
    repo_url = "https://github.com/fake/repo_scaffold.git"

    with (
        instance_for_test(),
        create_defs_folder_sandbox() as sandbox,
        patch(_SHALLOW_CLONE) as mock_clone,
        environ({"DAGSTER_IS_DEV_CLI": "1"}),
    ):
        mock_clone.side_effect = mock_git_clone(dbt_project_dir)

        # Invoke scaffolder with git_url params (no defs_yaml_contents to use scaffolder output)
        defs_path = sandbox.scaffold_component(
            component_cls=DbtProjectComponent,
            scaffold_params={"git_url": repo_url, "project_path": project_path},
            defs_path="remote_dbt_scaffold",
        )

        # Verify the component can be loaded without error
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, _defs),
        ):
            assert isinstance(component, DbtProjectComponent)
            assert isinstance(component.project, RemoteGitDbtProjectManager)
            assert component.project.repo_url == repo_url
            # Component instantiated successfully - no error means the scaffolder created valid YAML


def _assert_shallow_clone_argv(mock_run, repo_url: str, dest: Path) -> None:
    assert mock_run.call_args.args[0] == [
        "git",
        "clone",
        "--depth",
        "1",
        "--",
        repo_url,
        str(dest),
    ]


def test_shallow_clone_invokes_git_cli(tmp_path: Path) -> None:
    dest = tmp_path / "project"
    dest.mkdir()
    repo_url = "https://github.com/fake/repo.git"
    completed = subprocess.CompletedProcess(
        args=["git", "clone", "--depth", "1", "--", repo_url, str(dest)],
        returncode=0,
        stdout="",
        stderr="",
    )

    with patch(_SUBPROCESS_RUN, return_value=completed) as mock_run:
        _shallow_clone(repo_url, dest)

    _assert_shallow_clone_argv(mock_run, repo_url, dest)
    assert mock_run.call_args.kwargs["stdin"] is subprocess.DEVNULL
    assert mock_run.call_args.kwargs["timeout"] == _GIT_CLONE_TIMEOUT_SECONDS
    assert mock_run.call_args.kwargs["env"]["GIT_TERMINAL_PROMPT"] == "0"


def test_shallow_clone_missing_executable(tmp_path: Path) -> None:
    dest = tmp_path / "project"
    dest.mkdir()
    repo_url = "https://github.com/fake/repo.git"

    with patch(
        _SUBPROCESS_RUN, side_effect=FileNotFoundError(2, "No such file or directory", "git")
    ) as mock_run:
        with pytest.raises(DagsterInvalidDefinitionError, match="git executable not found"):
            _shallow_clone(repo_url, dest)

    _assert_shallow_clone_argv(mock_run, repo_url, dest)


def test_shallow_clone_nonzero_exit(tmp_path: Path) -> None:
    dest = tmp_path / "project"
    dest.mkdir()
    repo_url = "https://secret_token@github.com/fake/repo.git"
    display_url = "https://github.com/fake/repo.git"
    failed = subprocess.CompletedProcess(
        args=["git", "clone", "--depth", "1", "--", repo_url, str(dest)],
        returncode=128,
        stdout="",
        stderr=f"fatal: repository '{repo_url}/' not found",
    )

    with patch(_SUBPROCESS_RUN, return_value=failed) as mock_run:
        with pytest.raises(DagsterInvalidDefinitionError, match="Failed to clone") as exc_info:
            _shallow_clone(repo_url, dest, display_url=display_url)

    _assert_shallow_clone_argv(mock_run, repo_url, dest)
    message = str(exc_info.value)
    assert "secret_token" not in message
    assert display_url in message
