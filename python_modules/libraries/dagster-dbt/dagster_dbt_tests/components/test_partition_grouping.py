"""Regression tests for _partitions_def_key and mixed-partition grouping.

These tests verify that:
  - _partitions_def_key generates stable, correct fingerprints for all partition
    definition types (time-window, static, dynamic, multi, None).
  - Semantically equivalent defs (e.g. timezone=None vs timezone="UTC") produce
    the same key.
  - build_defs_from_state correctly splits assets into multiple @multi_asset ops
    when their partition definitions are incompatible.
"""


import dagster as dg
from dagster import (
    AssetKey,
    AssetSpec,
    DailyPartitionsDefinition,
    DynamicPartitionsDefinition,
    HourlyPartitionsDefinition,
    MonthlyPartitionsDefinition,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
    WeeklyPartitionsDefinition,
)
from dagster_dbt.components.dbt_project.component import _partitions_def_key, _partitions_group_key

# ============================================================================
# Unit tests: _partitions_def_key
# ============================================================================


class TestPartitionsDefKeyNone:
    def test_none_returns_none_tuple(self):
        assert _partitions_def_key(None) == ("none",)


class TestPartitionsDefKeyTimeWindow:
    """TimeWindow-family defs: Daily, Hourly, Weekly, Monthly."""

    def test_daily_includes_structural_attrs(self):
        d = DailyPartitionsDefinition(start_date="2024-01-01")
        key = _partitions_def_key(d)
        assert key[0] == "DailyPartitionsDefinition"
        assert any("cron_schedule=" in p for p in key)
        assert any("timezone=" in p for p in key)

    def test_equivalent_daily_defs_match(self):
        d1 = DailyPartitionsDefinition(start_date="2024-01-01")
        d2 = DailyPartitionsDefinition(start_date="2024-01-01")
        assert _partitions_def_key(d1) == _partitions_def_key(d2)

    def test_different_start_dates_differ(self):
        d1 = DailyPartitionsDefinition(start_date="2024-01-01")
        d2 = DailyPartitionsDefinition(start_date="2025-01-01")
        assert _partitions_def_key(d1) != _partitions_def_key(d2)

    def test_timezone_none_equals_utc(self):
        """timezone=None and timezone='UTC' should produce the same key."""
        d1 = DailyPartitionsDefinition(start_date="2024-01-01")
        d2 = DailyPartitionsDefinition(start_date="2024-01-01", timezone="UTC")
        assert _partitions_def_key(d1) == _partitions_def_key(d2)

    def test_different_timezones_differ(self):
        d1 = DailyPartitionsDefinition(start_date="2024-01-01", timezone="UTC")
        d2 = DailyPartitionsDefinition(start_date="2024-01-01", timezone="US/Eastern")
        assert _partitions_def_key(d1) != _partitions_def_key(d2)

    def test_hourly_detected_as_time_window(self):
        h = HourlyPartitionsDefinition(start_date="2024-01-01-00:00")
        key = _partitions_def_key(h)
        assert key[0] == "HourlyPartitionsDefinition"
        assert any("cron_schedule=" in p for p in key)

    def test_weekly_detected_as_time_window(self):
        w = WeeklyPartitionsDefinition(start_date="2024-01-01")
        key = _partitions_def_key(w)
        assert key[0] == "WeeklyPartitionsDefinition"
        assert any("cron_schedule=" in p for p in key)

    def test_monthly_detected_as_time_window(self):
        m = MonthlyPartitionsDefinition(start_date="2024-01-01")
        key = _partitions_def_key(m)
        assert key[0] == "MonthlyPartitionsDefinition"
        assert any("cron_schedule=" in p for p in key)

    def test_daily_vs_hourly_differ(self):
        d = DailyPartitionsDefinition(start_date="2024-01-01")
        h = HourlyPartitionsDefinition(start_date="2024-01-01-00:00")
        assert _partitions_def_key(d) != _partitions_def_key(h)


