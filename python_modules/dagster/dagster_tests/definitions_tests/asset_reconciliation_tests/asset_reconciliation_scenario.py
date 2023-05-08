import contextlib
import datetime
import itertools
import os
import random
import sys
from typing import Iterable, List, Mapping, NamedTuple, Optional, Sequence, Set, Union

import mock
import pendulum
from dagster import (
    AssetIn,
    AssetKey,
    AssetOut,
    AssetsDefinition,
    AssetSelection,
    DagsterInstance,
    DataVersion,
    Field,
    Nothing,
    Output,
    PartitionMapping,
    PartitionsDefinition,
    RunRequest,
    SourceAsset,
    asset,
    materialize_to_memory,
    multi_asset,
    observable_source_asset,
    repository,
)
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.asset_reconciliation_sensor import (
    AssetReconciliationCursor,
    reconcile,
)
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.observe import observe
from dagster._core.definitions.partition import (
    PartitionsSubset,
)
from dagster._core.events.log import EventLogEntry
from dagster._core.execution.asset_backfill import AssetBackfillData
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.host_representation.origin import InProcessCodeLocationOrigin
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.test_utils import (
    InProcessTestWorkspaceLoadTarget,
    create_test_daemon_workspace_context,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._daemon.asset_daemon import AssetDaemon


class RunSpec(NamedTuple):
    asset_keys: Sequence[AssetKey]
    partition_key: Optional[str] = None
    failed_asset_keys: Optional[Sequence[AssetKey]] = None
    is_observation: bool = False


class AssetReconciliationScenario(NamedTuple):
    unevaluated_runs: Sequence[RunSpec]
    assets: Optional[Sequence[Union[SourceAsset, AssetsDefinition]]]
    between_runs_delta: Optional[datetime.timedelta] = None
    evaluation_delta: Optional[datetime.timedelta] = None
    cursor_from: Optional["AssetReconciliationScenario"] = None
    current_time: Optional[datetime.datetime] = None
    asset_selection: Optional[AssetSelection] = None
    active_backfill_targets: Optional[Sequence[Mapping[AssetKey, PartitionsSubset]]] = None
    dagster_runs: Optional[Sequence[DagsterRun]] = None
    event_log_entries: Optional[Sequence[EventLogEntry]] = None
    expected_run_requests: Optional[Sequence[RunRequest]] = None
    code_locations: Optional[Mapping[str, Sequence[Union[SourceAsset, AssetsDefinition]]]] = None

    def _get_code_location_origin(
        self, scenario_name, location_name=None
    ) -> InProcessCodeLocationOrigin:
        return InProcessCodeLocationOrigin(
            loadable_target_origin=LoadableTargetOrigin(
                executable_path=sys.executable,
                module_name="dagster_tests.definitions_tests.asset_reconciliation_tests.scenarios",
                working_directory=os.getcwd(),
                attribute="hacky_daemon_repo_"
                + scenario_name
                + (f"_{location_name}" if location_name else ""),
            ),
            location_name=location_name or "test_location",
        )

    def do_sensor_scenario(self, instance, scenario_name=None, with_external_asset_graph=False):
        assert not self.code_locations, "setting code_locations not supported for sensor tests"

        test_time = self.current_time or pendulum.now()

        with pendulum.test(test_time):

            @repository
            def repo():
                return self.assets

            # add any runs to the instance
            for dagster_run in self.dagster_runs or []:
                instance.add_run(dagster_run)

            # add any events to the instance
            for event_log_entry in self.event_log_entries or []:
                instance.store_event(event_log_entry)

            # add any backfills to the instance
            for i, target in enumerate(self.active_backfill_targets or []):
                target_subset = AssetGraphSubset(
                    asset_graph=repo.asset_graph,
                    partitions_subsets_by_asset_key=target,
                    non_partitioned_asset_keys=set(),
                )
                empty_subset = AssetGraphSubset(
                    asset_graph=repo.asset_graph,
                    partitions_subsets_by_asset_key={},
                    non_partitioned_asset_keys=set(),
                )
                asset_backfill_data = AssetBackfillData(
                    latest_storage_id=0,
                    target_subset=target_subset,
                    requested_runs_for_target_roots=False,
                    materialized_subset=empty_subset,
                    requested_subset=empty_subset,
                    failed_and_downstream_subset=empty_subset,
                    backfill_start_time=test_time,
                )
                backfill = PartitionBackfill(
                    backfill_id=f"backfill{i}",
                    status=BulkActionStatus.REQUESTED,
                    from_failure=False,
                    tags={},
                    backfill_timestamp=test_time.timestamp(),
                    serialized_asset_backfill_data=asset_backfill_data.serialize(
                        dynamic_partitions_store=instance
                    ),
                )
                instance.add_backfill(backfill)

            if self.cursor_from is not None:

                @repository
                def prior_repo():
                    return self.cursor_from.assets

                run_requests, cursor = self.cursor_from.do_sensor_scenario(
                    instance,
                    scenario_name=scenario_name,
                    with_external_asset_graph=with_external_asset_graph,
                )
                for run_request in run_requests:
                    instance.create_run_for_job(
                        prior_repo.get_implicit_job_def_for_assets(run_request.asset_selection),
                        asset_selection=set(run_request.asset_selection),
                        tags=run_request.tags,
                    )

                # make sure we can deserialize it using the new asset graph
                cursor = AssetReconciliationCursor.from_serialized(
                    cursor.serialize(), repo.asset_graph
                )

            else:
                cursor = AssetReconciliationCursor.empty()

        start = datetime.datetime.now()

        def test_time_fn():
            return (test_time + (datetime.datetime.now() - start)).timestamp()

        for run in self.unevaluated_runs:
            if self.between_runs_delta is not None:
                test_time += self.between_runs_delta

            with pendulum.test(test_time), mock.patch("time.time", new=test_time_fn):
                if run.is_observation:
                    observe(
                        instance=instance,
                        source_assets=[
                            a
                            for a in self.assets
                            if isinstance(a, SourceAsset) and a.key in run.asset_keys
                        ],
                    )
                else:
                    do_run(
                        asset_keys=run.asset_keys,
                        partition_key=run.partition_key,
                        all_assets=self.assets,
                        instance=instance,
                        failed_asset_keys=run.failed_asset_keys,
                    )

        if self.evaluation_delta is not None:
            test_time += self.evaluation_delta
        with pendulum.test(test_time):
            # get asset_graph
            if not with_external_asset_graph:
                asset_graph = repo.asset_graph
            else:
                assert scenario_name is not None, "scenario_name must be provided for daemon runs"
                with create_test_daemon_workspace_context(
                    workspace_load_target=InProcessTestWorkspaceLoadTarget(
                        self._get_code_location_origin(scenario_name)
                    ),
                    instance=instance,
                ) as workspace_context:
                    workspace = workspace_context.create_request_context()
                    assert (
                        workspace.get_code_location_error("test_location") is None
                    ), workspace.get_code_location_error("test_location")
                    asset_graph = ExternalAssetGraph.from_workspace(workspace)

            target_asset_keys = (
                self.asset_selection.resolve(asset_graph)
                if self.asset_selection
                else asset_graph.non_source_asset_keys
            )

            run_requests, cursor = reconcile(
                asset_graph=asset_graph,
                target_asset_keys=target_asset_keys,
                instance=instance,
                run_tags={},
                cursor=cursor,
            )

        for run_request in run_requests:
            base_job = repo.get_implicit_job_def_for_assets(run_request.asset_selection)
            assert base_job is not None

        return run_requests, cursor

    def do_daemon_scenario(self, instance, scenario_name):
        assert bool(self.assets) != bool(
            self.code_locations
        ), "Must specify either assets or code_locations"

        assert (
            not self.active_backfill_targets
        ), "setting active_backfill_targets not supported for daemon tests"

        test_time = self.current_time or pendulum.now()

        with pendulum.test(test_time) if self.current_time else contextlib.nullcontext():
            if self.cursor_from is not None:
                self.cursor_from.do_daemon_scenario(
                    instance,
                    scenario_name=scenario_name,
                )

        start = datetime.datetime.now()

        def test_time_fn():
            return (test_time + (datetime.datetime.now() - start)).timestamp()

        for run in self.unevaluated_runs:
            if self.between_runs_delta is not None:
                test_time += self.between_runs_delta

            with pendulum.test(test_time), mock.patch("time.time", new=test_time_fn):
                assert not run.is_observation, "Observations not supported for daemon tests"
                if self.assets:
                    do_run(
                        asset_keys=run.asset_keys,
                        partition_key=run.partition_key,
                        all_assets=self.assets,
                        instance=instance,
                        failed_asset_keys=run.failed_asset_keys,
                    )
                else:
                    all_assets = [
                        asset for assets in self.code_locations.values() for asset in assets
                    ]
                    do_run(
                        asset_keys=run.asset_keys,
                        partition_key=run.partition_key,
                        all_assets=all_assets,  # This isn't quite right, it should be filtered to just the assets for the location
                        instance=instance,
                        failed_asset_keys=run.failed_asset_keys,
                    )

        if self.evaluation_delta is not None:
            test_time += self.evaluation_delta
        with pendulum.test(test_time):
            assert scenario_name is not None, "scenario_name must be provided for daemon runs"

            if self.code_locations:
                target = InProcessTestWorkspaceLoadTarget(
                    [
                        self._get_code_location_origin(scenario_name, location_name)
                        for location_name in self.code_locations.keys()
                    ]
                )
            else:
                target = InProcessTestWorkspaceLoadTarget(
                    self._get_code_location_origin(scenario_name)
                )

            with create_test_daemon_workspace_context(
                workspace_load_target=target,
                instance=instance,
            ) as workspace_context:
                workspace = workspace_context.create_request_context()
                assert (
                    workspace.get_code_location_error("test_location") is None
                ), workspace.get_code_location_error("test_location")

                list(AssetDaemon(interval_seconds=42).run_iteration(workspace_context))


def do_run(
    asset_keys: Sequence[AssetKey],
    partition_key: Optional[str],
    all_assets: Sequence[Union[SourceAsset, AssetsDefinition]],
    instance: DagsterInstance,
    failed_asset_keys: Optional[Sequence[AssetKey]] = None,
    tags: Optional[Mapping[str, str]] = None,
) -> None:
    assets_in_run: List[Union[SourceAsset, AssetsDefinition]] = []
    asset_keys_set = set(asset_keys)
    for a in all_assets:
        if isinstance(a, SourceAsset):
            assets_in_run.append(a)
        else:
            selected_keys = asset_keys_set.intersection(a.keys)
            if selected_keys == a.keys:
                assets_in_run.append(a)
            elif not selected_keys:
                assets_in_run.extend(a.to_source_assets())
            else:
                assets_in_run.append(a.subset_for(asset_keys_set))
                assets_in_run.extend(a.subset_for(a.keys - selected_keys).to_source_assets())
    materialize_to_memory(
        instance=instance,
        partition_key=partition_key,
        assets=assets_in_run,
        run_config={
            "ops": {
                failed_asset_key.path[-1]: {"config": {"fail": True}}
                for failed_asset_key in (failed_asset_keys or [])
            }
        },
        raise_on_error=False,
        tags=tags,
    )


def single_asset_run(asset_key: str, partition_key: Optional[str] = None) -> RunSpec:
    return RunSpec(asset_keys=[AssetKey.from_coercible(asset_key)], partition_key=partition_key)


def run(
    asset_keys: Iterable[str],
    partition_key: Optional[str] = None,
    failed_asset_keys: Optional[Iterable[str]] = None,
    is_observation: bool = False,
):
    return RunSpec(
        asset_keys=list(
            map(AssetKey.from_coercible, itertools.chain(asset_keys, failed_asset_keys or []))
        ),
        failed_asset_keys=list(map(AssetKey.from_coercible, failed_asset_keys or [])),
        partition_key=partition_key,
        is_observation=is_observation,
    )


def run_request(asset_keys: List[str], partition_key: Optional[str] = None) -> RunRequest:
    return RunRequest(
        asset_selection=[AssetKey(key) for key in asset_keys],
        partition_key=partition_key,
    )


def asset_def(
    key: str,
    deps: Optional[Union[List[str], Mapping[str, Optional[PartitionMapping]]]] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    freshness_policy: Optional[FreshnessPolicy] = None,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
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
        auto_materialize_policy=auto_materialize_policy,
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
    freshness_policies: Optional[Mapping[str, FreshnessPolicy]] = None,
) -> AssetsDefinition:
    if deps is None:
        non_argument_deps = set()
        internal_asset_deps = None
    elif isinstance(deps, list):
        non_argument_deps = set(deps)
        internal_asset_deps = None
    else:
        non_argument_deps = set().union(*deps.values()) - set(deps.keys())
        internal_asset_deps = {k: {AssetKey(vv) for vv in v} for k, v in deps.items()}

    @multi_asset(
        outs={
            key: AssetOut(
                is_required=not can_subset,
                freshness_policy=freshness_policies.get(key) if freshness_policies else None,
            )
            for key in keys
        },
        name="_".join(keys),
        non_argument_deps=non_argument_deps,
        internal_asset_deps=internal_asset_deps,
        can_subset=can_subset,
    )
    def _assets(context):
        for output in keys:
            if output in context.selected_output_names:
                yield Output(output, output)

    return _assets


def observable_source_asset_def(key: str):
    @observable_source_asset(name=key)
    def _observable():
        return DataVersion(str(random.random()))

    return _observable
