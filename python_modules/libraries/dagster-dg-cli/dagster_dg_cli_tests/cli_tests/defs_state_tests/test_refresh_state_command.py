import shutil
from pathlib import Path

import dagster as dg
import yaml
from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster_dg_core.utils import activate_venv
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
        state_storage = DefsStateStorage.get_current()
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
        state_storage = DefsStateStorage.get_current()
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
