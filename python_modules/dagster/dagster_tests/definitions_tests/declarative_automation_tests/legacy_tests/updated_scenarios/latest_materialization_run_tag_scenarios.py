from dagster import AutoMaterializeAssetPartitionsFilter, AutoMaterializePolicy, AutoMaterializeRule

from ...scenario_utils.asset_daemon_scenario import AssetDaemonScenario
from ...scenario_utils.base_scenario import run_request
from ...scenario_utils.scenario_specs import (
    one_asset_depends_on_two,
    three_assets_in_sequence,
    two_assets_in_sequence,
)

filter_latest_run_tag_key_policy = (
    AutoMaterializePolicy.eager()
    .without_rules(AutoMaterializeRule.materialize_on_parent_updated())
    .with_rules(
        AutoMaterializeRule.materialize_on_parent_updated(
            updated_parent_filter=AutoMaterializeAssetPartitionsFilter(
                latest_run_required_tags={"dagster/auto_materialize": "true"}
            )
        )
    )
)


latest_materialization_run_tag_scenarios = [
    AssetDaemonScenario(
        id="latest_parent_materialization_has_required_tag",
        initial_spec=two_assets_in_sequence.with_asset_properties(
            auto_materialize_policy=filter_latest_run_tag_key_policy
        ),
        execution_fn=lambda state: state.with_runs(
            run_request(["A", "B"]), run_request(["A"], tags={"dagster/auto_materialize": "true"})
        )
        .evaluate_tick()
        .assert_requested_runs(run_request(["B"])),
    ),
    AssetDaemonScenario(
        id="latest_parent_materialization_missing_required_tag",
        initial_spec=two_assets_in_sequence.with_asset_properties(
            auto_materialize_policy=filter_latest_run_tag_key_policy
        ),
        execution_fn=lambda state: state.with_runs(run_request(["A", "B"]), run_request(["A"]))
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="latest_parent_materialization_missing_one_of_required_tags",
        initial_spec=two_assets_in_sequence.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.eager()
            .without_rules(AutoMaterializeRule.materialize_on_parent_updated())
            .with_rules(
                AutoMaterializeRule.materialize_on_parent_updated(
                    updated_parent_filter=AutoMaterializeAssetPartitionsFilter(
                        latest_run_required_tags={
                            "dagster/auto_materialize": "true",
                            "some_other_key": "some_other_value",
                        }
                    )
                )
            )
        ),
        execution_fn=lambda state: state.with_runs(
            run_request(["A", "B"]), run_request(["A"], tags={"dagster/auto_materialize": "true"})
        )
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="earlier_parent_materialization_missing_required_tag",
        initial_spec=two_assets_in_sequence.with_asset_properties(
            auto_materialize_policy=filter_latest_run_tag_key_policy
        ),
        execution_fn=lambda state: state.with_runs(
            run_request(["A", "B"]),
            run_request(["A"]),
            run_request(["A"], tags={"dagster/auto_materialize": "true"}),
        )
        .evaluate_tick()
        .assert_requested_runs(run_request(["B"])),
    ),
    AssetDaemonScenario(
        id="only_updated_parent_missing_required_tag",
        initial_spec=one_asset_depends_on_two.with_asset_properties(
            auto_materialize_policy=filter_latest_run_tag_key_policy
        ),
        execution_fn=lambda state: state.with_runs(
            run_request(["A", "B", "C"]),
            run_request(["A"]),
        )
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="one_updated_parent_has_required_tag_but_other_does_not",
        initial_spec=one_asset_depends_on_two.with_asset_properties(
            auto_materialize_policy=filter_latest_run_tag_key_policy
        ),
        execution_fn=lambda state: state.with_runs(
            run_request(["A", "B", "C"]),
            run_request(["A"], tags={"dagster/auto_materialize": "true"}),
            run_request(["B"]),
        )
        .evaluate_tick()
        .assert_requested_runs(run_request(["C"])),
    ),
    AssetDaemonScenario(
        id="latest_materialization_missing_required_tag_but_will_update",
        initial_spec=three_assets_in_sequence.with_asset_properties(
            auto_materialize_policy=filter_latest_run_tag_key_policy
        ),
        execution_fn=lambda state: state.with_runs(
            run_request(["A", "B", "C"]),
            run_request(["A", "B"]),
            run_request(["A"], tags={"dagster/auto_materialize": "true"}),
        )
        .evaluate_tick()
        .assert_requested_runs(run_request(["B", "C"])),
    ),
    AssetDaemonScenario(
        # this ensures that updates that happened prior to the cursor of the current tick
        # get ignored if they're missing the required keys
        id="latest_materialization_missing_required_tag_previous_tick",
        initial_spec=one_asset_depends_on_two.with_asset_properties(
            auto_materialize_policy=filter_latest_run_tag_key_policy
        ),
        execution_fn=lambda state: state.with_runs(
            run_request(["A", "B", "C"]),
            run_request(["A"]),
        )
        .evaluate_tick()
        .assert_requested_runs()
        .with_runs(run_request(["B"]))
        .evaluate_tick()
        .assert_requested_runs(),
    ),
]
