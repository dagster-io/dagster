from dagster import AssetCheckResult, AssetKey, AutoMaterializePolicy, Output, asset
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.auto_materialize_rule import (
    AutoMaterializeRule,
    BlockingAssetCheckRule,
)
from dagster._core.definitions.auto_materialize_rule_evaluation import (
    AutoMaterializeRuleEvaluation,
    ParentUpdatedRuleEvaluationData,
)

from ..base_scenario import (
    AssetEvaluationSpec,
    AssetReconciliationScenario,
    run,
    run_request,
)

eager_with_blocking_check = AutoMaterializePolicy.eager().with_rules(BlockingAssetCheckRule())


@asset(
    auto_materialize_policy=eager_with_blocking_check,
    check_specs=[
        AssetCheckSpec(name="blocking_check", asset="asset1", blocking=True),
        AssetCheckSpec(name="non_blocking_check", asset="asset1"),
    ],
)
def asset1(context):
    yield Output(1)
    yield AssetCheckResult(
        check_name="blocking_check", passed=context.run.tags.get("blocking_check_fail") != "true"
    )
    yield AssetCheckResult(
        check_name="non_blocking_check",
        passed=context.run.tags.get("non_blocking_check_fail") != "true",
    )


@asset(auto_materialize_policy=eager_with_blocking_check, deps=[asset1])
def asset2():
    pass


@asset(auto_materialize_policy=eager_with_blocking_check, deps=[asset2])
def asset3():
    pass


blocking_check_scenarios = {
    "blocking_check_fail_inside_run": AssetReconciliationScenario(
        assets=[asset1, asset2, asset3],
        unevaluated_runs=[run(["asset1", "asset2"], tags={"blocking_check_fail": "true"})],
        expected_run_requests=[],
        expected_evaluations=[
            AssetEvaluationSpec(
                asset_key="asset2",
                rule_evaluations=[
                    (
                        AutoMaterializeRuleEvaluation(
                            BlockingAssetCheckRule().to_snapshot(), evaluation_data=None
                        ),
                        None,
                    ),
                ],
            ),
        ],
    ),
    "blocking_check_fail_across_runs": AssetReconciliationScenario(
        assets=[asset1, asset2, asset3],
        unevaluated_runs=[run(["asset1"], tags={"blocking_check_fail": "true"})],
        expected_run_requests=[],
        expected_evaluations=[
            AssetEvaluationSpec(
                asset_key="asset2",
                rule_evaluations=[
                    (
                        AutoMaterializeRuleEvaluation(
                            AutoMaterializeRule.materialize_on_missing().to_snapshot(),
                            evaluation_data=None,
                        ),
                        None,
                    ),
                    (
                        AutoMaterializeRuleEvaluation(
                            AutoMaterializeRule.materialize_on_parent_updated().to_snapshot(),
                            evaluation_data=ParentUpdatedRuleEvaluationData(
                                updated_asset_keys=frozenset({AssetKey(["asset1"])}),
                                will_update_asset_keys=frozenset(),
                            ),
                        ),
                        None,
                    ),
                    (
                        AutoMaterializeRuleEvaluation(
                            BlockingAssetCheckRule().to_snapshot(), evaluation_data=None
                        ),
                        None,
                    ),
                ],
                num_skipped=1,
            ),
        ],
    ),
    "blocking_check_pass_inside_run": AssetReconciliationScenario(
        assets=[asset1, asset2, asset3],
        unevaluated_runs=[run(["asset1", "asset2"])],
        expected_run_requests=[run_request(["asset3"])],
    ),
    "blocking_check_pass_across_runs": AssetReconciliationScenario(
        assets=[asset1, asset2, asset3],
        unevaluated_runs=[run(["asset1"])],
        expected_run_requests=[run_request(["asset2", "asset3"])],
    ),
    "non_blocking_check_pass_inside_run": AssetReconciliationScenario(
        assets=[asset1, asset2, asset3],
        unevaluated_runs=[run(["asset1", "asset2"], tags={"non_blocking_check_fail": "true"})],
        expected_run_requests=[run_request(["asset3"])],
    ),
    "non_blocking_check_pass_across_runs": AssetReconciliationScenario(
        assets=[asset1, asset2, asset3],
        unevaluated_runs=[run(["asset1"], tags={"non_blocking_check_fail": "true"})],
        expected_run_requests=[run_request(["asset2", "asset3"])],
    ),
}
