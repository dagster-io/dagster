import itertools
from typing import Iterable, List, Mapping, NamedTuple, Optional, Sequence, Union

import pytest

from dagster import (
    AssetIn,
    AssetKey,
    AssetSelection,
    AssetsDefinition,
    DagsterInstance,
    DailyPartitionsDefinition,
    Field,
    Nothing,
    PartitionKeyRange,
    PartitionMapping,
    PartitionsDefinition,
    ResourceDefinition,
    RunRequest,
    StaticPartitionsDefinition,
    asset,
    build_asset_reconciliation_sensor,
    build_sensor_context,
    materialize_to_memory,
    repository,
    with_resources,
)
from dagster._core.definitions.asset_reconciliation_sensor import (
    AssetReconciliationCursor,
    reconcile,
)
from dagster._core.storage.tags import PARTITION_NAME_TAG


class PriorRun(NamedTuple):
    asset_keys: Sequence[AssetKey]
    partition_key: Optional[str] = None
    failed_asset_keys: Optional[Sequence[AssetKey]] = None


class AssetReconciliationScenario(NamedTuple):
    prior_runs: Sequence[PriorRun]
    assets: Sequence[AssetsDefinition]
    cursor_from: Optional["AssetReconciliationScenario"] = None

    expected_run_requests: Optional[Sequence[RunRequest]] = None

    def do_scenario(self, instance):
        @repository
        def repo():
            return with_resources(
                self.assets,
                resource_defs={
                    "lock": ResourceDefinition.none_resource(),
                    "assets_to_wait_at": ResourceDefinition.none_resource(),
                },
            )

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

        for run in self.prior_runs:
            assets_in_run = [
                asset if asset.key in run.asset_keys else asset.to_source_assets()[0]
                for asset in self.assets
            ]
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


def single_asset_run(asset_key: str, partition_key: Optional[str] = None) -> PriorRun:
    return PriorRun(asset_keys=[AssetKey.from_coerceable(asset_key)], partition_key=partition_key)


def prior_run(
    asset_keys: Iterable[str],
    partition_key: Optional[str] = None,
    failed_asset_keys: Optional[Iterable[str]] = None,
):
    return PriorRun(
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
            dep: AssetIn(partition_mapping=partition_mapping, dagster_type=Nothing)
            for dep, partition_mapping in deps.items()
        }

    @asset(
        name=key,
        partitions_def=partitions_def,
        non_argument_deps=non_argument_deps,
        ins=ins,
        config_schema={"fail": Field(bool, default_value=False)},
    )
    def _asset(context, **kwargs):
        if context.op_config["fail"]:
            raise ValueError("")

    return _asset


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


daily_partitions_def = DailyPartitionsDefinition("2022-10-31")
one_partition_partitions_def = StaticPartitionsDefinition(["a"])
two_partitions_partitions_def = StaticPartitionsDefinition(["a", "b"])
fanned_out_partitions_def = StaticPartitionsDefinition(["a_1", "a_2", "a_3"])


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

two_assets_in_sequence_same_partitioning = [
    asset_def("asset1", partitions_def=daily_partitions_def),
    asset_def("asset2", ["asset1"], partitions_def=daily_partitions_def),
]

three_assets_in_sequence_same_partitioning = two_assets_in_sequence_same_partitioning + [
    asset_def("asset3", ["asset2"], partitions_def=daily_partitions_def)
]


joined_assets_same_partitioning = [
    asset_def("asset1", partitions_def=daily_partitions_def),
    asset_def("asset2", partitions_def=daily_partitions_def),
    asset_def("asset3", ["asset1", "asset2"], partitions_def=daily_partitions_def),
]


three_assets_in_sequence_prev_partition_mapping = [
    asset_def("asset1", partitions_def=daily_partitions_def),
    asset_def("asset2", ["asset1"], partitions_def=daily_partitions_def),
    asset_def("asset3", {"asset2": None}, partitions_def=daily_partitions_def),
]


