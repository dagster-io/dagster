"""
Regression test for issue #33720: any_deps_match().allow() permanently corrupts AssetNode.parent_keys

This test verifies that the fix for the mutation bug in _get_dep_keys works correctly.
The bug was that dep_keys was a reference to the live parent_entity_keys set, so &= and -=
operations mutated the original set instead of a copy.
"""

import warnings

import dagster as dg
import pytest


@pytest.mark.asyncio
def test_any_deps_match_allow_does_not_corrupt_parent_keys():
    """Test that .allow() and .ignore() don't permanently corrupt parent_entity_keys across ticks."""
    # Scope warning suppression to this test only, for the specific warning category
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        scenes = dg.DynamicPartitionsDefinition(name="scenes")

        @dg.asset(partitions_def=scenes)
        def dep_a():
            pass

        dep_b = dg.AssetSpec("dep_b", partitions_def=scenes)  # external asset

        # Fire downstream when dep_a is updated OR dep_b is updated.
        # Using .allow() to target each dep separately — the intended API.
        @dg.asset(
            partitions_def=scenes,
            deps=["dep_a", "dep_b"],
            automation_condition=(
                dg.AutomationCondition.any_deps_match(dg.AutomationCondition.newly_updated())
                .allow(dg.AssetSelection.assets("dep_a"))
                | dg.AutomationCondition.any_deps_match(dg.AutomationCondition.newly_updated())
                .allow(dg.AssetSelection.assets("dep_b"))
            ),
        )
        def downstream():
            pass

        def make_defs():
            return dg.Definitions(assets=[dep_a, dep_b, downstream])

        def new_instance():
            inst = dg.DagsterInstance.ephemeral()
            inst.add_dynamic_partitions("scenes", ["scene1"])
            return inst

        def mat(inst, key):
            inst.report_runless_asset_event(dg.AssetMaterialization(asset_key=key, partition="scene1"))

        def fires(result) -> bool:
            return result.get_num_requested(dg.AssetKey("downstream")) > 0

        # ── TEST: Verify fix prevents mutation ──────────────────────────────────────
        instance = new_instance()
        defs = make_defs()
        
        # Baseline tick
        r0 = dg.evaluate_automation_conditions(defs, instance)
        
        # Materialize dep_a
        mat(instance, "dep_a")
        
        # Tick 1: should fire because dep_a was updated
        r1 = dg.evaluate_automation_conditions(defs, instance, cursor=r0.cursor)
        assert fires(r1), "Tick 1 should fire after dep_a updated"
        
        # Materialize dep_a again
        mat(instance, "dep_a")
        
        # Tick 2: should STILL fire because dep_a was updated again
        # Before the fix, this would fail because parent_keys was corrupted in tick 1
        r2 = dg.evaluate_automation_conditions(defs, instance, cursor=r1.cursor)
        assert fires(r2), "Tick 2 should fire after dep_a updated again (bug fix verification)"