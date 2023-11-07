from dagster import AutoMaterializePolicy, AutoMaterializeRule, LatestMaterializationHasRunTag

from ..asset_daemon_scenario import AssetDaemonScenario
from ..base_scenario import run_request
from .asset_daemon_scenario_states import one_asset_depends_on_two, two_assets_in_sequence

filter_latest_run_tag_key_policy = (
    AutoMaterializePolicy.eager()
    .without_rules(AutoMaterializeRule.materialize_on_parent_updated())
    .with_rules(
        AutoMaterializeRule.materialize_on_parent_updated(
            ignore_updates=LatestMaterializationHasRunTag("some_key")
        )
    )
)

filter_latest_run_tag_key_and_value_policy = (
    AutoMaterializePolicy.eager()
    .without_rules(AutoMaterializeRule.materialize_on_parent_updated())
    .with_rules(
        AutoMaterializeRule.materialize_on_parent_updated(
            ignore_updates=LatestMaterializationHasRunTag("some_key", "some_value")
        )
    )
)


latest_materialization_run_tag_scenarios = [
    AssetDaemonScenario(
        id="latest_parent_materialization_does_not_have_ignored_tag",
        initial_state=two_assets_in_sequence.with_asset_properties(
            auto_materialize_policy=filter_latest_run_tag_key_policy
        ),
        execution_fn=lambda state: state.with_runs(run_request(["A", "B"]), run_request(["A"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B"])),
    ),
    AssetDaemonScenario(
        id="latest_parent_materialization_has_ignored_tag",
        initial_state=two_assets_in_sequence.with_asset_properties(
            auto_materialize_policy=filter_latest_run_tag_key_policy
        ),
        execution_fn=lambda state: state.with_runs(
            run_request(["A", "B"]), run_request(["A"], tags={"some_key": "some_value"})
        )
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="latest_parent_materialization_has_ignored_key_but_not_value",
        initial_state=two_assets_in_sequence.with_asset_properties(
            auto_materialize_policy=filter_latest_run_tag_key_and_value_policy
        ),
        execution_fn=lambda state: state.with_runs(
            run_request(["A", "B"]), run_request(["A"], tags={"some_key": "some_other_value"})
        )
        .evaluate_tick()
        .assert_requested_runs(run_request(["B"])),
    ),
    AssetDaemonScenario(
        id="earlier_parent_materialization_has_ignored_tag",
        initial_state=two_assets_in_sequence.with_asset_properties(
            auto_materialize_policy=filter_latest_run_tag_key_policy
        ),
        execution_fn=lambda state: state.with_runs(
            run_request(["A", "B"]),
            run_request(["A"], tags={"some_key": "some_value"}),
            run_request(["A"]),
        )
        .evaluate_tick()
        .assert_requested_runs(run_request(["B"])),
    ),
    AssetDaemonScenario(
        id="only_updated_parent_has_ignored_tag",
        initial_state=one_asset_depends_on_two.with_asset_properties(
            auto_materialize_policy=filter_latest_run_tag_key_policy
        ),
        execution_fn=lambda state: state.with_runs(
            run_request(["A", "B", "C"]),
            run_request(["A"], tags={"some_key": "some_value"}),
        )
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="one_updated_parent_has_ignored_tag_but_other_does_not",
        initial_state=one_asset_depends_on_two.with_asset_properties(
            auto_materialize_policy=filter_latest_run_tag_key_policy
        ),
        execution_fn=lambda state: state.with_runs(
            run_request(["A", "B", "C"]),
            run_request(["A"], tags={"some_key": "some_value"}),
            run_request(["B"]),
        )
        .evaluate_tick()
        .assert_requested_runs(run_request(["C"])),
    ),
]
