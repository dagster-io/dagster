"""Tests for the per-component UI definitions storage primitives."""

import tempfile
from pathlib import Path

import pytest
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.defs_state.blob_storage_state_storage import UPathDefsStateStorage
from dagster.components.component.ui_definitions_state import (
    UIComponentEntry,
    delete_ui_component_entry,
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


class TestDeletion:
    def test_delete_then_read_returns_none(self, storage):
        write_ui_component_entry(storage, "loc", "comp1", _entry("a"))
        assert read_ui_component_entry(storage, "loc", "comp1") is not None

        delete_ui_component_entry(storage, "loc", "comp1")
        assert read_ui_component_entry(storage, "loc", "comp1") is None

    def test_delete_drops_id_from_listing(self, storage):
        """A deleted component's id must not show up in the listing — that's
        the path the framework uses to discover the active set.
        """
        write_ui_component_entry(storage, "loc", "comp1", _entry("a"))
        write_ui_component_entry(storage, "loc", "comp2", _entry("b"))
        assert get_ui_component_ids(storage, "loc") == {"comp1", "comp2"}

        delete_ui_component_entry(storage, "loc", "comp1")
        assert get_ui_component_ids(storage, "loc") == {"comp2"}

    def test_delete_is_idempotent(self, storage):
        """Caller doesn't need to first check whether the component exists."""
        delete_ui_component_entry(storage, "loc", "never-existed")  # no-op, no error
        write_ui_component_entry(storage, "loc", "comp1", _entry("a"))
        delete_ui_component_entry(storage, "loc", "comp1")
        delete_ui_component_entry(storage, "loc", "comp1")  # second delete also a no-op

    def test_delete_does_not_affect_other_locations(self, storage):
        """A delete in one location is scoped to that location — same component
        id in a sibling location stays put.
        """
        write_ui_component_entry(storage, "locA", "shared_id", _entry("from_a"))
        write_ui_component_entry(storage, "locB", "shared_id", _entry("from_b"))

        delete_ui_component_entry(storage, "locA", "shared_id")

        assert get_ui_component_ids(storage, "locA") == set()
        assert get_ui_component_ids(storage, "locB") == {"shared_id"}
        assert read_ui_component_entry(storage, "locB", "shared_id") == _entry("from_b")

    def test_delete_then_re_add_with_same_id_works(self, storage):
        """The component_id namespace is reusable after deletion — useful if
        a caller wants to recreate a deleted component at the same logical id.
        """
        write_ui_component_entry(storage, "loc", "comp1", _entry("first"))
        delete_ui_component_entry(storage, "loc", "comp1")

        write_ui_component_entry(storage, "loc", "comp1", _entry("second"))
        result = read_ui_component_entry(storage, "loc", "comp1")
        assert result == _entry("second")
