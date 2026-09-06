import tempfile
from pathlib import Path

import pytest
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster._core.storage.defs_state.blob_storage_state_storage import UPathDefsStateStorage
from dagster_shared import check
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo
from upath import UPath

from dagster_tests.storage_tests.utils.defs_state_storage import TestDefsStateStorage


def test_artifact_key_layout_is_frozen():
    """The remote DefsStateStorage key layout is a cross-version contract: the agent and the
    ``dg`` CLI (producers) and host cloud (consumer) all derive blob keys from the shared
    base-class ``_get_artifact_key``. Changing the prefix or the sanitization orphans every
    previously-uploaded state blob, so this layout is effectively frozen -- if this test fails
    because you changed the layout, you are also signing up to migrate already-stored state.
    """

    class _StubDefsStateStorage(DefsStateStorage):
        def get_latest_defs_state_info(self) -> DefsStateInfo | None:
            raise NotImplementedError

        def download_state_to_path(self, key: str, version: str, path: Path) -> None:
            raise NotImplementedError

        def upload_state_from_path(self, key: str, version: str, path: Path) -> None:
            raise NotImplementedError

        def set_latest_version(self, key: str, version: str | None) -> None:
            raise NotImplementedError

    storage = _StubDefsStateStorage()
    assert storage._get_artifact_key("MyComponent", "v1") == "__state__/MyComponent/v1"  # noqa: SLF001
    # The key component is sanitized: anything outside [A-Za-z0-9._-] collapses to "__".
    assert storage._get_artifact_key("a/b c", "v1") == "__state__/a__b__c/v1"  # noqa: SLF001


class TestDefaultDefsStateStorage(TestDefsStateStorage):
    """Tests the default state storage implementation."""

    __test__ = True

    @pytest.fixture(name="storage", scope="function")
    def state_storage(self):
        with instance_for_test() as instance:
            yield check.not_none(instance.defs_state_storage)


class TestExplicitUPathDefsStateStorage(TestDefsStateStorage):
    """Tests the blob storage state storage implementation."""

    __test__ = True

    @pytest.fixture(name="storage", scope="function")
    def state_storage(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with instance_for_test(
                overrides={
                    "defs_state_storage": {
                        "module": "dagster._core.storage.defs_state.blob_storage_state_storage",
                        "class": "UPathDefsStateStorage",
                        "config": {"base_path": temp_dir},
                    }
                }
            ) as instance:
                state_storage = check.inst(instance.defs_state_storage, UPathDefsStateStorage)

                assert state_storage.base_path == UPath(temp_dir)
                yield state_storage
