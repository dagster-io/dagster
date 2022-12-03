import contextlib
import datetime
import itertools
from typing import Iterable, List, Mapping, NamedTuple, Optional, Sequence, Set, Union

import pendulum
import pytest

from dagster import (
    AssetIn,
    AssetKey,
    AssetOut,
    AssetSelection,
    AssetsDefinition,
    DagsterInstance,
    DailyPartitionsDefinition,
    Field,
    Nothing,
    Output,
    PartitionKeyRange,
    PartitionMapping,
    PartitionsDefinition,
    RunRequest,
    SourceAsset,
    StaticPartitionsDefinition,
    asset,
    build_asset_reconciliation_sensor,
    build_sensor_context,
    materialize_to_memory,
    multi_asset,
    repository,
)
from dagster._core.definitions.asset_reconciliation_sensor import (
    AssetReconciliationCursor,
    reconcile,
)
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._seven.compat.pendulum import create_pendulum_time


class RunSpec(NamedTuple):
    asset_keys: Sequence[AssetKey]
    partition_key: Optional[str] = None
    failed_asset_keys: Optional[Sequence[AssetKey]] = None


class AssetReconciliationScenario(NamedTuple):
    unevaluated_runs: Sequence[RunSpec]
    assets: Sequence[Union[SourceAsset, AssetsDefinition]]
    evaluation_delta: Optional[datetime.timedelta] = None
    cursor_from: Optional["AssetReconciliationScenario"] = None  # type: ignore
    current_time: Optional[datetime.datetime] = None

    expected_run_requests: Optional[Sequence[RunRequest]] = None

    def do_scenario(self, instance):
        with pendulum.test(self.current_time) if self.current_time else contextlib.nullcontext():

            @repository
            def repo():
                return self.assets

            if self.cursor_from is not None:
                run_requests, cursor = self.cursor_from.do_scenario(instance)
                for run_request in run_requests:
                    instance.create_run_for_pipeline(
                        repo.get_base_job_for_assets(run_request.asset_selection),
                        asset_selection=set(run_request.asset_selection),
                        tags=run_request.tags,
                    )
            else:
                cursor = AssetReconciliationCursor.empty()

            for run in self.unevaluated_runs:
                assets_in_run = []
                run_keys = set(run.asset_keys)
                for asset in self.assets:
                    if isinstance(asset, SourceAsset):
                        assets_in_run.append(asset)
                    else:
                        selected_keys = run_keys.intersection(asset.keys)
                        if selected_keys == asset.keys:
                            assets_in_run.append(asset)
                        elif not selected_keys:
                            assets_in_run.extend(asset.to_source_assets())
                        else:
                            assets_in_run.append(asset.subset_for(run_keys))
                            assets_in_run.extend(
                                asset.subset_for(asset.keys - selected_keys).to_source_assets()
                            )
                materialize_to_memory(
                    instance=instance,
                    partition_key=run.partition_key,
                    assets=assets_in_run,
                    run_config={
                        "ops": {
                            failed_asset_key.path[-1]: {"config": {"fail": True}}
                            for failed_asset_key in (run.failed_asset_keys or [])
                        }
                    },
                    raise_on_error=False,
                )

            with pendulum.test(
                pendulum.now() + self.evaluation_delta
            ) if self.evaluation_delta else contextlib.nullcontext():

                run_requests, cursor = reconcile(
                    repository_def=repo,
                    instance=instance,
                    asset_selection=AssetSelection.all(),
                    run_tags={},
                    cursor=cursor,
                )

            for run_request in run_requests:
                base_job = repo.get_base_job_for_assets(run_request.asset_selection)
                assert base_job is not None

            return run_requests, cursor


def single_asset_run(asset_key: str, partition_key: Optional[str] = None) -> RunSpec:
    return RunSpec(asset_keys=[AssetKey.from_coerceable(asset_key)], partition_key=partition_key)


def run(
    asset_keys: Iterable[str],
    partition_key: Optional[str] = None,
    failed_asset_keys: Optional[Iterable[str]] = None,
):
    return RunSpec(
        asset_keys=list(
            map(AssetKey.from_coerceable, itertools.chain(asset_keys, failed_asset_keys or []))
        ),
        failed_asset_keys=list(map(AssetKey.from_coerceable, failed_asset_keys or [])),
        partition_key=partition_key,
    )


