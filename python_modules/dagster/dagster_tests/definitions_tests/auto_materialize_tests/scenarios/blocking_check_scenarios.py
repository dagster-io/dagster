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
)

eager_with_blocking_check = AutoMaterializePolicy.eager().with_rules(BlockingAssetCheckRule())


@asset(
    auto_materialize_policy=eager_with_blocking_check,
    check_specs=[AssetCheckSpec(name="check1", asset="asset1", blocking=True)],
)
def asset1():
    yield Output(1)
    yield AssetCheckResult(passed=False)


@asset(auto_materialize_policy=eager_with_blocking_check, deps=[asset1])
def asset2():
    pass


@asset(auto_materialize_policy=eager_with_blocking_check, deps=[asset2])
def asset3():
    pass


blocking_check_scenarios = {
    "blocking_check_inside_run": AssetReconciliationScenario(
        assets=[asset1, asset2, asset3],
        unevaluated_runs=[run(["asset1", "asset2"])],
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
    "blocking_check_across_runs": AssetReconciliationScenario(
        assets=[asset1, asset2, asset3],
        unevaluated_runs=[run(["asset1"])],
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
}
