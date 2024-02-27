from dagster import AutoMaterializeRule
from dagster._core.definitions.asset_condition.asset_condition import AssetCondition, RuleCondition
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy

from ..asset_daemon_scenario import (
    AssetDaemonScenario,
)
from ..base_scenario import run_request
from .asset_daemon_scenario_states import one_asset, two_assets_in_sequence

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
    AssetDaemonScenario(
        id="funky_custom_condition_static_constructor_scenario",
        initial_state=one_asset.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.from_asset_condition(
                # same as above, but with static constructor
                ~(~AssetCondition.missing() & AssetCondition.parent_newer())
            )
        ),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(
            run_request(asset_keys=["A"])
        ),
    ),
    AssetDaemonScenario(
        id="parent_newer_and_not_updated_since_cron_scenario",
        initial_state=two_assets_in_sequence.with_asset_properties(
            "B",
            auto_materialize_policy=AutoMaterializePolicy.from_asset_condition(
                ~AssetCondition.updated_since_cron("@daily") & AssetCondition.parent_newer()
            ),
        ).with_current_time("2024-01-01 00:01:00"),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs()
        .with_runs(run_request("A"))
        # has not been updated since cron, and parent is newer
        .evaluate_tick()
        .assert_requested_runs(run_request("B"))
        .with_runs(run_request("A"))
        # parent is newer, but has been updated since cron
        .evaluate_tick()
        .assert_requested_runs()
        .with_current_time_advanced(days=1)
        # parent is newer, and has not been updated since cron
        .evaluate_tick()
        .assert_requested_runs(run_request("B")),
    ),
]
