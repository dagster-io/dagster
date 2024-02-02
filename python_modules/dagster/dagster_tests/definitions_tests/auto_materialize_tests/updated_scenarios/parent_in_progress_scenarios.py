from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.auto_materialize_rule import (
    MaterializeOnMissingRule,
    MaterializeOnParentUpdatedRule,
)

from ..asset_daemon_scenario import (
    AssetDaemonScenario,
    AssetDaemonScenarioState,
)

asset_up1 = AssetSpec("up1")
asset_up2 = AssetSpec("up2")
asset_down = AssetSpec("down", deps=[asset_up1, asset_up2])

two_up_assets = AssetDaemonScenarioState(asset_specs=[asset_up1, asset_up2, asset_down])


from ..asset_daemon_scenario import AssetConditionInspector


def asset_inspector_test(state: AssetDaemonScenarioState):
    state1 = state.evaluate_tick()
    inspector1 = AssetConditionInspector(state1)
    assert inspector1.eval_for_key("up1")
    assert inspector1.eval_for_key("up2")
    assert inspector1.eval_for_key("down")
    assert not inspector1.try_eval_for_key("does not exist")

    assert inspector1.eval_result_for_legacy_rule("up1", MaterializeOnMissingRule.__name__)
    assert inspector1.eval_result_for_legacy_rule("up2", MaterializeOnMissingRule.__name__)
    assert inspector1.eval_result_for_legacy_rule("down", MaterializeOnMissingRule.__name__)

    assert not inspector1.eval_result_for_legacy_rule(
        "up1", MaterializeOnParentUpdatedRule.__name__
    )
    assert not inspector1.eval_result_for_legacy_rule(
        "up2", MaterializeOnParentUpdatedRule.__name__
    )
    # The logic here is that this rule does fire because the a parent asset will also
    # be updated within the run that gets instigated. It is true for both reasons
    assert inspector1.eval_result_for_legacy_rule("down", MaterializeOnParentUpdatedRule.__name__)

    state2 = state1.evaluate_tick()
    state2.assert_requested_runs()

    inspector2 = AssetConditionInspector(state2)

    # none of these are missing anwymore
    assert not inspector2.eval_result_for_legacy_rule("up1", MaterializeOnMissingRule.__name__)
    assert not inspector2.eval_result_for_legacy_rule("up2", MaterializeOnMissingRule.__name__)
    assert not inspector2.eval_result_for_legacy_rule("down", MaterializeOnMissingRule.__name__)


parent_progress_scenarios = [
    AssetDaemonScenario(
        id="asset_inspector_test",
        initial_state=two_up_assets.with_all_eager(),
        execution_fn=asset_inspector_test,
    ),
]
