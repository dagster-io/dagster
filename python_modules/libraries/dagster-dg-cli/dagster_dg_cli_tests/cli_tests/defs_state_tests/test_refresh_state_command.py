import shutil
from pathlib import Path

import dagster as dg
import yaml
from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster_dg_core.utils import activate_venv
from dagster_shared.utils import environ
from dagster_test.dg_utils.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_project_foo_bar,
)


def test_refresh_state_command():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, use_editable_dagster=True, uv_sync=True
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
        dg.instance_for_test(),
    ):
        state_storage = DefsStateStorage.get()
        assert state_storage is not None
        # no components, nothing to refresh
        result = runner.invoke("utils", "refresh-defs-state")
        assert_runner_result(result)
        latest_state_info = state_storage.get_latest_defs_state_info()
        assert latest_state_info is None

        # write a local component defs.yaml
        component_dir = project_dir / "src/foo_bar/defs/the_component"
        component_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(__file__).parent / "sample_state_backed_component.py",
            component_dir / "local.py",
        )
        with (component_dir / "defs.yaml").open("w") as f:
            yaml.dump(
                {"type": ".local.SampleStateBackedComponent"},
                f,
            )

        # now we have a state-backed component, command should succeed
        # and we should have a new state version
        result = runner.invoke("utils", "refresh-defs-state")
        assert_runner_result(result)

        latest_state_info = state_storage.get_latest_defs_state_info()
        assert latest_state_info is not None
        assert latest_state_info.info_mapping.keys() == {"SampleStateBackedComponent"}

        # write another local component defs.yaml, this one will fail to write state
        component_dir = project_dir / "src/foo_bar/defs/the_component_fails"
        component_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(__file__).parent / "sample_state_backed_component.py",
            component_dir / "local.py",
        )
        with (component_dir / "defs.yaml").open("w") as f:
            yaml.dump(
                {
                    "type": ".local.SampleStateBackedComponent",
                    "attributes": {
                        "fail_write": True,
                        "defs_state_key_id": "second",
                    },
                },
                f,
            )

        # command should fail, but state should be updated for the non-failing component
        result = runner.invoke("utils", "refresh-defs-state")
        assert result.exit_code == 1

        new_latest_state_info = state_storage.get_latest_defs_state_info()
        assert new_latest_state_info is not None
        assert new_latest_state_info.info_mapping.keys() == {"SampleStateBackedComponent"}
        assert (
            new_latest_state_info.info_mapping["SampleStateBackedComponent"]
            != latest_state_info.info_mapping["SampleStateBackedComponent"]
        )


def test_refresh_state_command_with_defs_key_filter():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, use_editable_dagster=True, uv_sync=True
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
        dg.instance_for_test(),
    ):
        state_storage = DefsStateStorage.get()
        assert state_storage is not None
        # Create two components
        component1_dir = project_dir / "src/foo_bar/defs/component1"
        component1_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(__file__).parent / "sample_state_backed_component.py",
            component1_dir / "local.py",
        )
        with (component1_dir / "defs.yaml").open("w") as f:
            yaml.dump(
                {
                    "type": ".local.SampleStateBackedComponent",
                    "attributes": {
                        "defs_state_key_id": "first",
                    },
                },
                f,
            )

        component2_dir = project_dir / "src/foo_bar/defs/component2"
        component2_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(__file__).parent / "sample_state_backed_component.py",
            component2_dir / "local.py",
        )
        with (component2_dir / "defs.yaml").open("w") as f:
            yaml.dump(
                {
                    "type": ".local.SampleStateBackedComponent",
                    "attributes": {
                        "defs_state_key_id": "second",
                    },
                },
                f,
            )

        # Refresh only component1
        result = runner.invoke(
            "utils",
            "refresh-defs-state",
            "--defs-state-key",
            "SampleStateBackedComponent[first]",
        )
        assert_runner_result(result)

        # Verify only component1 was refreshed
        latest_state_info = state_storage.get_latest_defs_state_info()
        assert latest_state_info is not None
        assert latest_state_info.info_mapping.keys() == {"SampleStateBackedComponent[first]"}

        # Refresh both components using multiple --defs-key flags
        result = runner.invoke(
            "utils",
            "refresh-defs-state",
            "--defs-state-key",
            "SampleStateBackedComponent[first]",
            "--defs-state-key",
            "SampleStateBackedComponent[second]",
        )
        assert_runner_result(result)

        # Verify both components were refreshed
        latest_state_info = state_storage.get_latest_defs_state_info()
        assert latest_state_info is not None
        assert latest_state_info.info_mapping.keys() == {
            "SampleStateBackedComponent[first]",
            "SampleStateBackedComponent[second]",
        }

        # Test with non-existent defs-key
        result = runner.invoke("utils", "refresh-defs-state", "--defs-state-key", "nonexistent")
        assert result.exit_code == 1
        assert "The following defs state keys were not found:" in result.output
        assert "nonexistent" in result.output
        assert "Available defs state keys:" in result.output


