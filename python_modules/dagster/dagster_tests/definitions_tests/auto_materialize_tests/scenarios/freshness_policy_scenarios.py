import datetime

from dagster import (
    AssetSelection,
    DailyPartitionsDefinition,
)
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule
from dagster._core.definitions.auto_materialize_rule_evaluation import (
    TextRuleEvaluationData,
)
from dagster._core.definitions.freshness_policy import FreshnessPolicy

from ..base_scenario import (
    AssetEvaluationSpec,
    AssetReconciliationScenario,
    asset_def,
    multi_asset_def,
    run,
    run_request,
)

freshness_30m = FreshnessPolicy(maximum_lag_minutes=30)
freshness_60m = FreshnessPolicy(maximum_lag_minutes=60)

non_subsettable_multi_asset_on_top = [
    multi_asset_def(["asset1", "asset2", "asset3"], can_subset=False),
    asset_def("asset4", ["asset1"]),
    asset_def("asset5", ["asset2"], freshness_policy=freshness_30m),
]
subsettable_multi_asset_on_top = [
    multi_asset_def(["asset1", "asset2", "asset3"], can_subset=True)
] + non_subsettable_multi_asset_on_top[1:]

subsettable_multi_asset_complex = [
    asset_def("users"),
    asset_def("orders"),
    asset_def("users_cleaned", ["users"]),
    asset_def("orders_cleaned", ["orders"]),
    multi_asset_def(
        [
            "orders_augmented",
            "order_stats",
            "sku_stats",
            "company_stats",
            "daily_order_summary",
        ],
        can_subset=True,
        deps={
            "orders_augmented": {"orders_cleaned", "users_cleaned"},
            "order_stats": {"orders_augmented"},
            "sku_stats": {"orders_augmented"},
            "company_stats": {"orders_augmented"},
            "daily_order_summary": {"order_stats"},
        },
        freshness_policies={"daily_order_summary": freshness_30m},
    ),
    asset_def("company_perf", ["company_stats"]),
    asset_def("top_users", ["orders_augmented", "company_perf"]),
    asset_def("avg_order", ["company_perf"], freshness_policy=freshness_30m),
]

daily_to_unpartitioned = [
    asset_def("daily", partitions_def=DailyPartitionsDefinition(start_date="2020-01-01")),
    asset_def("unpartitioned", ["daily"], freshness_policy=freshness_30m),
]

freshness_policy_scenarios = {
    "freshness_non_subsettable_multi_asset_on_top": AssetReconciliationScenario(
        assets=non_subsettable_multi_asset_on_top,
        unevaluated_runs=[run([f"asset{i}" for i in range(1, 6)])],
        evaluation_delta=datetime.timedelta(minutes=35),
        # need to run assets 1, 2 and 3 as they're all part of the same non-subsettable multi asset
        expected_run_requests=[run_request(asset_keys=["asset1", "asset2", "asset3", "asset5"])],
        expected_evaluations=[
            AssetEvaluationSpec.from_single_rule(
                "asset2",
                AutoMaterializeRule.materialize_on_required_for_freshness(),
                TextRuleEvaluationData("Required by downstream asset's policy"),
            ),
            AssetEvaluationSpec.from_single_rule(
                "asset5",
                AutoMaterializeRule.materialize_on_required_for_freshness(),
                TextRuleEvaluationData("Required by this asset's policy"),
            ),
        ],
    ),
    "freshness_subsettable_multi_asset_on_top": AssetReconciliationScenario(
        assets=subsettable_multi_asset_on_top,
        unevaluated_runs=[run([f"asset{i}" for i in range(1, 6)])],
        evaluation_delta=datetime.timedelta(minutes=35),
        expected_run_requests=[run_request(asset_keys=["asset2", "asset5"])],
        expected_evaluations=[
            AssetEvaluationSpec.from_single_rule(
                "asset2",
                AutoMaterializeRule.materialize_on_required_for_freshness(),
                TextRuleEvaluationData("Required by downstream asset's policy"),
            ),
            AssetEvaluationSpec.from_single_rule(
                "asset5",
                AutoMaterializeRule.materialize_on_required_for_freshness(),
                TextRuleEvaluationData("Required by this asset's policy"),
            ),
        ],
    ),
    "freshness_complex_subsettable": AssetReconciliationScenario(
        assets=subsettable_multi_asset_complex,
        asset_selection=AssetSelection.keys("avg_order").upstream(),
        unevaluated_runs=[
            # everything exists
            run(
                [
                    "orders",
                    "users",
                    "orders_cleaned",
                    "users_cleaned",
                    "orders_augmented",
                    "order_stats",
                    "sku_stats",
                    "company_stats",
                    "daily_order_summary",
                    "company_perf",
                    "top_users",
                    "avg_order",
                ]
            ),
            # now avg_order references a run that is not the newest
            run(
                [
                    "orders",
                    "users",
                    "orders_cleaned",
                    "users_cleaned",
                    "orders_augmented",
                    "order_stats",
                    "daily_order_summary",
                ]
            ),
        ],
        expected_run_requests=[],
    ),
}
