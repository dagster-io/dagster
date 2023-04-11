from .asset_reconciliation_scenario import (
    AssetReconciliationScenario,
    asset_def,
    multi_asset_def,
    run,
    run_request,
    single_asset_run,
)

one_asset = [asset_def("asset1")]

two_assets_in_sequence = [asset_def("asset1"), asset_def("asset2", ["asset1"])]
two_assets_depend_on_one = [
    asset_def("asset1"),
    asset_def("asset2", ["asset1"]),
    asset_def("asset3", ["asset1"]),
]
one_asset_depends_on_two = [
    asset_def("parent1"),
    asset_def("parent2"),
    asset_def("child", ["parent1", "parent2"]),
]
two_assets_one_source = [
    asset_def("asset1"),
    asset_def("asset2", ["asset1", "source_asset"]),
]

diamond = [
    asset_def("asset1"),
    asset_def("asset2", ["asset1"]),
    asset_def("asset3", ["asset1"]),
    asset_def("asset4", ["asset2", "asset3"]),
]

three_assets_in_sequence = two_assets_in_sequence + [asset_def("asset3", ["asset2"])]

# multi-assets

multi_asset_in_middle = [
    asset_def("asset1"),
    asset_def("asset2"),
    multi_asset_def(["asset3", "asset4"], {"asset3": {"asset1"}, "asset4": {"asset2"}}),
    asset_def("asset5", ["asset3"]),
    asset_def("asset6", ["asset4"]),
]

multi_asset_after_fork = [
    asset_def("asset1"),
    asset_def("asset2", ["asset1"]),
    asset_def("asset3", ["asset1"]),
    multi_asset_def(["asset4", "asset5"], {"asset4": {"asset3"}, "asset5": {"asset3"}}),
]

multi_asset_in_middle_subsettable = (
    multi_asset_in_middle[:2]
    + [
        multi_asset_def(
            ["asset3", "asset4"], {"asset3": {"asset1"}, "asset4": {"asset2"}}, can_subset=True
        ),
    ]
    + multi_asset_in_middle[-2:]
)