def run_request(asset_keys: List[str], partition_key: Optional[str] = None) -> RunRequest:
    return RunRequest(
        asset_selection=[AssetKey(key) for key in asset_keys],
        tags={PARTITION_NAME_TAG: partition_key} if partition_key else None,
    )


def asset_def(
    key: str,
    deps: Optional[Union[List[str], Mapping[str, PartitionMapping]]] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    freshness_policy: Optional[FreshnessPolicy] = None,
) -> AssetsDefinition:
    if deps is None:
        non_argument_deps = set()
        ins = None
    elif isinstance(deps, list):
        non_argument_deps = set(deps)
        ins = None
    else:
        non_argument_deps = None
        ins = {
            dep: AssetIn(partition_mapping=partition_mapping, dagster_type=Nothing)  # type: ignore
            for dep, partition_mapping in deps.items()
        }

    @asset(
        name=key,
        partitions_def=partitions_def,
        non_argument_deps=non_argument_deps,
        ins=ins,
        config_schema={"fail": Field(bool, default_value=False)},
        freshness_policy=freshness_policy,
    )
    def _asset(context, **kwargs):
        del kwargs

        if context.op_config["fail"]:
            raise ValueError("")

    return _asset


def multi_asset_def(
    keys: List[str],
    deps: Optional[Union[List[str], Mapping[str, Set[str]]]] = None,
    can_subset: bool = False,
) -> AssetsDefinition:
    if deps is None:
        non_argument_deps = set()
        internal_asset_deps = None
    elif isinstance(deps, list):
        non_argument_deps = set(deps)
        internal_asset_deps = None
    else:
        non_argument_deps = set().union(*deps.values())
        internal_asset_deps = {k: {AssetKey(vv) for vv in v} for k, v in deps.items()}

    @multi_asset(
        outs={key: AssetOut(is_required=not can_subset) for key in keys},
        name="_".join(keys),
        non_argument_deps=non_argument_deps,
        internal_asset_deps=internal_asset_deps,
        can_subset=can_subset,
    )
    def _assets(context):
        for output in context.selected_output_names:
            yield Output(output, output)

    return _assets


######################################################################
# The cases
######################################################################


class FanInPartitionMapping(PartitionMapping):
    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range,
        downstream_partitions_def,
        upstream_partitions_def,
    ):
        assert downstream_partition_key_range
        assert downstream_partition_key_range.start == downstream_partition_key_range.end
        downstream_partition_key = downstream_partition_key_range.start
        return PartitionKeyRange(f"{downstream_partition_key}_1", f"{downstream_partition_key}_3")

    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range,
        downstream_partitions_def,
        upstream_partitions_def,
    ):
        assert upstream_partition_key_range
        assert upstream_partition_key_range.start == upstream_partition_key_range.end
        upstream_partition_key = upstream_partition_key_range.start
        result = upstream_partition_key.split("_")[0]
        return PartitionKeyRange(result, result)


class FanOutPartitionMapping(PartitionMapping):
    def get_upstream_partitions_for_partition_range(
        self,
        downstream_partition_key_range,
        downstream_partitions_def,
        upstream_partitions_def,
    ):
        assert downstream_partition_key_range
        assert downstream_partition_key_range.start == downstream_partition_key_range.end
        downstream_partition_key = downstream_partition_key_range.start
        result = downstream_partition_key.split("_")[0]
        return PartitionKeyRange(result, result)

    def get_downstream_partitions_for_partition_range(
        self,
        upstream_partition_key_range,
        downstream_partitions_def,
        upstream_partitions_def,
    ):
        assert upstream_partition_key_range
        assert upstream_partition_key_range.start == upstream_partition_key_range.end
        upstream_partition_key = upstream_partition_key_range.start
        return PartitionKeyRange(f"{upstream_partition_key}_1", f"{upstream_partition_key}_3")


daily_partitions_def = DailyPartitionsDefinition("2013-01-05")
one_partition_partitions_def = StaticPartitionsDefinition(["a"])
two_partitions_partitions_def = StaticPartitionsDefinition(["a", "b"])
fanned_out_partitions_def = StaticPartitionsDefinition(["a_1", "a_2", "a_3"])

freshness_30m = FreshnessPolicy(maximum_lag_minutes=30)
freshness_60m = FreshnessPolicy(maximum_lag_minutes=60)
freshness_inf = FreshnessPolicy(maximum_lag_minutes=99999)

# basics
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

multi_asset_in_middle_subsettable = (
    multi_asset_in_middle[:2]
    + [
        multi_asset_def(
            ["asset3", "asset4"], {"asset3": {"asset1"}, "asset4": {"asset2"}}, can_subset=True
        ),
    ]
    + multi_asset_in_middle[-2:]
)

