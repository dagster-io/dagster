from typing import Sequence

from dagster import _check as check
from dagster._core.definitions.asset_condition import (
    AssetConditionEvaluation,
)
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.auto_materialize_rule import (
    MaterializeOnMissingRule,
    MaterializeOnParentUpdatedRule,
)
from dagster._core.definitions.events import CoercibleToAssetKey

from ..asset_daemon_scenario import (
    AssetDaemonScenario,
    AssetDaemonScenarioState,
)
from ..base_scenario import run_request

asset_up1 = AssetSpec("up1")
asset_up2 = AssetSpec("up2")
asset_down = AssetSpec("down", deps=[asset_up1, asset_up2])

two_up_assets = AssetDaemonScenarioState(asset_specs=[asset_up1, asset_up2, asset_down])


# def get_condition_evals_with_amp_rule_class_name(
#     root_condition_eval: AssetConditionEvaluation, rule_class_name: str
# ) -> Sequence[AssetConditionEvaluation]:
#     condition_evals = []

#     def _recurse(condition_eval: AssetConditionEvaluation):
#         if condition_eval.condition_snapshot.class_name == "RuleCondition":
#             auto_mat_rule = check.not_none(
#                 condition_eval.condition_snapshot.underlying_auto_materialize_rule
#             )
#             if auto_mat_rule.class_name == rule_class_name:
#                 condition_evals.append(condition_eval)
#         for child_condition_eval in condition_eval.child_evaluations:
#             _recurse(child_condition_eval)

#     _recurse(root_condition_eval)
#     return condition_evals


# def get_single_eval(
#     state: AssetDaemonScenarioState, asset_key: CoercibleToAssetKey, class_name: str
# ) -> AssetConditionEvaluation:
#     evals = get_condition_evals_with_amp_rule_class_name(state.eval_for_key(asset_key), class_name)
#     assert len(evals) == 1
#     return evals[0]


# def eval_result_for_legacy_rule(
#     state: AssetDaemonScenarioState, asset_key: CoercibleToAssetKey, legacy_rule: str
# ):
#     return get_single_eval(state, asset_key, legacy_rule).true_subset.bool_value

from ..asset_daemon_scenario import AssetConditionInspector

# def _exec_fn(state: AssetDaemonScenarioState):
#     state1 = state.evaluate_tick()
    

#     # with eager materialization policy, missing materializations should be requested
#     state1.assert_requested_runs(run_request(asset_keys=["up1", "up2", "down"]))

#     assert state1.eval_for_key("up1")
#     assert state1.eval_for_key("up2")
#     assert state1.eval_for_key("down")
#     assert not state1.try_eval_for_key("does not exist")

#     inspector1 = AssetConditionInspector(state1)

#     assert eval_result_for_legacy_rule(state1, "up1", MaterializeOnMissingRule.__name__)
#     assert eval_result_for_legacy_rule(state1, "up2", MaterializeOnMissingRule.__name__)
#     assert eval_result_for_legacy_rule(state1, "down", MaterializeOnMissingRule.__name__)

#     assert not eval_result_for_legacy_rule(state1, "up1", MaterializeOnParentUpdatedRule.__name__)
#     assert not eval_result_for_legacy_rule(state1, "up2", MaterializeOnParentUpdatedRule.__name__)
#     # The logic here is that this rule does fire because the a parent asset will also
#     # be updated within the run that gets instigated. It is true for both reasons
#     assert eval_result_for_legacy_rule(state1, "down", MaterializeOnParentUpdatedRule.__name__)

#     state2 = state1.evaluate_tick()
#     state2.assert_requested_runs()

#     # none of these are missing anwymore
#     assert not eval_result_for_legacy_rule(state2, "up1", MaterializeOnMissingRule.__name__)
#     assert not eval_result_for_legacy_rule(state2, "up2", MaterializeOnMissingRule.__name__)
#     assert not eval_result_for_legacy_rule(state2, "down", MaterializeOnMissingRule.__name__)


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

    assert not inspector1.eval_result_for_legacy_rule("up1", MaterializeOnParentUpdatedRule.__name__)
    assert not inspector1.eval_result_for_legacy_rule("up2", MaterializeOnParentUpdatedRule.__name__)
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
