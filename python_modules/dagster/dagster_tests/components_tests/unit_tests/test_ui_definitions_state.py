"""Tests for the per-component UI definitions storage primitives."""

import tempfile
from pathlib import Path

import pytest
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.defs_state.blob_storage_state_storage import UPathDefsStateStorage
from dagster.components.component.ui_definitions_state import (
    UIComponentEntry,
    get_ui_component_ids,
    get_ui_component_state_key,
    get_ui_definitions_prefix,
    read_ui_component_entry,
    write_ui_component_entry,
)
from dagster_shared import check


def _entry(name: str = "x") -> UIComponentEntry:
    return UIComponentEntry(component_type="dagster.SomeComponent", attributes=f"name: {name}\n")


@pytest.fixture(name="storage")
def state_storage():
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
            yield check.inst(instance.defs_state_storage, UPathDefsStateStorage)


class TestKeys:
    def test_prefix_is_location_scoped(self):
        assert get_ui_definitions_prefix("locA") != get_ui_definitions_prefix("locB")
        assert get_ui_definitions_prefix("locA").startswith("dagster-ui-definitions[locA]")

    def test_per_component_keys_are_distinct(self):
        a = get_ui_component_state_key("loc", "id1")
        b = get_ui_component_state_key("loc", "id2")
        assert a != b
        assert a.startswith(get_ui_definitions_prefix("loc"))


class TestReadWriteRoundtrip:
    def test_read_missing_component_returns_none(self, storage):
        assert read_ui_component_entry(storage, "loc", "missing") is None

    def test_write_then_read(self, storage):
        entry = _entry("alice")
        write_ui_component_entry(storage, "loc", "comp1", entry)
        assert read_ui_component_entry(storage, "loc", "comp1") == entry

    def test_overwrite_replaces_lww(self, storage):
        """Two writes to the same component_id: latest wins, no error."""
        write_ui_component_entry(storage, "loc", "comp1", _entry("first"))
        write_ui_component_entry(storage, "loc", "comp1", _entry("second"))
        result = read_ui_component_entry(storage, "loc", "comp1")
        assert result == _entry("second")

    def test_writes_to_distinct_ids_dont_contend(self, storage):
        """Per-component sharding: writes to different ids target different keys."""
        write_ui_component_entry(storage, "loc", "comp1", _entry("a"))
        write_ui_component_entry(storage, "loc", "comp2", _entry("b"))
        assert read_ui_component_entry(storage, "loc", "comp1") == _entry("a")
        assert read_ui_component_entry(storage, "loc", "comp2") == _entry("b")


class TestListing:
    def test_empty_when_no_components(self, storage):
        assert get_ui_component_ids(storage, "loc") == set()

    def test_lists_written_components(self, storage):
        write_ui_component_entry(storage, "loc", "comp1", _entry("a"))
        write_ui_component_entry(storage, "loc", "comp2", _entry("b"))
        assert get_ui_component_ids(storage, "loc") == {"comp1", "comp2"}

    def test_filters_by_location_prefix(self, storage):
        """Components in different locations are isolated by prefix."""
        write_ui_component_entry(storage, "locA", "shared_id", _entry("from_a"))
        write_ui_component_entry(storage, "locB", "shared_id", _entry("from_b"))
        write_ui_component_entry(storage, "locA", "only_in_a", _entry("solo"))

        assert get_ui_component_ids(storage, "locA") == {"only_in_a", "shared_id"}
        assert get_ui_component_ids(storage, "locB") == {"shared_id"}

    def test_does_not_pick_up_unrelated_state_keys(self, storage):
        """Non-UI state keys aren't returned, even though they live in the same
        global state info.
        """
        with tempfile.TemporaryDirectory() as tmp:
            unrelated_path = Path(tmp) / "u"
            unrelated_path.write_text("unrelated state", encoding="utf-8")
            storage.upload_state_from_path("UnrelatedKey", "v1", unrelated_path)

        write_ui_component_entry(storage, "loc", "comp1", _entry("a"))
        assert get_ui_component_ids(storage, "loc") == {"comp1"}