# freshness policy
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
] + overlapping_freshness[
    1:
]  # type: ignore
overlapping_freshness_inf = diamond + [
    asset_def("asset5", ["asset3"], freshness_policy=freshness_30m),
    asset_def("asset6", ["asset4"], freshness_policy=freshness_inf),
]
overlapping_freshness_none = diamond + [
    asset_def("asset5", ["asset3"], freshness_policy=freshness_30m),
    asset_def("asset6", ["asset4"], freshness_policy=None),
]

non_subsettable_multi_asset_on_top = [
    multi_asset_def(["asset1", "asset2", "asset3"], can_subset=False),
    asset_def("asset4", ["asset1"]),
    asset_def("asset5", ["asset2"], freshness_policy=freshness_30m),
]
subsettable_multi_asset_on_top = [
    multi_asset_def(["asset1", "asset2", "asset3"], can_subset=True)
] + non_subsettable_multi_asset_on_top[1:]

# partitions
one_asset_one_partition = [asset_def("asset1", partitions_def=one_partition_partitions_def)]
one_asset_two_partitions = [asset_def("asset1", partitions_def=two_partitions_partitions_def)]
two_assets_one_partition = [
    asset_def("asset1", partitions_def=one_partition_partitions_def),
    asset_def("asset2", partitions_def=one_partition_partitions_def),
]
two_assets_in_sequence_one_partition = [
    asset_def("asset1", partitions_def=one_partition_partitions_def),
    asset_def("asset2", ["asset1"], partitions_def=one_partition_partitions_def),
]

two_assets_in_sequence_fan_in_partitions = [
    asset_def("asset1", partitions_def=fanned_out_partitions_def),
    asset_def(
        "asset2", {"asset1": FanInPartitionMapping()}, partitions_def=one_partition_partitions_def
    ),
]

two_assets_in_sequence_fan_out_partitions = [
    asset_def("asset1", partitions_def=one_partition_partitions_def),
    asset_def(
        "asset2", {"asset1": FanOutPartitionMapping()}, partitions_def=fanned_out_partitions_def
    ),
]
one_asset_daily_partitions = [asset_def("asset1", partitions_def=daily_partitions_def)]


