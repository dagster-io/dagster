import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Optional

import pytest
from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster._core.storage.defs_state.defs_state_info import DefsStateInfo


def _version_map(state_info: Optional[DefsStateInfo]) -> Optional[dict[str, str]]:
    if state_info is None:
        return None
    return {k: v.version for k, v in state_info.info_mapping.items()}


class TestStateStorage:
    """You can extend this class to easily run these set of tests on any state storage. When extending,
    you simply need to override the `state_storage` fixture and return your implementation of
    `StateStorage`.
    """

    __test__ = False

    @pytest.fixture(name="storage")
    def state_storage(self) -> Iterator[DefsStateStorage]: ...

    def test_get_latest_state_version_for_defs(self, storage: DefsStateStorage) -> None:
        """Test get_latest_state_version_for_defs method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "test_state.json"
            path.write_text("foo")

            result = storage.get_latest_version("test_defs")
            assert result is None

            storage.upload_state_from_path("A", "v1.0", path)
            result = storage.get_latest_version("A")
            assert result == "v1.0"

            storage.upload_state_from_path("B", "v2.0", path)
            result = storage.get_latest_version("B")
            assert result == "v2.0"

            result = storage.get_latest_version("A")
            assert result == "v1.0"

            assert _version_map(storage.get_latest_defs_state_info()) == {
                "A": "v1.0",
                "B": "v2.0",
            }

    def test_load_state_file(self, storage: DefsStateStorage) -> None:
        """Test load_state_file method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_file_path = Path(temp_dir) / "state.json"
            load_file_path = Path(temp_dir) / "load_state.json"

            test_state = '{"key": "value", "number": 42}'
            store_file_path.write_text(test_state)
            storage.upload_state_from_path("A", "v1.0", store_file_path)

            storage.download_state_to_path("A", "v1.0", load_file_path)
            assert load_file_path.exists()
            assert load_file_path.read_text() == test_state

            test_state_v2 = '{"key": "new_value", "number": 100}'
            store_file_path.write_text(test_state_v2)
            storage.upload_state_from_path("A", "v2.0", store_file_path)

            storage.download_state_to_path("A", "v2.0", load_file_path)
            assert load_file_path.exists()
            assert load_file_path.read_text() == test_state_v2

            assert _version_map(storage.get_latest_defs_state_info()) == {"A": "v2.0"}

    def test_persist_state_from_file(self, storage: DefsStateStorage) -> None:
        """Test persist_state_from_file method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "state.json"
            test_state = '{"key": "value", "number": 42}'
            file_path.write_text(test_state)

            storage.upload_state_from_path("A", "v1.0", file_path)
            assert storage.get_latest_version("A") == "v1.0"

            test_state_v2 = '{"key": "new_value", "updated": true}'
            file_path.write_text(test_state_v2)

            storage.upload_state_from_path("A", "v2.0", file_path)
            assert storage.get_latest_version("A") == "v2.0"

    def test_state_store_integration(self, storage: DefsStateStorage) -> None:
        """Test integration of all three methods together."""
        with tempfile.TemporaryDirectory() as temp_dir:
            assert storage.get_latest_version("integration_test") is None

            state_file = Path(temp_dir) / "integration_state.json"
            original_state = '{"step": 1, "data": "initial"}'
            state_file.write_text(original_state)

            storage.upload_state_from_path("integration_test", "v1.0", state_file)

            assert storage.get_latest_version("integration_test") == "v1.0"

            loaded_file = Path(temp_dir) / "loaded_state.json"
            storage.download_state_to_path("integration_test", "v1.0", loaded_file)
            assert loaded_file.read_text() == original_state

            updated_state = '{"step": 2, "data": "updated"}'
            state_file.write_text(updated_state)
            storage.upload_state_from_path("integration_test", "v1.1", state_file)

            assert storage.get_latest_version("integration_test") == "v1.1"

            old_version_file = Path(temp_dir) / "old_version.json"
            storage.download_state_to_path("integration_test", "v1.0", old_version_file)
            assert old_version_file.read_text() == original_state

            new_version_file = Path(temp_dir) / "new_version.json"
            storage.download_state_to_path("integration_test", "v1.1", new_version_file)
            assert new_version_file.read_text() == updated_state
