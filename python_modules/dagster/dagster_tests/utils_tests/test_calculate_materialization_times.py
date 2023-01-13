import datetime
from collections import defaultdict

import mock
import pytest
from dagster import (
    AssetKey,
    AssetOut,
    AssetSelection,
    DagsterEventType,
    DagsterInstance,
    Output,
    asset,
    multi_asset,
    repository,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_layer import build_asset_selection_job
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer


@pytest.mark.parametrize("ignore_asset_tags", [True, False])
@pytest.mark.parametrize(
    ["relative_to", "runs_to_expected_data_times_index"],
    [
        (
            # materialization times are calculated relative to the root assets
            # in this case, the root of all assets in the graph is AssetKey("a")
            "ROOTS",
            [
                # EXPLANATION FOR THIS FORMAT:
                #
                # run assets a,c,e
                # expect assets a,c,e to have upstream materialization times:
                #    {AssetKey("a"): <timestamp of a's asset materialization in run 0 (this run)>}
                ("ace", {"ace": {"a": 0}}),
                #
                # run assets a,b,d
                # expect assets a,b to have upstream materialization times:
                #    {AssetKey("a"): <timestamp of a's asset materialization in run 1 (this run)>}
                # expect assets c,d,e to have upstream materialization times:
                #    {AssetKey("a"): <timestamp of a's asset materialization in run 0 (previous run)>}
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
            # materialization times are calculated relative to the asset itself
            # this sidesteps any of the recursion, you're just looking at the latest materialization
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
            # materialization times are calculated relative to assets b and c
            "bc",
            [
                ("abcd", {"d": {"b": 0, "c": 0}}),
                ("acd", {"d": {"b": 0, "c": 1}}),
                ("abd", {"d": {"b": 2, "c": 1}}),
                ("f", {"df": {"b": 2, "c": 1}}),
            ],
        ),
        (
            # materialization times are calculated relative to assets a and c
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
def test_caching_instance_queryer(
    ignore_asset_tags, relative_to, runs_to_expected_data_times_index
):
    r"""
    A = B = D = F
     \\  //
       C = E
    B,C,D share an op.
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

    asset_graph = AssetGraph.from_assets(all_assets)

    @repository
    def my_repo():
        return [all_assets]

    def _get_root_keys(key):
        upstream_keys = asset_graph.get_parents(key)
        if not upstream_keys:
            return {key}
        return set().union(*(_get_root_keys(upstream_key) for upstream_key in upstream_keys))

    with DagsterInstance.ephemeral() as instance:
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

            # rebuild the data time queryer after each run
            data_time_queryer = CachingInstanceQueryer(instance)

            # build mapping of expected timestamps
            for entry in instance.all_logs(
                result.run_id, of_type=DagsterEventType.ASSET_MATERIALIZATION
            ):
                asset_key = entry.dagster_event.event_specific_data.materialization.asset_key
                materialization_times_index[asset_key][idx] = datetime.datetime.fromtimestamp(
                    entry.timestamp, tz=datetime.timezone.utc
                )

            for asset_keys, expected_data_times in expected_index_mapping.items():
                for ak in asset_keys:
                    latest_asset_record = data_time_queryer.get_latest_materialization_record(
                        AssetKey(ak)
                    )
                    if relative_to == "ROOTS":
                        relevant_upstream_keys = None
                    elif relative_to == "SELF":
                        relevant_upstream_keys = {AssetKey(ak)}
                    else:
                        relevant_upstream_keys = {AssetKey(u) for u in relative_to}
                    if ignore_asset_tags:
                        # simulate an environment where materialization tags were not populated
                        with mock.patch(
                            "dagster.AssetMaterialization.tags", new_callable=mock.PropertyMock
                        ) as tags_property:
                            tags_property.return_value = None
                            upstream_data_times = data_time_queryer.get_used_data_times_for_record(
                                asset_graph=asset_graph,
                                record=latest_asset_record,
                                upstream_keys=relevant_upstream_keys,
                            )
                    else:
                        upstream_data_times = data_time_queryer.get_used_data_times_for_record(
                            asset_graph=asset_graph,
                            record=latest_asset_record,
                            upstream_keys=relevant_upstream_keys,
                        )
                    assert upstream_data_times == {
                        AssetKey(k): materialization_times_index[AssetKey(k)][v]
                        for k, v in expected_data_times.items()
                    }