scenarios = {
    ################################################################################################
    # Basics
    ################################################################################################
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
    ################################################################################################
    # Partial runs
    ################################################################################################
    "partial_run": AssetReconciliationScenario(
        assets=two_assets_in_sequence,
        unevaluated_runs=[run(["asset1"], failed_asset_keys=["asset2"])],
        expected_run_requests=[],
    ),
    ################################################################################################
    # Partitions
    ################################################################################################
    "one_asset_one_partition_never_materialized": AssetReconciliationScenario(
        assets=one_asset_one_partition,
        unevaluated_runs=[],
        expected_run_requests=[run_request(asset_keys=["asset1"], partition_key="a")],
    ),
    "one_asset_two_partitions_never_materialized": AssetReconciliationScenario(
        assets=one_asset_two_partitions,
        unevaluated_runs=[],
        expected_run_requests=[
            run_request(asset_keys=["asset1"], partition_key="a"),
            run_request(asset_keys=["asset1"], partition_key="b"),
        ],
    ),
    "two_assets_one_partition_never_materialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence_one_partition,
        unevaluated_runs=[],
        expected_run_requests=[
            run_request(asset_keys=["asset1", "asset2"], partition_key="a"),
        ],
    ),
    "one_asset_one_partition_already_requested": AssetReconciliationScenario(
        assets=one_asset_one_partition,
        unevaluated_runs=[],
        cursor_from=AssetReconciliationScenario(
            assets=one_asset_one_partition, unevaluated_runs=[]
        ),
        expected_run_requests=[],
    ),
    "one_asset_one_partition_already_materialized": AssetReconciliationScenario(
        assets=one_asset_one_partition,
        unevaluated_runs=[single_asset_run(asset_key="asset1", partition_key="a")],
        expected_run_requests=[],
    ),
    "two_assets_one_partition_already_materialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence_one_partition,
        unevaluated_runs=[run(["asset1", "asset2"], partition_key="a")],
        expected_run_requests=[],
    ),
    "parent_one_partition_one_run": AssetReconciliationScenario(
        assets=two_assets_in_sequence_one_partition,
        unevaluated_runs=[single_asset_run(asset_key="asset1", partition_key="a")],
        expected_run_requests=[run_request(asset_keys=["asset2"], partition_key="a")],
    ),
    "parent_rematerialized_one_partition": AssetReconciliationScenario(
        assets=two_assets_in_sequence_one_partition,
        unevaluated_runs=[
            run(["asset1", "asset2"], partition_key="a"),
            single_asset_run(asset_key="asset1", partition_key="a"),
        ],
        expected_run_requests=[run_request(asset_keys=["asset2"], partition_key="a")],
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
    "one_asset_daily_partitions_never_materialized": AssetReconciliationScenario(
        assets=one_asset_daily_partitions,
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4),
        expected_run_requests=[
            run_request(asset_keys=["asset1"], partition_key="2013-01-05"),
            run_request(asset_keys=["asset1"], partition_key="2013-01-06"),
        ],
    ),
    "one_asset_daily_partitions_two_years_never_materialized": AssetReconciliationScenario(
        assets=one_asset_daily_partitions,
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2015, month=1, day=7, hour=4),
        expected_run_requests=[
            run_request(asset_keys=["asset1"], partition_key=partition_key)
            for partition_key in daily_partitions_def.get_partition_keys(
                current_time=create_pendulum_time(year=2015, month=1, day=7, hour=4)
            )
        ],
    ),
    ################################################################################################
    # Exotic partition-mappings
    ################################################################################################
    "fan_in_partitions_none_materialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence_fan_in_partitions,
        unevaluated_runs=[],
        expected_run_requests=[
            run_request(asset_keys=["asset1"], partition_key="a_1"),
            run_request(asset_keys=["asset1"], partition_key="a_2"),
            run_request(asset_keys=["asset1"], partition_key="a_3"),
        ],
    ),
    "fan_in_partitions_some_materialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence_fan_in_partitions,
        unevaluated_runs=[
            single_asset_run(asset_key="asset1", partition_key="a_1"),
            single_asset_run(asset_key="asset1", partition_key="a_2"),
        ],
        expected_run_requests=[
            run_request(asset_keys=["asset1"], partition_key="a_3"),
        ],
    ),
    "fan_in_partitions_upstream_materialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence_fan_in_partitions,
        unevaluated_runs=[
            single_asset_run(asset_key="asset1", partition_key="a_1"),
            single_asset_run(asset_key="asset1", partition_key="a_2"),
            single_asset_run(asset_key="asset1", partition_key="a_3"),
        ],
        expected_run_requests=[
            run_request(asset_keys=["asset2"], partition_key="a"),
        ],
    ),
    "fan_in_partitions_upstream_materialized_all_materialized_before": AssetReconciliationScenario(
        assets=two_assets_in_sequence_fan_in_partitions,
        unevaluated_runs=[
            single_asset_run(asset_key="asset1", partition_key="a_1"),
            single_asset_run(asset_key="asset1", partition_key="a_2"),
            single_asset_run(asset_key="asset1", partition_key="a_3"),
        ],
        cursor_from=AssetReconciliationScenario(
            assets=two_assets_in_sequence_fan_in_partitions,
            unevaluated_runs=[
                single_asset_run(asset_key="asset1", partition_key="a_1"),
                single_asset_run(asset_key="asset1", partition_key="a_2"),
                single_asset_run(asset_key="asset1", partition_key="a_3"),
                single_asset_run(asset_key="asset2", partition_key="a"),
            ],
        ),
        expected_run_requests=[
            run_request(asset_keys=["asset2"], partition_key="a"),
        ],
    ),
    "fan_out_partitions_upstream_materialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence_fan_out_partitions,
        unevaluated_runs=[single_asset_run(asset_key="asset1", partition_key="a")],
        expected_run_requests=[
            run_request(asset_keys=["asset2"], partition_key="a_1"),
            run_request(asset_keys=["asset2"], partition_key="a_2"),
            run_request(asset_keys=["asset2"], partition_key="a_3"),
        ],
    ),
    "fan_out_partitions_upstream_materialized_all_materialized_before": AssetReconciliationScenario(
        assets=two_assets_in_sequence_fan_out_partitions,
        cursor_from=AssetReconciliationScenario(
            assets=two_assets_in_sequence_fan_out_partitions,
            unevaluated_runs=[
                single_asset_run(asset_key="asset1", partition_key="a"),
                single_asset_run(asset_key="asset2", partition_key="a_1"),
                single_asset_run(asset_key="asset2", partition_key="a_2"),
                single_asset_run(asset_key="asset2", partition_key="a_3"),
            ],
        ),
        unevaluated_runs=[single_asset_run(asset_key="asset1", partition_key="a")],
        expected_run_requests=[
            run_request(asset_keys=["asset2"], partition_key="a_1"),
            run_request(asset_keys=["asset2"], partition_key="a_2"),
            run_request(asset_keys=["asset2"], partition_key="a_3"),
        ],
    ),
    "fan_out_partitions_upstream_materialized_next_tick": AssetReconciliationScenario(
        assets=two_assets_in_sequence_fan_out_partitions,
        unevaluated_runs=[],
        expected_run_requests=[],
        cursor_from=AssetReconciliationScenario(
            assets=two_assets_in_sequence_fan_out_partitions,
            unevaluated_runs=[single_asset_run(asset_key="asset1", partition_key="a")],
        ),
    ),
    "fan_out_partitions_upstream_materialize_two_more_ticks": AssetReconciliationScenario(
        assets=two_assets_in_sequence_fan_out_partitions,
        unevaluated_runs=[],
        expected_run_requests=[],
        cursor_from=AssetReconciliationScenario(
            assets=two_assets_in_sequence_fan_out_partitions,
            unevaluated_runs=[],
            cursor_from=AssetReconciliationScenario(
                assets=two_assets_in_sequence_fan_out_partitions,
                unevaluated_runs=[single_asset_run(asset_key="asset1", partition_key="a")],
            ),
        ),
    ),
    ################################################################################################
    # Freshness policies
    ################################################################################################
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
        assets=overlapping_freshness_with_source,  # type: ignore
        unevaluated_runs=[run(["asset1", "asset3", "asset5"]), run(["asset2", "asset4", "asset6"])],
        expected_run_requests=[],
    ),
    "freshness_overlapping_runs_half_stale": AssetReconciliationScenario(
        assets=overlapping_freshness_with_source,  # type: ignore
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
        # change at the top, doesn't need to be propagated to 1, 3, 5 as freshness policy will
        # handle it, but assets 2, 4, 6 will not recieve an update in the plan window. 2 can be
        # updated immediately, but 4 and 6 depend on 3, so will be defered
        unevaluated_runs=[run(["asset1"])],
        expected_run_requests=[run_request(asset_keys=["asset2"])],
    ),
    "freshness_overlapping_defer_propagate2": AssetReconciliationScenario(
        assets=overlapping_freshness_none,
        cursor_from=AssetReconciliationScenario(
            assets=overlapping_freshness_inf,
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4", "asset5", "asset6"])],
        ),
        # same as above
        unevaluated_runs=[run(["asset1"])],
        expected_run_requests=[run_request(asset_keys=["asset2"])],
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
}