class TestPartitionsDefKeyStatic:
    """StaticPartitionsDefinition fingerprinting."""

    def test_static_includes_hash_and_count(self):
        s = StaticPartitionsDefinition(["A", "B", "C"])
        key = _partitions_def_key(s)
        assert key[0] == "StaticPartitionsDefinition"
        assert any("keys_n=3" in p for p in key)
        assert any("keys_hash=" in p for p in key)

    def test_static_no_timezone(self):
        """Static defs should NOT get a timezone entry."""
        s = StaticPartitionsDefinition(["X"])
        key = _partitions_def_key(s)
        assert not any("timezone" in p for p in key)

    def test_same_keys_same_hash(self):
        s1 = StaticPartitionsDefinition(["A", "B"])
        s2 = StaticPartitionsDefinition(["A", "B"])
        assert _partitions_def_key(s1) == _partitions_def_key(s2)

    def test_different_keys_different_hash(self):
        s1 = StaticPartitionsDefinition(["A", "B"])
        s2 = StaticPartitionsDefinition(["X", "Y"])
        assert _partitions_def_key(s1) != _partitions_def_key(s2)

    def test_order_independent(self):
        """Keys are sorted before hashing, so order shouldn't matter."""
        s1 = StaticPartitionsDefinition(["B", "A"])
        s2 = StaticPartitionsDefinition(["A", "B"])
        assert _partitions_def_key(s1) == _partitions_def_key(s2)


class TestPartitionsDefKeyDynamic:
    """DynamicPartitionsDefinition fingerprinting."""

    def test_dynamic_includes_name(self):
        d = DynamicPartitionsDefinition(name="my_dyn")
        key = _partitions_def_key(d)
        assert key[0] == "DynamicPartitionsDefinition"
        assert "name=my_dyn" in key

    def test_dynamic_no_timezone(self):
        d = DynamicPartitionsDefinition(name="test")
        key = _partitions_def_key(d)
        assert not any("timezone" in p for p in key)

    def test_different_names_differ(self):
        d1 = DynamicPartitionsDefinition(name="alpha")
        d2 = DynamicPartitionsDefinition(name="beta")
        assert _partitions_def_key(d1) != _partitions_def_key(d2)


class TestPartitionsDefKeyMulti:
    """MultiPartitionsDefinition fingerprinting."""

    def test_multi_includes_dimensions(self):
        daily = DailyPartitionsDefinition(start_date="2024-01-01")
        static = StaticPartitionsDefinition(["AAPL", "GOOG"])
        mp = MultiPartitionsDefinition({"date": daily, "symbol": static})

        key = _partitions_def_key(mp)
        assert key[0] == "MultiPartitionsDefinition"
        # Should have dim entries for both dimensions
        dim_parts = [p for p in key if p.startswith("dim:")]
        assert len(dim_parts) == 2
        dim_names = {p.split(":")[1].split("=")[0] for p in dim_parts}
        assert dim_names == {"date", "symbol"}

    def test_multi_deterministic_ordering(self):
        """Dimension ordering in the key should be alphabetical, not insertion order."""
        daily = DailyPartitionsDefinition(start_date="2024-01-01")
        static = StaticPartitionsDefinition(["X"])
        mp1 = MultiPartitionsDefinition({"zzz": daily, "aaa": static})
        mp2 = MultiPartitionsDefinition({"aaa": static, "zzz": daily})
        assert _partitions_def_key(mp1) == _partitions_def_key(mp2)


class TestPartitionsDefKeyCrossType:
    """Ensure all types are distinct from each other."""

    def test_all_types_unique(self):
        none_key = _partitions_def_key(None)
        daily_key = _partitions_def_key(DailyPartitionsDefinition(start_date="2024-01-01"))
        static_key = _partitions_def_key(StaticPartitionsDefinition(["A", "B"]))
        dynamic_key = _partitions_def_key(DynamicPartitionsDefinition(name="test"))
        multi_key = _partitions_def_key(
            MultiPartitionsDefinition(
                {
                    "d": DailyPartitionsDefinition(start_date="2024-01-01"),
                    "s": StaticPartitionsDefinition(["X"]),
                }
            )
        )
        all_keys = {none_key, daily_key, static_key, dynamic_key, multi_key}
        assert len(all_keys) == 5, f"Expected 5 unique keys, got {len(all_keys)}"


# ============================================================================
# Unit tests: _partitions_group_key
# ============================================================================