def test_refresh_state_command_dagster_home_not_set():
    """Test that refresh-defs-state command errors when DAGSTER_HOME is not set."""
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, use_editable_dagster=True, uv_sync=True
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
        environ({"DAGSTER_HOME": None}),  # pyright: ignore[reportArgumentType] # Temporarily unset DAGSTER_HOME
    ):
        # no components to refresh, so command should succeed
        result = runner.invoke("utils", "refresh-defs-state")
        assert_runner_result(result)

        # check that the warning is emitted
        assert (
            "DAGSTER_HOME is not set, which means defs state for VERSIONED_STATE_STORAGE components "
            in result.output
        )
        assert "export DAGSTER_HOME" in result.output


def test_refresh_state_command_with_duplicate_keys():
    """Test that refresh-defs-state deduplicates components with the same defs state key."""
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, use_editable_dagster=True, uv_sync=True
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
        dg.instance_for_test(),
    ):
        state_storage = DefsStateStorage.get()
        assert state_storage is not None

        # Create two components with the same defs state key
        component1_dir = project_dir / "src/foo_bar/defs/component1"
        component1_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(__file__).parent / "sample_state_backed_component.py",
            component1_dir / "local.py",
        )
        with (component1_dir / "defs.yaml").open("w") as f:
            yaml.dump(
                {
                    "type": ".local.SampleStateBackedComponent",
                    "attributes": {
                        "defs_state_key_id": "shared",
                    },
                },
                f,
            )

        component2_dir = project_dir / "src/foo_bar/defs/component2"
        component2_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(__file__).parent / "sample_state_backed_component.py",
            component2_dir / "local.py",
        )
        with (component2_dir / "defs.yaml").open("w") as f:
            yaml.dump(
                {
                    "type": ".local.SampleStateBackedComponent",
                    "attributes": {
                        "defs_state_key_id": "shared",
                    },
                },
                f,
            )

        # Refresh should succeed and only refresh once despite two components sharing the same key
        result = runner.invoke("utils", "refresh-defs-state")
        assert_runner_result(result)

        # Verify that only one entry was created in the state storage
        latest_state_info = state_storage.get_latest_defs_state_info()
        assert latest_state_info is not None
        assert latest_state_info.info_mapping.keys() == {"SampleStateBackedComponent[shared]"}

        # The output should only show one refresh status line (not two)
        # Count how many times the key appears in the output
        key_count = result.output.count("SampleStateBackedComponent[shared]")
        # It should appear once in the status display, not twice
        assert key_count == 1, f"Expected key to appear once, but appeared {key_count} times"


