from dagster import AssetSpec, AutoMaterializePolicy, AutoMaterializeRule
from dagster._core.definitions.auto_materialize_rule import SkipOnRunInProgressRule
from dagster._core.definitions.auto_materialize_rule_evaluation import (
    ParentUpdatedRuleEvaluationData,
)

from ..base_scenario import run_request
from ..scenario_specs import (
    diamond,
    one_asset,
    one_asset_depends_on_two,
    three_assets_in_sequence,
    two_assets_depend_on_one,
    two_assets_in_sequence,
)
from ..scenario_state import ScenarioSpec
from .asset_daemon_scenario import (
    AssetDaemonScenario,
    AssetRuleEvaluationSpec,
)

basic_scenarios = [
    AssetDaemonScenario(
        id="one_asset_never_materialized",
        initial_spec=one_asset.with_all_eager(),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(run_request(asset_keys=["A"]))
        .assert_evaluation(
            "A", [AssetRuleEvaluationSpec(rule=AutoMaterializeRule.materialize_on_missing())]
        ),
    ),
    AssetDaemonScenario(
        id="one_asset_already_launched",
        initial_spec=one_asset.with_all_eager(),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(run_request(asset_keys=["A"]))
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="two_assets_in_sequence_never_materialized",
        initial_spec=two_assets_in_sequence.with_all_eager(),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(run_request(asset_keys=["A", "B"]))
        .assert_evaluation(
            "A", [AssetRuleEvaluationSpec(rule=AutoMaterializeRule.materialize_on_missing())]
        )
        .assert_evaluation(
            "B",
            [
                AssetRuleEvaluationSpec(
                    rule=AutoMaterializeRule.materialize_on_parent_updated()
                ).with_rule_evaluation_data(
                    ParentUpdatedRuleEvaluationData,
                    updated_asset_keys=set(),
                    will_update_asset_keys={"A"},
                ),
                AssetRuleEvaluationSpec(rule=AutoMaterializeRule.materialize_on_missing()),
            ],
        ),
    ),
    AssetDaemonScenario(
        id="parent_materialized_child_not",
        initial_spec=two_assets_in_sequence.with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(["A"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B"]))
        .assert_evaluation(
            "B",
            [
                AssetRuleEvaluationSpec(AutoMaterializeRule.materialize_on_missing()),
                AssetRuleEvaluationSpec(
                    AutoMaterializeRule.materialize_on_parent_updated()
                ).with_rule_evaluation_data(
                    ParentUpdatedRuleEvaluationData,
                    updated_asset_keys={"A"},
                    will_update_asset_keys=set(),
                ),
            ],
            num_requested=1,
        )
        .assert_evaluation("A", []),
    ),
    AssetDaemonScenario(
        id="parent_materialized_launch_two_children",
        initial_spec=two_assets_depend_on_one.with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(["A"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B", "C"]))
        .assert_evaluation(
            "B",
            [
                AssetRuleEvaluationSpec(AutoMaterializeRule.materialize_on_missing()),
                AssetRuleEvaluationSpec(
                    AutoMaterializeRule.materialize_on_parent_updated()
                ).with_rule_evaluation_data(
                    ParentUpdatedRuleEvaluationData,
                    updated_asset_keys=set("A"),
                    will_update_asset_keys=set(),
                ),
            ],
        )
        .assert_evaluation(
            "C",
            [
                AssetRuleEvaluationSpec(AutoMaterializeRule.materialize_on_missing()),
                AssetRuleEvaluationSpec(
                    AutoMaterializeRule.materialize_on_parent_updated()
                ).with_rule_evaluation_data(
                    ParentUpdatedRuleEvaluationData,
                    updated_asset_keys=set("A"),
                    will_update_asset_keys=set(),
                ),
            ],
        ),
    ),
    AssetDaemonScenario(
        id="parent_materialized_with_source_asset_launch_child",
        initial_spec=ScenarioSpec(
            asset_specs=[AssetSpec("A"), AssetSpec("B", deps=["A", "source"])]
        ).with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(["A"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B"])),
    ),
    AssetDaemonScenario(
        id="parent_rematerialized_after_tick",
        initial_spec=two_assets_in_sequence.with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(["A", "B"]))
        .evaluate_tick()
        .assert_requested_runs()
        .with_runs(run_request(["A"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B"]))
        .assert_evaluation(
            "B", [AssetRuleEvaluationSpec(AutoMaterializeRule.materialize_on_parent_updated())]
        ),
    ),
    AssetDaemonScenario(
        id="parent_rematerialized",
        initial_spec=two_assets_in_sequence.with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(["A", "B"]), run_request(["A"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B"])),
    ),
    AssetDaemonScenario(
        id="one_parent_materialized_other_never_materialized",
        initial_spec=one_asset_depends_on_two.with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(["A"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B", "C"]))
        .assert_evaluation(
            "B", [AssetRuleEvaluationSpec(AutoMaterializeRule.materialize_on_missing())]
        )
        .assert_evaluation(
            "C",
            [
                AssetRuleEvaluationSpec(AutoMaterializeRule.materialize_on_missing()),
                AssetRuleEvaluationSpec(AutoMaterializeRule.materialize_on_parent_updated()),
            ],
        ),
    ),
    AssetDaemonScenario(
        id="one_parent_materialized_others_materialized_before",
        initial_spec=one_asset_depends_on_two.with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(["A", "B", "C"]))
        .evaluate_tick()
        .assert_requested_runs()
        .with_runs(run_request(["A"]))
        .evaluate_tick("a")
        .assert_requested_runs(run_request(["C"]))
        .assert_evaluation(
            "C",
            [
                AssetRuleEvaluationSpec(
                    AutoMaterializeRule.materialize_on_parent_updated()
                ).with_rule_evaluation_data(
                    ParentUpdatedRuleEvaluationData,
                    updated_asset_keys={"A"},
                    will_update_asset_keys=set(),
                ),
            ],
        ),
    ),
    AssetDaemonScenario(
        id="diamond_never_materialized",
        initial_spec=diamond.with_all_eager(),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(
            run_request(["A", "B", "C", "D"])
        ),
    ),
    AssetDaemonScenario(
        id="diamond_only_root_materialized",
        initial_spec=diamond.with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(["A"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B", "C", "D"])),
    ),
    AssetDaemonScenario(
        id="diamond_root_rematerialized",
        initial_spec=diamond.with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(["A", "B", "C", "D"]))
        .evaluate_tick()
        .assert_requested_runs()
        .with_runs(run_request(["A"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B", "C", "D"]))
        .assert_evaluation(
            "B",
            [
                AssetRuleEvaluationSpec(
                    AutoMaterializeRule.materialize_on_parent_updated()
                ).with_rule_evaluation_data(
                    ParentUpdatedRuleEvaluationData,
                    updated_asset_keys={"A"},
                    will_update_asset_keys=set(),
                )
            ],
        )
        .assert_evaluation(
            "C",
            [
                AssetRuleEvaluationSpec(
                    AutoMaterializeRule.materialize_on_parent_updated()
                ).with_rule_evaluation_data(
                    ParentUpdatedRuleEvaluationData,
                    updated_asset_keys={"A"},
                    will_update_asset_keys=set(),
                )
            ],
        )
        .assert_evaluation(
            "D",
            [
                AssetRuleEvaluationSpec(
                    AutoMaterializeRule.materialize_on_parent_updated()
                ).with_rule_evaluation_data(
                    ParentUpdatedRuleEvaluationData,
                    updated_asset_keys=set(),
                    will_update_asset_keys={"B", "C"},
                )
            ],
        ),
    ),
    AssetDaemonScenario(
        id="diamond_root_and_one_in_middle_rematerialized",
        initial_spec=diamond.with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(["A", "B", "C", "D"]))
        .evaluate_tick()
        .assert_requested_runs()
        .with_runs(run_request(["A", "B"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["C", "D"])),
    ),
    AssetDaemonScenario(
        id="diamond_root_and_sink_rematerialized",
        initial_spec=diamond.with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(["A", "B", "C", "D"]))
        .evaluate_tick()
        .assert_requested_runs()
        .with_runs(run_request(["A", "D"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B", "C", "D"])),
    ),
    AssetDaemonScenario(
        id="parents_materialized_separate_runs",
        initial_spec=three_assets_in_sequence.with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(["A"]), run_request(["B"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["C"])),
    ),
    AssetDaemonScenario(
        id="parent_materialized_twice",
        initial_spec=two_assets_in_sequence.with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(["A"]), run_request(["A"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B"]))
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="parent_rematerialized_twice",
        initial_spec=two_assets_in_sequence.with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(["A", "B"]))
        .evaluate_tick()
        .assert_requested_runs()
        .with_runs(run_request(["A"]), run_request(["A"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B"]))
        .with_not_started_runs()
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    # Ensure that with a rule that skips on run in progress, we don't launch a new run
    AssetDaemonScenario(
        id="asset_in_progress-rule",
        initial_spec=two_assets_in_sequence.with_asset_properties(
            keys=["B"],
            auto_materialize_policy=AutoMaterializePolicy.eager().with_rules(
                SkipOnRunInProgressRule()
            ),
        ),
        execution_fn=lambda state: state.with_runs(run_request(["A"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B"]))
        .with_not_started_runs()
        .evaluate_tick()
        .assert_requested_runs()
        .with_runs(run_request(["A"]))
        .with_in_progress_run_for_asset("B")
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    # Demonstrate the behavior that we will always launch a new run if there is no rule
    AssetDaemonScenario(
        id="asset_in_progress-no-rule",
        initial_spec=two_assets_in_sequence.with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(["A"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B"]))
        .with_not_started_runs()
        .evaluate_tick()
        .assert_requested_runs()
        .with_runs(run_request(["A"]))
        .with_in_progress_run_for_asset("B")
        .evaluate_tick()
        .assert_requested_runs(run_request(["B"])),
    ),
]
