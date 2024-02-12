from dagster import AutoMaterializeRule
from dagster._core.definitions.asset_condition import RuleCondition
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy

from ..asset_daemon_scenario import (
    AssetDaemonScenario,
)
from ..base_scenario import run_request
from .asset_daemon_scenario_states import (
    one_asset,
)

custom_condition_scenarios = [
    AssetDaemonScenario(
        id="funky_custom_condition_scenario",
        initial_state=one_asset.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.from_asset_condition(
                # intentionally funky condition
                # not ((not missing) | (parent_updated)) ->
                # it starts missing, and with no parents updated, so this evaluates to true
                ~(
                    ~RuleCondition(AutoMaterializeRule.materialize_on_missing())
                    & RuleCondition(AutoMaterializeRule.materialize_on_parent_updated())
                )
            )
        ),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(
            run_request(asset_keys=["A"])
        ),
    ),
]