def test_refresh_state_command_with_management_type_filter():
    """Test that refresh-defs-state filters by management type correctly."""
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, use_editable_dagster=True, uv_sync=True
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
        dg.instance_for_test(),
    ):
        state_storage = DefsStateStorage.get()
        assert state_storage is not None

        # Create a component with VERSIONED_STATE_STORAGE
        versioned_component_dir = project_dir / "src/foo_bar/defs/versioned_component"
        versioned_component_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(__file__).parent / "sample_state_backed_component.py",
            versioned_component_dir / "local.py",
        )
        with (versioned_component_dir / "defs.yaml").open("w") as f:
            yaml.dump(
                {
                    "type": ".local.SampleStateBackedComponent",
                    "attributes": {
                        "defs_state_key_id": "versioned",
                        "defs_state": {"management_type": "VERSIONED_STATE_STORAGE"},
                    },
                },
                f,
            )

        # Create a component with LOCAL_FILESYSTEM
        local_component_dir = project_dir / "src/foo_bar/defs/local_component"
        local_component_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(__file__).parent / "sample_state_backed_component.py",
            local_component_dir / "local.py",
        )
        with (local_component_dir / "defs.yaml").open("w") as f:
            yaml.dump(
                {
                    "type": ".local.SampleStateBackedComponent",
                    "attributes": {
                        "defs_state_key_id": "local",
                        "defs_state": {"management_type": "LOCAL_FILESYSTEM"},
                    },
                },
                f,
            )

        # Test 1: Filter by VERSIONED_STATE_STORAGE only
        result = runner.invoke(
            "utils", "refresh-defs-state", "--management-type", "VERSIONED_STATE_STORAGE"
        )
        assert_runner_result(result)

        # Should only refresh the versioned component (check output not storage as storage is cumulative)
        assert "SampleStateBackedComponent[versioned]" in result.output
        # Should not show the local component
        assert "SampleStateBackedComponent[local]" not in result.output

        # Verify state storage has the versioned component
        latest_state_info = state_storage.get_latest_defs_state_info()
        assert latest_state_info is not None
        assert "SampleStateBackedComponent[versioned]" in latest_state_info.info_mapping

        # Test 2: Filter by LOCAL_FILESYSTEM only
        result = runner.invoke(
            "utils", "refresh-defs-state", "--management-type", "LOCAL_FILESYSTEM"
        )
        assert_runner_result(result)

        # Should only refresh the local component (check output not storage as storage is cumulative)
        assert "SampleStateBackedComponent[local]" in result.output
        # Should not show the versioned component
        assert "SampleStateBackedComponent[versioned]" not in result.output

        # Verify state storage has the local component (state is cumulative, so it has both now)
        latest_state_info = state_storage.get_latest_defs_state_info()
        assert latest_state_info is not None
        assert "SampleStateBackedComponent[local]" in latest_state_info.info_mapping

        # Test 3: Refresh both by specifying both management types
        result = runner.invoke(
            "utils",
            "refresh-defs-state",
            "--management-type",
            "VERSIONED_STATE_STORAGE",
            "--management-type",
            "LOCAL_FILESYSTEM",
        )
        assert_runner_result(result)

        # Should refresh both components (check output shows both)
        assert "SampleStateBackedComponent[versioned]" in result.output
        assert "SampleStateBackedComponent[local]" in result.output

        # Verify state storage has both components
        latest_state_info = state_storage.get_latest_defs_state_info()
        assert latest_state_info is not None
        assert "SampleStateBackedComponent[versioned]" in latest_state_info.info_mapping
        assert "SampleStateBackedComponent[local]" in latest_state_info.info_mapping


def test_refresh_state_command_excludes_legacy_code_server_snapshots_by_default():
    """Test that LEGACY_CODE_SERVER_SNAPSHOTS components are excluded by default."""
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, use_editable_dagster=True, uv_sync=True
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
        dg.instance_for_test(),
    ):
        state_storage = DefsStateStorage.get()
        assert state_storage is not None

        # Create a component with VERSIONED_STATE_STORAGE
        versioned_component_dir = project_dir / "src/foo_bar/defs/versioned_component"
        versioned_component_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(__file__).parent / "sample_state_backed_component.py",
            versioned_component_dir / "local.py",
        )
        with (versioned_component_dir / "defs.yaml").open("w") as f:
            yaml.dump(
                {
                    "type": ".local.SampleStateBackedComponent",
                    "attributes": {
                        "defs_state_key_id": "versioned",
                        "defs_state": {"management_type": "VERSIONED_STATE_STORAGE"},
                    },
                },
                f,
            )

        # Create a component with LEGACY_CODE_SERVER_SNAPSHOTS
        legacy_component_dir = project_dir / "src/foo_bar/defs/legacy_component"
        legacy_component_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(__file__).parent / "sample_state_backed_component.py",
            legacy_component_dir / "local.py",
        )
        with (legacy_component_dir / "defs.yaml").open("w") as f:
            yaml.dump(
                {
                    "type": ".local.SampleStateBackedComponent",
                    "attributes": {
                        "defs_state_key_id": "legacy",
                        "defs_state": {"management_type": "LEGACY_CODE_SERVER_SNAPSHOTS"},
                    },
                },
                f,
            )

        # Refresh without specifying management type
        result = runner.invoke("utils", "refresh-defs-state")
        assert_runner_result(result)

        # Should only refresh the versioned component, not the legacy one
        assert "SampleStateBackedComponent[versioned]" in result.output
        assert "SampleStateBackedComponent[legacy]" not in result.output

        # Verify state storage has only the versioned component
        latest_state_info = state_storage.get_latest_defs_state_info()
        assert latest_state_info is not None
        assert latest_state_info.info_mapping.keys() == {"SampleStateBackedComponent[versioned]"}