basic_scenarios = {
    "one_asset_never_materialized": AssetReconciliationScenario(
        assets=one_asset,
        unevaluated_runs=[],
        expected_run_requests=[run_request(asset_keys=["asset1"])],
    ),
    "two_assets_in_sequence_never_materialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence,
        unevaluated_runs=[],
        expected_run_requests=[run_request(asset_keys=["asset1", "asset2"])],
    ),
    "one_asset_already_launched": AssetReconciliationScenario(
        assets=one_asset,
        unevaluated_runs=[],
        cursor_from=AssetReconciliationScenario(
            assets=one_asset,
            unevaluated_runs=[],
        ),
        expected_run_requests=[],
    ),
    "parent_materialized_child_not": AssetReconciliationScenario(
        assets=two_assets_in_sequence,
        unevaluated_runs=[single_asset_run(asset_key="asset1")],
        expected_run_requests=[run_request(asset_keys=["asset2"])],
    ),
    "parent_materialized_launch_two_children": AssetReconciliationScenario(
        assets=two_assets_depend_on_one,
        unevaluated_runs=[single_asset_run(asset_key="asset1")],
        expected_run_requests=[run_request(asset_keys=["asset2", "asset3"])],
    ),
    "parent_materialized_with_source_asset_launch_child": AssetReconciliationScenario(
        assets=two_assets_one_source,
        unevaluated_runs=[single_asset_run(asset_key="asset1")],
        expected_run_requests=[run_request(asset_keys=["asset2"])],
    ),
    "parent_rematerialized_after_tick": AssetReconciliationScenario(
        assets=two_assets_in_sequence,
        cursor_from=AssetReconciliationScenario(
            assets=two_assets_in_sequence, unevaluated_runs=[run(["asset1", "asset2"])]
        ),
        unevaluated_runs=[single_asset_run(asset_key="asset1")],
        expected_run_requests=[run_request(asset_keys=["asset2"])],
    ),
    "parent_rematerialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence,
        unevaluated_runs=[
            run(["asset1", "asset2"]),
            single_asset_run(asset_key="asset1"),
        ],
        expected_run_requests=[run_request(asset_keys=["asset2"])],
    ),
    "one_parent_materialized_other_never_materialized": AssetReconciliationScenario(
        assets=one_asset_depends_on_two,
        unevaluated_runs=[single_asset_run(asset_key="parent1")],
        expected_run_requests=[run_request(asset_keys=["parent2", "child"])],
    ),
    "one_parent_materialized_others_materialized_before": AssetReconciliationScenario(
        assets=one_asset_depends_on_two,
        unevaluated_runs=[single_asset_run(asset_key="parent1")],
        cursor_from=AssetReconciliationScenario(
            assets=one_asset_depends_on_two,
            unevaluated_runs=[run(["parent1", "parent2", "child"])],
        ),
        expected_run_requests=[run_request(asset_keys=["child"])],
    ),
    "diamond_never_materialized": AssetReconciliationScenario(
        assets=diamond,
        unevaluated_runs=[],
        expected_run_requests=[run_request(asset_keys=["asset1", "asset2", "asset3", "asset4"])],
    ),
    "diamond_only_root_materialized": AssetReconciliationScenario(
        assets=diamond,
        unevaluated_runs=[single_asset_run("asset1")],
        expected_run_requests=[run_request(asset_keys=["asset2", "asset3", "asset4"])],
    ),
    "diamond_root_rematerialized": AssetReconciliationScenario(
        assets=diamond,
        unevaluated_runs=[single_asset_run("asset1")],
        cursor_from=AssetReconciliationScenario(
            assets=diamond,
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4"])],
        ),
        expected_run_requests=[run_request(asset_keys=["asset2", "asset3", "asset4"])],
    ),
    "diamond_root_and_one_in_middle_rematerialized": AssetReconciliationScenario(
        assets=diamond,
        unevaluated_runs=[run(["asset1", "asset2"])],
        cursor_from=AssetReconciliationScenario(
            assets=diamond,
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4"])],
        ),
        expected_run_requests=[run_request(asset_keys=["asset3", "asset4"])],
    ),
    "diamond_root_and_sink_rematerialized": AssetReconciliationScenario(
        assets=diamond,
        unevaluated_runs=[single_asset_run("asset1"), single_asset_run("asset4")],
        cursor_from=AssetReconciliationScenario(
            assets=diamond,
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4"])],
        ),
        expected_run_requests=[run_request(asset_keys=["asset2", "asset3", "asset4"])],
    ),
    "parents_materialized_separate_runs": AssetReconciliationScenario(
        assets=three_assets_in_sequence,
        unevaluated_runs=[single_asset_run("asset1"), single_asset_run("asset2")],
        expected_run_requests=[run_request(asset_keys=["asset3"])],
    ),
    "parent_materialized_twice": AssetReconciliationScenario(
        assets=two_assets_in_sequence,
        unevaluated_runs=[
            single_asset_run(asset_key="asset1"),
            single_asset_run(asset_key="asset1"),
        ],
        expected_run_requests=[run_request(asset_keys=["asset2"])],
    ),
    "parent_rematerialized_twice": AssetReconciliationScenario(
        assets=two_assets_in_sequence,
        unevaluated_runs=[
            single_asset_run(asset_key="asset1"),
            single_asset_run(asset_key="asset1"),
        ],
        cursor_from=AssetReconciliationScenario(
            assets=two_assets_in_sequence, unevaluated_runs=[run(["asset1", "asset2"])]
        ),
        expected_run_requests=[run_request(asset_keys=["asset2"])],
    ),
    ################################################################################################
    # Multi Assets
    ################################################################################################
    "multi_asset_in_middle_single_parent_rematerialized": AssetReconciliationScenario(
        assets=multi_asset_in_middle,
        unevaluated_runs=[single_asset_run("asset1")],
        cursor_from=AssetReconciliationScenario(
            assets=multi_asset_in_middle,
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4", "asset5", "asset6"])],
        ),
        # don't need to run asset4 for reconciliation but asset4 must run when asset3 does
        expected_run_requests=[run_request(asset_keys=["asset3", "asset4", "asset5"])],
    ),
    "multi_asset_in_middle_single_parent_rematerialized_subsettable": AssetReconciliationScenario(
        assets=multi_asset_in_middle_subsettable,
        unevaluated_runs=[single_asset_run("asset1")],
        cursor_from=AssetReconciliationScenario(
            assets=multi_asset_in_middle,
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4", "asset5", "asset6"])],
        ),
        expected_run_requests=[run_request(asset_keys=["asset3", "asset5"])],
    ),
    "multi_asset_one_parent_unreconciled": AssetReconciliationScenario(
        assets=multi_asset_after_fork,
        unevaluated_runs=[run(["asset1", "asset2"], failed_asset_keys=["asset3"])],
        expected_run_requests=[],
    ),
    ################################################################################################
    # Partial runs
    ################################################################################################
    "partial_run": AssetReconciliationScenario(
        assets=two_assets_in_sequence,
        unevaluated_runs=[run(["asset1"], failed_asset_keys=["asset2"])],
        expected_run_requests=[],
    ),
}