class TestPartitionsGroupKey:
    def test_spec_without_partitions(self):
        spec = AssetSpec("my_asset")
        assert _partitions_group_key(spec) == ("none",)

    def test_spec_with_daily_partitions(self):
        daily = DailyPartitionsDefinition(start_date="2024-01-01")
        spec = AssetSpec("my_asset", partitions_def=daily)
        key = _partitions_group_key(spec)
        assert key[0] == "DailyPartitionsDefinition"

    def test_same_partition_def_same_group(self):
        daily = DailyPartitionsDefinition(start_date="2024-01-01")
        s1 = AssetSpec("asset_a", partitions_def=daily)
        s2 = AssetSpec("asset_b", partitions_def=daily)
        assert _partitions_group_key(s1) == _partitions_group_key(s2)

    def test_different_partition_def_different_group(self):
        daily = DailyPartitionsDefinition(start_date="2024-01-01")
        static = StaticPartitionsDefinition(["A", "B"])
        s1 = AssetSpec("asset_a", partitions_def=daily)
        s2 = AssetSpec("asset_b", partitions_def=static)
        assert _partitions_group_key(s1) != _partitions_group_key(s2)


# ============================================================================
# Integration Test: DbtProjectComponent.build_defs_from_state
# ============================================================================


def test_component_splits_assets_by_partitions_def(monkeypatch, tmp_path):
    """Verify that build_defs_from_state splits a list of mixed-partition specs
    into multiple AssetsDefinitions.
    """
    # 1. Setup fake AssetSpecs with different partition definitions
    key_none = AssetKey("unpartitioned")
    spec_none = AssetSpec(key=key_none)

    key_daily = AssetKey("daily_asset")
    daily_def = DailyPartitionsDefinition(start_date="2024-01-01")
    spec_daily = AssetSpec(key=key_daily, partitions_def=daily_def)

    key_multi = AssetKey("multi_asset")
    multi_def = MultiPartitionsDefinition(
        {
            "date": DailyPartitionsDefinition(start_date="2024-01-01"),
            "static": StaticPartitionsDefinition(["A", "B"]),
        }
    )
    spec_multi = AssetSpec(key=key_multi, partitions_def=multi_def)

    # 2. Monkeypatch build_dbt_specs to return these specs
    def _fake_build_dbt_specs(**kwargs):
        # returns (asset_specs, check_specs)
        return [spec_none, spec_daily, spec_multi], []

    monkeypatch.setattr(
        "dagster_dbt.components.dbt_project.component.build_dbt_specs", _fake_build_dbt_specs
    )

    # 3. Monkeypatch validate_manifest to avoid needing a real manifest
    monkeypatch.setattr(
        "dagster_dbt.components.dbt_project.component.validate_manifest", lambda *_: {"nodes": {}}
    )

    # 4. Construct a DbtProjectComponent.
    # We use the real DbtProject but with a dummy directory
    from dagster_dbt import DbtProject, DbtProjectComponent
    # ComponentLoadContext is available as dg.ComponentLoadContext via imports at module level

    dbt_dir = tmp_path / "dbt_project"
    dbt_dir.mkdir()
    (dbt_dir / "manifest.json").touch()
    (dbt_dir / "dbt_project.yml").write_text("name: test")

    real_project = DbtProject(dbt_dir)

    # Instantiate component
    component = DbtProjectComponent(project=real_project)

    # 5. Create a ComponentLoadContext using the test helper
    from dagster.components.core.component_tree import ComponentTree

    load_context = ComponentTree.for_test().load_context

    # 6. Call build_defs_from_state
    defs = component.build_defs_from_state(load_context, state_path=None)

    # 7. Assertions
    # We expect 3 groups -> 3 AssetsDefinitions
    assert len(defs.assets) == 3

    # Check that we have one op for each partition type
    pdefs = [a.partitions_def for a in defs.assets]

    # One None
    assert any(pd is None for pd in pdefs)
    # One Daily matches our daily_def
    assert any(isinstance(pd, DailyPartitionsDefinition) and pd == daily_def for pd in pdefs)
    # One Multi
    assert any(isinstance(pd, MultiPartitionsDefinition) for pd in pdefs)

    # 8. Verify we can create a job (ensures no definition errors)
    job = dg.define_asset_job("all_assets_job", selection=dg.AssetSelection.all())
    # This construction validates the assets/jobs connectivity
    full_defs = dg.Definitions(assets=defs.assets, jobs=[job])
    assert full_defs
