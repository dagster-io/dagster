import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import dagster as dg
import pytest
from dagster._core.definitions.definitions_load_context import DefinitionsLoadType
from dagster._core.definitions.repository_definition.repository_definition import RepositoryLoadData
from dagster._core.instance_for_test import instance_for_test
from dagster._utils.env import environ
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.testing import create_defs_folder_sandbox
from dagster_dbt import DbtProjectComponent
from dagster_dbt.dbt_project_manager import RemoteGitDbtProjectManager

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

    def _clone_from(repo_url: str, to_path: Path, depth: int = 1):
        # we expect to_path to be an empty directory
        assert to_path.exists()
        assert to_path.is_dir()
        assert not any(to_path.iterdir())
        # Instead of actually cloning, copy our prepared test project
        shutil.copytree(dbt_project_dir, to_path, dirs_exist_ok=True)
        return MagicMock()

    return _clone_from


def test_remote_dbt_project_dev_mode_calls_fetch(dbt_project_dir: Path) -> None:
    """Test that loading with DAGSTER_IS_DEV_CLI=1 calls fetch and loads assets."""
    repo_url = "https://github.com/fake/repo.git"

    with (
        instance_for_test(),
        create_defs_folder_sandbox() as sandbox,
        patch("dagster_dbt.dbt_project_manager.Repo.clone_from") as mock_clone,
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
            specs = defs.get_all_asset_specs()
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
        patch("dagster_dbt.dbt_project_manager.Repo.clone_from") as mock_clone,
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
            specs = defs.get_all_asset_specs()
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
            specs = defs.get_all_asset_specs()
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
        patch("dagster_dbt.dbt_project_manager.Repo.clone_from") as mock_clone,
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
            specs = defs.get_all_asset_specs()
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
        patch("dagster_dbt.dbt_project_manager.Repo.clone_from") as mock_clone,
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
            specs = defs.get_all_asset_specs()
            assert len(specs) > 0

            # fetch should have been called
            mock_clone.assert_called_once_with(repo_url_with_token, ANY, depth=1)