scenarios = {
    ################################################################################################
    # Basics
    ################################################################################################
    "one_asset_never_materialized": AssetReconciliationScenario(
        assets=one_asset,
        prior_runs=[],
        expected_run_requests=[run_request(asset_keys=["asset1"])],
    ),
    "two_assets_in_sequence_never_materialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence,
        prior_runs=[],
        expected_run_requests=[run_request(asset_keys=["asset1", "asset2"])],
    ),
    "one_asset_already_launched": AssetReconciliationScenario(
        assets=one_asset,
        prior_runs=[],
        cursor_from=AssetReconciliationScenario(
            assets=one_asset,
            prior_runs=[],
        ),
        expected_run_requests=[],
    ),
    "parent_materialized_child_not": AssetReconciliationScenario(
        assets=two_assets_in_sequence,
        prior_runs=[single_asset_run(asset_key="asset1")],
        expected_run_requests=[run_request(asset_keys=["asset2"])],
    ),
    "parent_materialized_launch_two_children": AssetReconciliationScenario(
        assets=two_assets_depend_on_one,
        prior_runs=[single_asset_run(asset_key="asset1")],
        expected_run_requests=[run_request(asset_keys=["asset2", "asset3"])],
    ),
    "parent_rematerialized_after_tick": AssetReconciliationScenario(
        assets=two_assets_in_sequence,
        cursor_from=AssetReconciliationScenario(
            assets=two_assets_in_sequence, prior_runs=[prior_run(["asset1", "asset2"])]
        ),
        prior_runs=[single_asset_run(asset_key="asset1")],
        expected_run_requests=[run_request(asset_keys=["asset2"])],
    ),
    "parent_rematerialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence,
        prior_runs=[prior_run(["asset1", "asset2"]), single_asset_run(asset_key="asset1")],
        expected_run_requests=[run_request(asset_keys=["asset2"])],
    ),
    "one_parent_materialized_other_never_materialized": AssetReconciliationScenario(
        assets=one_asset_depends_on_two,
        prior_runs=[single_asset_run(asset_key="parent1")],
        expected_run_requests=[run_request(asset_keys=["parent2", "child"])],
    ),
    "one_parent_materialized_others_materialized_before": AssetReconciliationScenario(
        assets=one_asset_depends_on_two,
        prior_runs=[single_asset_run(asset_key="parent1")],
        cursor_from=AssetReconciliationScenario(
            assets=one_asset_depends_on_two, prior_runs=[prior_run(["parent1", "parent2", "child"])]
        ),
        expected_run_requests=[run_request(asset_keys=["child"])],
    ),
    "diamond_only_root_materialized": AssetReconciliationScenario(
        assets=diamond,
        prior_runs=[single_asset_run("asset1")],
        expected_run_requests=[run_request(asset_keys=["asset2", "asset3", "asset4"])],
    ),
    "diamond_root_rematerialized": AssetReconciliationScenario(
        assets=diamond,
        prior_runs=[single_asset_run("asset1")],
        cursor_from=AssetReconciliationScenario(
            assets=diamond, prior_runs=[prior_run(["asset1", "asset2", "asset3", "asset4"])]
        ),
        expected_run_requests=[run_request(asset_keys=["asset2", "asset3", "asset4"])],
    ),
    "diamond_root_and_one_in_middle_rematerialized": AssetReconciliationScenario(
        assets=diamond,
        prior_runs=[prior_run(["asset1", "asset2"])],
        cursor_from=AssetReconciliationScenario(
            assets=diamond, prior_runs=[prior_run(["asset1", "asset2", "asset3", "asset4"])]
        ),
        expected_run_requests=[run_request(asset_keys=["asset3", "asset4"])],
    ),
    "diamond_root_and_sink_rematerialized": AssetReconciliationScenario(
        assets=diamond,
        prior_runs=[single_asset_run("asset1"), single_asset_run("asset4")],
        cursor_from=AssetReconciliationScenario(
            assets=diamond, prior_runs=[prior_run(["asset1", "asset2", "asset3", "asset4"])]
        ),
        expected_run_requests=[run_request(asset_keys=["asset2", "asset3", "asset4"])],
    ),
    "parents_materialized_separate_runs": AssetReconciliationScenario(
        assets=three_assets_in_sequence,
        prior_runs=[single_asset_run("asset1"), single_asset_run("asset2")],
        expected_run_requests=[run_request(asset_keys=["asset3"])],
    ),
    ################################################################################################
    # Partial runs
    ################################################################################################
    "partial_run": AssetReconciliationScenario(
        assets=two_assets_in_sequence,
        prior_runs=[prior_run(["asset1"], failed_asset_keys=["asset2"])],
        expected_run_requests=[],
    ),
}


@pytest.mark.parametrize("scenario", list(scenarios.values()), ids=list(scenarios.keys()))
def test_reconciliation(scenario):
    instance = DagsterInstance.ephemeral()
    run_requests, cursor = scenario.do_scenario(instance)

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


def test_sensor():
    @repository
    def repo():
        return diamond

    reconciliation_sensor = build_asset_reconciliation_sensor(AssetSelection.all())
    instance = DagsterInstance.ephemeral()
    context = build_sensor_context(instance=instance, repository_def=repo)
    result = reconciliation_sensor(context)
    assert len(list(result)) == 1

    context2 = build_sensor_context(cursor=context.cursor, instance=instance, repository_def=repo)
    result2 = reconciliation_sensor(context2)
    assert len(list(result2)) == 0
