import datetime

from dagster import (
    AssetSelection,
    SourceAsset,
)
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._seven.compat.pendulum import create_pendulum_time

from .asset_reconciliation_scenario import (
    AssetReconciliationScenario,
    asset_def,
    multi_asset_def,
    run,
    run_request,
)
from .basic_scenarios import diamond

freshness_30m = FreshnessPolicy(maximum_lag_minutes=30)
freshness_60m = FreshnessPolicy(maximum_lag_minutes=60)
freshness_1d = FreshnessPolicy(maximum_lag_minutes=24 * 60)
freshness_inf = FreshnessPolicy(maximum_lag_minutes=99999)
freshness_cron = FreshnessPolicy(cron_schedule="0 7 * * *", maximum_lag_minutes=7 * 60)


nothing_dep_freshness = [
    asset_def("asset1", ["some_undefined_source"], freshness_policy=freshness_30m)
]
many_to_one_freshness = [
    asset_def("asset1"),
    asset_def("asset2"),
    asset_def("asset3"),
    asset_def("asset4", ["asset1", "asset2", "asset3"]),
    asset_def("asset5", ["asset4"], freshness_policy=freshness_30m),
]
diamond_freshness = diamond[:-1] + [
    asset_def("asset4", ["asset2", "asset3"], freshness_policy=freshness_30m)
]
overlapping_freshness = diamond + [
    asset_def("asset5", ["asset3"], freshness_policy=freshness_30m),
    asset_def("asset6", ["asset4"], freshness_policy=freshness_60m),
]
overlapping_freshness_with_source = [
    SourceAsset("source_asset"),
    asset_def("asset1", ["source_asset"]),
] + overlapping_freshness[1:]
overlapping_freshness_inf = diamond + [
    asset_def("asset5", ["asset3"], freshness_policy=freshness_30m),
    asset_def("asset6", ["asset4"], freshness_policy=freshness_inf),
]
overlapping_freshness_none = diamond + [
    asset_def("asset5", ["asset3"], freshness_policy=freshness_30m),
    asset_def("asset6", ["asset4"], freshness_policy=None),
]

overlapping_freshness_cron = [
    asset_def("asset1"),
    asset_def("asset2", ["asset1"], freshness_policy=freshness_30m),
    asset_def("asset3", ["asset1"], freshness_policy=freshness_cron),
]


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

