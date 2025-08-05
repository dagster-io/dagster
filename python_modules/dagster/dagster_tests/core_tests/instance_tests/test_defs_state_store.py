import tempfile
from pathlib import Path

import dagster as dg


def test_get_latest_state_version_for_defs():
    """Test get_latest_state_version_for_defs method."""
    with dg.instance_for_test() as instance, tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "test_state.json"
        path.write_text("foo")

        storage = instance.state_storage
        result = storage.get_latest_version("test_defs")
        assert result is None

        storage.store_state("A", "v1.0", path)
        result = storage.get_latest_version("A")
        assert result == "v1.0"

        storage.store_state("B", "v2.0", path)
        result = storage.get_latest_version("B")
        assert result == "v2.0"

        result = storage.get_latest_version("A")
        assert result == "v1.0"


def test_load_state_file():
    """Test load_state_file method."""
    with dg.instance_for_test() as instance, tempfile.TemporaryDirectory() as temp_dir:
        storage = instance.state_storage
        store_file_path = Path(temp_dir) / "state.json"
        load_file_path = Path(temp_dir) / "load_state.json"

        test_state = '{"key": "value", "number": 42}'
        store_file_path.write_text(test_state)
        storage.store_state("A", "v1.0", store_file_path)

        storage.load_state_to_path("A", "v1.0", load_file_path)
        assert load_file_path.exists()
        assert load_file_path.read_text() == test_state

        test_state_v2 = '{"key": "new_value", "number": 100}'
        store_file_path.write_text(test_state_v2)
        storage.store_state("A", "v2.0", store_file_path)

        storage.load_state_to_path("A", "v2.0", load_file_path)
        assert load_file_path.exists()
        assert load_file_path.read_text() == test_state_v2


def test_persist_state_from_file():
    """Test persist_state_from_file method."""
    with dg.instance_for_test() as instance, tempfile.TemporaryDirectory() as temp_dir:
        storage = instance.state_storage
        file_path = Path(temp_dir) / "state.json"
        test_state = '{"key": "value", "number": 42}'
        file_path.write_text(test_state)

        storage.store_state("A", "v1.0", file_path)
        assert storage.get_latest_version("A") == "v1.0"

        test_state_v2 = '{"key": "new_value", "updated": true}'
        file_path.write_text(test_state_v2)

        storage.store_state("A", "v2.0", file_path)
        assert storage.get_latest_version("A") == "v2.0"


def test_state_store_integration():
    """Test integration of all three methods together."""
    with dg.instance_for_test() as instance, tempfile.TemporaryDirectory() as temp_dir:
        assert instance.state_storage.get_latest_version("integration_test") is None

        state_file = Path(temp_dir) / "integration_state.json"
        original_state = '{"step": 1, "data": "initial"}'
        state_file.write_text(original_state)

        storage = instance.state_storage
        storage.store_state("integration_test", "v1.0", state_file)

        assert storage.get_latest_version("integration_test") == "v1.0"

        loaded_file = Path(temp_dir) / "loaded_state.json"
        storage.load_state_to_path("integration_test", "v1.0", loaded_file)
        assert loaded_file.read_text() == original_state

        updated_state = '{"step": 2, "data": "updated"}'
        state_file.write_text(updated_state)
        storage.store_state("integration_test", "v1.1", state_file)

        assert storage.get_latest_version("integration_test") == "v1.1"

        old_version_file = Path(temp_dir) / "old_version.json"
        storage.load_state_to_path("integration_test", "v1.0", old_version_file)
        assert old_version_file.read_text() == original_state

        new_version_file = Path(temp_dir) / "new_version.json"
        storage.load_state_to_path("integration_test", "v1.1", new_version_file)
        assert new_version_file.read_text() == updated_state
