import tempfile
from pathlib import Path

import dagster as dg


def test_get_latest_state_version_for_defs():
    """Test get_latest_state_version_for_defs method."""
    with dg.instance_for_test() as instance:
        result = instance.get_latest_state_version_for_defs("test_defs")
        assert result is None

        instance.run_storage.set_cursor_values({"version_test_defs": "v1.0"})
        result = instance.get_latest_state_version_for_defs("test_defs")
        assert result == "v1.0"

        instance.run_storage.set_cursor_values({"version_other_defs": "v2.0"})
        result = instance.get_latest_state_version_for_defs("other_defs")
        assert result == "v2.0"

        result = instance.get_latest_state_version_for_defs("test_defs")
        assert result == "v1.0"


def test_load_state_file():
    """Test load_state_file method."""
    with dg.instance_for_test() as instance:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "state.json"

            result = instance.load_state_file("test_defs", "v1.0", file_path)
            assert result is False
            assert not file_path.exists()

            result = instance.load_state_file("test_defs", "", file_path)
            assert result is False
            assert not file_path.exists()

            test_state = '{"key": "value", "number": 42}'
            instance.run_storage.set_cursor_values({"test_defs_v1.0": test_state})

            result = instance.load_state_file("test_defs", "v1.0", file_path)
            assert result is True
            assert file_path.exists()
            assert file_path.read_text() == test_state

            test_state_v2 = '{"key": "new_value", "number": 100}'
            instance.run_storage.set_cursor_values({"test_defs_v2.0": test_state_v2})

            file_path_v2 = Path(temp_dir) / "state_v2.json"
            result = instance.load_state_file("test_defs", "v2.0", file_path_v2)
            assert result is True
            assert file_path_v2.exists()
            assert file_path_v2.read_text() == test_state_v2


def test_persist_state_from_file():
    """Test persist_state_from_file method."""
    with dg.instance_for_test() as instance:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "state.json"
            test_state = '{"key": "value", "number": 42}'
            file_path.write_text(test_state)

            instance.persist_state_from_file("test_defs", "v1.0", file_path)

            state_key = "test_defs_v1.0"
            version_key = "version_test_defs"

            cursor_values = instance.run_storage.get_cursor_values({state_key, version_key})
            assert cursor_values[state_key] == test_state
            assert cursor_values[version_key] == "v1.0"

            test_state_v2 = '{"key": "new_value", "updated": true}'
            file_path.write_text(test_state_v2)

            instance.persist_state_from_file("test_defs", "v2.0", file_path)

            all_keys = {"test_defs_v1.0", "test_defs_v2.0", "version_test_defs"}
            cursor_values = instance.run_storage.get_cursor_values(all_keys)

            assert cursor_values["test_defs_v1.0"] == test_state
            assert cursor_values["test_defs_v2.0"] == test_state_v2
            assert cursor_values["version_test_defs"] == "v2.0"


def test_state_store_integration():
    """Test integration of all three methods together."""
    with dg.instance_for_test() as instance:
        with tempfile.TemporaryDirectory() as temp_dir:
            assert instance.get_latest_state_version_for_defs("integration_test") is None

            state_file = Path(temp_dir) / "integration_state.json"
            original_state = '{"step": 1, "data": "initial"}'
            state_file.write_text(original_state)

            instance.persist_state_from_file("integration_test", "v1.0", state_file)

            assert instance.get_latest_state_version_for_defs("integration_test") == "v1.0"

            loaded_file = Path(temp_dir) / "loaded_state.json"
            success = instance.load_state_file("integration_test", "v1.0", loaded_file)
            assert success is True
            assert loaded_file.read_text() == original_state

            updated_state = '{"step": 2, "data": "updated"}'
            state_file.write_text(updated_state)
            instance.persist_state_from_file("integration_test", "v1.1", state_file)

            assert instance.get_latest_state_version_for_defs("integration_test") == "v1.1"

            old_version_file = Path(temp_dir) / "old_version.json"
            success = instance.load_state_file("integration_test", "v1.0", old_version_file)
            assert success is True
            assert old_version_file.read_text() == original_state

            new_version_file = Path(temp_dir) / "new_version.json"
            success = instance.load_state_file("integration_test", "v1.1", new_version_file)
            assert success is True
            assert new_version_file.read_text() == updated_state
