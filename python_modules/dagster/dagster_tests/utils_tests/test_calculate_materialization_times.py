from collections import defaultdict
from datetime import datetime

import pytest

from dagster import (
    AssetKey,
    AssetOut,
    AssetSelection,
    DagsterEventType,
    EventRecordsFilter,
    Output,
    asset,
    multi_asset,
    repository,
)
from dagster._core.definitions.asset_layer import build_asset_selection_job
from dagster._core.selector.subset_selector import generate_asset_dep_graph
from dagster._core.test_utils import instance_for_test
from dagster._utils.calculate_data_time import get_upstream_materialization_times_for_record


@pytest.mark.parametrize(
    ["relative_to", "runs_to_expected_data_times_index"],
    [
        (
            "ROOTS",
            [
                ("ace", {"ace": {"a": 0}}),
                ("abd", {"ab": {"a": 1}, "cde": {"a": 0}}),
                ("ac", {"ac": {"a": 2}, "b": {"a": 1}, "ed": {"a": 0}}),
                ("e", {"ace": {"a": 2}, "b": {"a": 1}, "d": {"a": 0}}),
            ],
        ),
        (
            "ROOTS",
            [
                ("abcf", {"abc": {"a": 0}}),
                ("bd", {"abd": {"a": 0}}),
                ("a", {"a": {"a": 2}, "bcd": {"a": 0}}),
                ("f", {"a": {"a": 2}, "bcdf": {"a": 0}}),
                ("bdf", {"ab": {"a": 2}, "cdf": {"a": 0}}),
                ("c", {"abc": {"a": 2}, "df": {"a": 0}}),
                ("df", {"abcdf": {"a": 2}}),
            ],
        ),
        (
            "SELF",
            [
                ("abcdef", {a: {a: 0} for a in "abcdef"}),
                ("abc", {a: {a: 1 if a in "abc" else 0} for a in "abcdef"}),
                ("def", {a: {a: 2 if a in "def" else 1} for a in "abcdef"}),
                ("abcdef", {a: {a: 3} for a in "abcdef"}),
                ("acd", {a: {a: 4 if a in "acd" else 3} for a in "abcdef"}),
                ("bef", {a: {a: 5 if a in "bef" else 4} for a in "abcdef"}),
            ],
        ),
        (
            "bc",
            [
                ("abcd", {"d": {"b": 0, "c": 0}}),
                ("acd", {"d": {"b": 0, "c": 1}}),
                ("abd", {"d": {"b": 2, "c": 1}}),
                ("f", {"df": {"b": 2, "c": 1}}),
            ],
        ),
        (
            "ac",
            [
                ("abcd", {"d": {"a": 0, "c": 0}}),
                ("ce", {"d": {"a": 0, "c": 0}, "e": {"a": 0, "c": 1}}),
                ("df", {"de": {"a": 0, "c": 1}}),
                ("abc", {"de": {"a": 0, "c": 1}}),
                ("d", {"d": {"a": 3, "c": 3}, "e": {"a": 0, "c": 1}}),
            ],
        ),
    ],
)
def test_calculate_data_time(relative_to, runs_to_expected_data_times_index):
    """
    A = B = D = F
     \\  //
       C = E
    B,C,D share an op
    """

    @asset
    def a():
        return 1

    @multi_asset(
        non_argument_deps={AssetKey("a")},
        outs={
            "b": AssetOut(is_required=False),
            "c": AssetOut(is_required=False),
            "d": AssetOut(is_required=False),
        },
        can_subset=True,
        internal_asset_deps={
            "b": {AssetKey("a")},
            "c": {AssetKey("a")},
            "d": {AssetKey("b"), AssetKey("c")},
        },
    )
    def bcd(context):
        for output_name in sorted(context.selected_output_names):
            yield Output(output_name, output_name)

    @asset(non_argument_deps={AssetKey("c")})
    def e():
        return 1

    @asset(non_argument_deps={AssetKey("d")})
    def f():
        return 1

    all_assets = [a, bcd, e, f]

    upstream_mapping = generate_asset_dep_graph(all_assets, [])["upstream"]

    @repository
    def my_repo():
        return [all_assets]

    def _get_root_keys(key_str):
        upstream_key_strs = upstream_mapping[key_str]
        if not upstream_key_strs:
            return {AssetKey.from_user_string(key_str)}
        return set().union(
            *(_get_root_keys(upstream_key_str) for upstream_key_str in upstream_key_strs)
        )

    with instance_for_test() as instance:

        # mapping from asset key to a mapping of materialization timestamp to run index
        materialization_times_index = defaultdict(dict)

        for idx, (to_materialize, expected_index_mapping) in enumerate(
            runs_to_expected_data_times_index
        ):
            # materialize selected assets
            result = build_asset_selection_job(
                "materialize_job",
                assets=all_assets,
                source_assets=[],
                asset_selection=AssetSelection.keys(*(AssetKey(c) for c in to_materialize)).resolve(
                    all_assets
                ),
            ).execute_in_process(instance=instance)

            assert result.success

            # build mapping of expected timestamps
            for entry in instance.all_logs(
                result.run_id, of_type=DagsterEventType.ASSET_MATERIALIZATION
            ):
                asset_key = entry.dagster_event.event_specific_data.materialization.asset_key
                materialization_times_index[asset_key][idx] = datetime.fromtimestamp(
                    entry.timestamp
                )

            for asset_keys, expected_data_times in expected_index_mapping.items():
                for ak in asset_keys:
                    latest_asset_record = instance.get_event_records(
                        EventRecordsFilter(
                            event_type=DagsterEventType.ASSET_MATERIALIZATION,
                            asset_key=AssetKey(ak),
                        ),
                        ascending=False,
                        limit=1,
                    )[0]
                    if relative_to == "ROOTS":
                        relevant_upstream_keys = _get_root_keys(ak)
                    elif relative_to == "SELF":
                        relevant_upstream_keys = {AssetKey(ak)}
                    else:
                        relevant_upstream_keys = {AssetKey(u) for u in relative_to}
                    upstream_data_times = get_upstream_materialization_times_for_record(
                        instance=instance,
                        upstream_asset_key_mapping=upstream_mapping,
                        relevant_upstream_keys=relevant_upstream_keys,
                        record=latest_asset_record,
                    )
                    assert upstream_data_times == {
                        AssetKey(k): materialization_times_index[AssetKey(k)][v]
                        for k, v in expected_data_times.items()
                    }