freshness_policy_scenarios = {
    "freshness_blank_slate": AssetReconciliationScenario(
        assets=diamond_freshness,
        unevaluated_runs=[],
        expected_run_requests=[run_request(asset_keys=["asset1", "asset2", "asset3", "asset4"])],
    ),
    "freshness_all_fresh": AssetReconciliationScenario(
        assets=diamond_freshness,
        unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4"])],
        expected_run_requests=[],
    ),
    "freshness_all_fresh_with_new_run": AssetReconciliationScenario(
        # expect no runs as the freshness policy will propagate the new change w/in the plan window
        assets=diamond_freshness,
        cursor_from=AssetReconciliationScenario(
            assets=diamond_freshness,
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4"])],
        ),
        unevaluated_runs=[run(["asset1"])],
        expected_run_requests=[],
    ),
    "freshness_all_fresh_with_new_run_stale": AssetReconciliationScenario(
        assets=diamond_freshness,
        cursor_from=AssetReconciliationScenario(
            assets=diamond_freshness,
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4"])],
        ),
        unevaluated_runs=[run(["asset1"])],
        evaluation_delta=datetime.timedelta(minutes=35),
        expected_run_requests=[run_request(asset_keys=["asset1", "asset2", "asset3", "asset4"])],
    ),
    "freshness_half_run": AssetReconciliationScenario(
        assets=diamond_freshness,
        unevaluated_runs=[run(["asset1", "asset2"])],
        expected_run_requests=[run_request(asset_keys=["asset3", "asset4"])],
    ),
    "freshness_nothing_dep": AssetReconciliationScenario(
        assets=nothing_dep_freshness,
        unevaluated_runs=[],
        expected_run_requests=[run_request(asset_keys=["asset1"])],
    ),
    "freshness_many_to_one_some_updated": AssetReconciliationScenario(
        assets=many_to_one_freshness,
        unevaluated_runs=[
            run(["asset1", "asset2", "asset3", "asset4", "asset5"]),
            run(["asset2", "asset3", "asset4", "asset5"]),
        ],
        between_runs_delta=datetime.timedelta(minutes=60),
        expected_run_requests=[run_request(["asset1", "asset4", "asset5"])],
    ),
    "freshness_many_to_one_roots_unselectable": AssetReconciliationScenario(
        assets=many_to_one_freshness,
        # the roots of this graph cannot be executed by this sensor
        asset_selection=AssetSelection.keys("asset4", "asset5"),
        unevaluated_runs=[
            run(["asset1", "asset2", "asset3", "asset4", "asset5"]),
            run(["asset2", "asset3"]),
        ],
        between_runs_delta=datetime.timedelta(minutes=35),
        # should wait for asset1 to become available before launching unnecessary runs
        expected_run_requests=[],
    ),
    "freshness_half_run_with_failure": AssetReconciliationScenario(
        assets=diamond_freshness,
        unevaluated_runs=[
            run(["asset1", "asset2", "asset3", "asset4"]),
            run(["asset3"], failed_asset_keys=["asset3"]),
        ],
        expected_run_requests=[],
    ),
    "freshness_half_run_after_delay": AssetReconciliationScenario(
        assets=diamond_freshness,
        unevaluated_runs=[
            run(["asset1", "asset2", "asset3", "asset4"]),
            run(["asset1", "asset3"]),
        ],
        between_runs_delta=datetime.timedelta(minutes=35),
        evaluation_delta=datetime.timedelta(minutes=5),
        expected_run_requests=[run_request(asset_keys=["asset2", "asset4"])],
    ),
    "freshness_half_run_with_failure_after_delay": AssetReconciliationScenario(
        assets=diamond_freshness,
        unevaluated_runs=[
            run(["asset1", "asset2", "asset3", "asset4"]),
            run(["asset1", "asset2", "asset3"], failed_asset_keys=["asset3"]),
        ],
        between_runs_delta=datetime.timedelta(minutes=35),
        evaluation_delta=datetime.timedelta(minutes=5),
        # even though 4 doesn't have the most up to date data yet, we just tried to materialize
        # asset 3 and it failed, so it doesn't make sense to try to run it again to get 4 up to date
        expected_run_requests=[],
    ),
    "freshness_half_run_with_failure_after_delay2": AssetReconciliationScenario(
        assets=diamond_freshness,
        unevaluated_runs=[
            run(["asset1", "asset2", "asset3", "asset4"]),
            run(["asset1", "asset2", "asset3"], failed_asset_keys=["asset3"]),
        ],
        between_runs_delta=datetime.timedelta(minutes=35),
        evaluation_delta=datetime.timedelta(minutes=35),
        # now that it's been awhile since that run failed, give it another attempt
        expected_run_requests=[run_request(asset_keys=["asset1", "asset2", "asset3", "asset4"])],
    ),
    "freshness_root_failure": AssetReconciliationScenario(
        assets=diamond_freshness,
        unevaluated_runs=[
            run(["asset1", "asset2", "asset3", "asset4"]),
            run(["asset1"], failed_asset_keys=["asset1"]),
        ],
        between_runs_delta=datetime.timedelta(minutes=35),
        evaluation_delta=datetime.timedelta(minutes=5),
        # need to rematerialize all, but asset1 just failed so we don't want to retry immediately
        expected_run_requests=[],
    ),
    "freshness_root_failure_after_delay": AssetReconciliationScenario(
        assets=diamond_freshness,
        unevaluated_runs=[
            run(["asset1", "asset2", "asset3", "asset4"]),
            run(["asset1"], failed_asset_keys=["asset1"]),
        ],
        between_runs_delta=datetime.timedelta(minutes=35),
        evaluation_delta=datetime.timedelta(minutes=35),
        # asset1 failed last time, but it's been awhile so we'll give it another shot
        expected_run_requests=[run_request(asset_keys=["asset1", "asset2", "asset3", "asset4"])],
    ),
    "freshness_half_run_stale": AssetReconciliationScenario(
        assets=diamond_freshness,
        unevaluated_runs=[run(["asset1", "asset2"])],
        evaluation_delta=datetime.timedelta(minutes=35),
        expected_run_requests=[run_request(asset_keys=["asset1", "asset2", "asset3", "asset4"])],
    ),
    "freshness_overlapping_runs": AssetReconciliationScenario(
        assets=overlapping_freshness,
        unevaluated_runs=[run(["asset1", "asset3", "asset5"]), run(["asset2", "asset4", "asset6"])],
        expected_run_requests=[],
    ),
    "freshness_overlapping_with_source": AssetReconciliationScenario(
        assets=overlapping_freshness_with_source,
        unevaluated_runs=[run(["asset1", "asset3", "asset5"]), run(["asset2", "asset4", "asset6"])],
        expected_run_requests=[],
    ),
    "freshness_overlapping_failure": AssetReconciliationScenario(
        assets=overlapping_freshness,
        unevaluated_runs=[
            run(["asset1", "asset2", "asset3", "asset4", "asset5", "asset6"]),
            run(["asset1"], failed_asset_keys=["asset1"]),
        ],
        between_runs_delta=datetime.timedelta(minutes=35),
        # need new data, but don't want to re-run immediately
        expected_run_requests=[],
    ),
    "freshness_overlapping_failure_after_delay": AssetReconciliationScenario(
        assets=overlapping_freshness,
        unevaluated_runs=[
            run(["asset1", "asset2", "asset3", "asset4", "asset5", "asset6"]),
            run(["asset1"], failed_asset_keys=["asset1"]),
        ],
        between_runs_delta=datetime.timedelta(minutes=35),
        evaluation_delta=datetime.timedelta(minutes=35),
        # after 30 minutes, we can try to kick off a run again
        expected_run_requests=[
            run_request(asset_keys=["asset1", "asset2", "asset3", "asset4", "asset5", "asset6"])
        ],
    ),
    "freshness_overlapping_runs_half_stale": AssetReconciliationScenario(
        assets=overlapping_freshness_inf,
        unevaluated_runs=[run(["asset1", "asset3", "asset5"]), run(["asset2", "asset4", "asset6"])],
        # evaluate 35 minutes later, only need to refresh the assets on the shorter freshness policy
        evaluation_delta=datetime.timedelta(minutes=35),
        expected_run_requests=[run_request(asset_keys=["asset1", "asset3", "asset5"])],
    ),
    "freshness_overlapping_defer_propagate": AssetReconciliationScenario(
        assets=overlapping_freshness_inf,
        cursor_from=AssetReconciliationScenario(
            assets=overlapping_freshness_inf,
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4", "asset5", "asset6"])],
        ),
        # change at the top, will not propagate immediately as freshness policies will handle it
        # (even though it will take awhile)
        unevaluated_runs=[run(["asset1"])],
        expected_run_requests=[],
    ),
    "freshness_overlapping_defer_propagate2": AssetReconciliationScenario(
        assets=overlapping_freshness_none,
        cursor_from=AssetReconciliationScenario(
            assets=overlapping_freshness_inf,
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4", "asset5", "asset6"])],
        ),
        # change at the top, doesn't need to be propagated to 1, 3, 5 as freshness policy will
        # handle it, but assets 2, 4, 6 will not recieve an update because they are not
        # upstream of a freshness policy. 2 can be updated immediately, but 4 and 6 depend on
        # 3, so will be defered
        unevaluated_runs=[run(["asset1"])],
        expected_run_requests=[run_request(asset_keys=["asset2"])],
    ),
    "freshness_overlapping_defer_propagate_with_cron": AssetReconciliationScenario(
        assets=overlapping_freshness_cron,
        current_time=create_pendulum_time(year=2023, month=1, day=1, hour=6, tz="UTC"),
        evaluation_delta=datetime.timedelta(minutes=90),
        unevaluated_runs=[
            run(["asset1", "asset2", "asset3"]),
            run(["asset1"]),
        ],
        # don't run asset 3 even though its parent updated as freshness policy will handle it
        expected_run_requests=[run_request(asset_keys=["asset1", "asset2"])],
    ),
    "freshness_non_subsettable_multi_asset_on_top": AssetReconciliationScenario(
        assets=non_subsettable_multi_asset_on_top,
        unevaluated_runs=[run([f"asset{i}" for i in range(1, 6)])],
        evaluation_delta=datetime.timedelta(minutes=35),
        # need to run assets 1, 2 and 3 as they're all part of the same non-subsettable multi asset
        expected_run_requests=[run_request(asset_keys=["asset1", "asset2", "asset3", "asset5"])],
    ),
    "freshness_subsettable_multi_asset_on_top": AssetReconciliationScenario(
        assets=subsettable_multi_asset_on_top,
        unevaluated_runs=[run([f"asset{i}" for i in range(1, 6)])],
        evaluation_delta=datetime.timedelta(minutes=35),
        expected_run_requests=[run_request(asset_keys=["asset2", "asset5"])],
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