@pytest.mark.parametrize("scenario", list(scenarios.values()), ids=list(scenarios.keys()))
def test_reconciliation(scenario):
    instance = DagsterInstance.ephemeral()
    run_requests, _ = scenario.do_scenario(instance)

    assert len(run_requests) == len(scenario.expected_run_requests)

    def sort_run_request_key_fn(run_request):
        return (min(run_request.asset_selection), run_request.partition_key)

    sorted_run_requests = sorted(run_requests, key=sort_run_request_key_fn)
    sorted_expected_run_requests = sorted(
        scenario.expected_run_requests, key=sort_run_request_key_fn
    )

    for run_request, expected_run_request in zip(sorted_run_requests, sorted_expected_run_requests):
        assert set(run_request.asset_selection) == set(expected_run_request.asset_selection)
        assert run_request.partition_key == expected_run_request.partition_key


@pytest.mark.parametrize(
    "scenario",
    [
        scenarios["diamond_never_materialized"],
        scenarios["one_asset_daily_partitions_never_materialized"],
    ],
)
def test_sensor(scenario):
    assert scenario.cursor_from is None

    @repository
    def repo():
        return scenario.assets

    reconciliation_sensor = build_asset_reconciliation_sensor(AssetSelection.all())
    instance = DagsterInstance.ephemeral()

    with pendulum.test(scenario.current_time):
        context = build_sensor_context(instance=instance, repository_def=repo)
        result = reconciliation_sensor(context)
        assert len(list(result)) == len(scenario.expected_run_requests)

        context2 = build_sensor_context(
            cursor=context.cursor, instance=instance, repository_def=repo
        )
        result2 = reconciliation_sensor(context2)
        assert len(list(result2)) == 0
