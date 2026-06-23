import tempfile
from pathlib import Path
from typing import Any

import pytest
from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo


def _version_map(state_info: DefsStateInfo | None) -> dict[str, str | None] | None:
    if state_info is None:
        return None
    return {k: v.version if v else None for k, v in state_info.info_mapping.items()}


class TestDefsStateStorage:
    """You can extend this class to easily run these set of tests on any state storage. When extending,
    you simply need to override the `state_storage` fixture and return your implementation of
    `StateStorage`.
    """

    __test__ = False

    @pytest.fixture(name="storage")
    def state_storage(self) -> Any: ...

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

    def test_set_latest_version_none_clears_pointer_and_listing(
        self, storage: DefsStateStorage
    ) -> None:
        """Passing ``version=None`` to ``set_latest_version`` drops the key
        from the latest-version pointer AND from prefix listings — the
        listing primitive is the discovery path for sharded features, so a
        cleared key must not reappear there.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.json"
            state_file.write_text("payload", encoding="utf-8")
            storage.upload_state_from_path("Sharded[loc]/A", "v1", state_file)
            storage.upload_state_from_path("Sharded[loc]/B", "v1", state_file)
            assert sorted(storage.list_state_keys_with_prefix("Sharded[loc]/")) == [
                "Sharded[loc]/A",
                "Sharded[loc]/B",
            ]

            storage.set_latest_version("Sharded[loc]/A", None)

            assert storage.get_latest_version("Sharded[loc]/A") is None
            # The cleared key disappears from listings; the surviving sibling stays.
            assert storage.list_state_keys_with_prefix("Sharded[loc]/") == ["Sharded[loc]/B"]

    def test_set_latest_version_none_is_idempotent(self, storage: DefsStateStorage) -> None:
        """Clearing a key that doesn't exist is a no-op — used by callers
        that don't need to first check whether the key is present.
        """
        # No prior write — should not raise.
        storage.set_latest_version("NeverExisted", None)
        assert storage.get_latest_version("NeverExisted") is None

        # Clear twice — the second call should also succeed.
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.json"
            state_file.write_text("payload", encoding="utf-8")
            storage.upload_state_from_path("Once", "v1", state_file)

        storage.set_latest_version("Once", None)
        storage.set_latest_version("Once", None)  # second clear is a no-op
        assert storage.get_latest_version("Once") is None

    def test_set_latest_version_none_then_re_upload_works(self, storage: DefsStateStorage) -> None:
        """After clearing, re-uploading at the same key should succeed and
        present the new version as the latest.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.json"
            state_file.write_text("first", encoding="utf-8")
            storage.upload_state_from_path("Cycled", "v1", state_file)

            storage.set_latest_version("Cycled", None)
            assert storage.get_latest_version("Cycled") is None

            state_file.write_text("second", encoding="utf-8")
            storage.upload_state_from_path("Cycled", "v2", state_file)
            assert storage.get_latest_version("Cycled") == "v2"

            loaded = Path(temp_dir) / "loaded.json"
            storage.download_state_to_path("Cycled", "v2", loaded)
            assert loaded.read_text(encoding="utf-8") == "second"

    def test_set_latest_version_none_does_not_affect_other_keys(
        self, storage: DefsStateStorage
    ) -> None:
        """The cursor record holds many keys' pointers; clearing one must
        not corrupt the others.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.json"
            state_file.write_text("payload", encoding="utf-8")
            storage.upload_state_from_path("KeepA", "v1", state_file)
            storage.upload_state_from_path("ClearMe", "v1", state_file)
            storage.upload_state_from_path("KeepB", "v1", state_file)

            storage.set_latest_version("ClearMe", None)

            assert storage.get_latest_version("KeepA") == "v1"
            assert storage.get_latest_version("KeepB") == "v1"
            assert storage.get_latest_version("ClearMe") is None

    @pytest.mark.parametrize(
        "key",
        [
            "integration_test",
            # ensure we can handle special characters
            "integration_test[xyz://foo.bar.baz@&*//xy]",
        ],
    )
    def test_state_store_integration(self, storage: DefsStateStorage, key: str) -> None:
        """Test integration of all three methods together."""
        with tempfile.TemporaryDirectory() as temp_dir:
            assert storage.get_latest_version(key) is None

            state_file = Path(temp_dir) / "integration_state.json"
            original_state = '{"step": 1, "data": "initial"}'
            state_file.write_text(original_state)

            storage.upload_state_from_path(key, "v1.0", state_file)

            assert storage.get_latest_version(key) == "v1.0"

            loaded_file = Path(temp_dir) / "loaded_state.json"
            storage.download_state_to_path(key, "v1.0", loaded_file)
            assert loaded_file.read_text() == original_state

            updated_state = '{"step": 2, "data": "updated"}'
            state_file.write_text(updated_state)
            storage.upload_state_from_path(key, "v1.1", state_file)

            assert storage.get_latest_version(key) == "v1.1"

            old_version_file = Path(temp_dir) / "old_version.json"
            storage.download_state_to_path(key, "v1.0", old_version_file)
            assert old_version_file.read_text() == original_state

            new_version_file = Path(temp_dir) / "new_version.json"
            storage.download_state_to_path(key, "v1.1", new_version_file)
            assert new_version_file.read_text() == updated_state
