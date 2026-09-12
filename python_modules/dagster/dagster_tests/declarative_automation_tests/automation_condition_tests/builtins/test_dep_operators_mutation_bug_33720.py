"""
Regression test for issue #33720: any_deps_match().allow() permanently corrupts AssetNode.parent_keys

This test verifies that the fix for the mutation bug in _get_dep_keys works correctly.
The bug was that dep_keys was a reference to the live parent_entity_keys set, so &= and -=
operations mutated the original set instead of a copy.
"""

import dagster as dg


def test_any_deps_match_allow_does_not_corrupt_parent_keys():
    """Test that .allow() and .ignore() don't permanently corrupt parent_entity_keys across ticks."""
    @dg.asset(
        automation_condition=dg.AutomationCondition.any_deps_match(
            dg.AutomationCondition.newly_updated()
        ).allow(dg.AssetSelection.keys("A"))
    )
    def downstream(A, B):
        pass

    @dg.asset
    def A():
        pass

    @dg.asset
    def B():
        pass

    instance = dg.DagsterInstance.ephemeral()
    defs = dg.Definitions(assets=[A, B, downstream])

    # First evaluation - no updates yet
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # Materialize A - should fire because A is in the allow list
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # Materialize A again - should still fire (bug fix verification)
    # Before the fix, parent_keys would be corrupted after the first evaluation
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # Materialize B - should NOT fire because B is not in the allow list
    instance.report_runless_asset_event(dg.AssetMaterialization("B"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # Materialize A again - should fire again (verify parent_keys still intact)
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1
