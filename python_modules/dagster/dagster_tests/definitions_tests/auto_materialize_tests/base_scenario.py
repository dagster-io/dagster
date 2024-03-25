import contextlib
import datetime
import itertools
import json
import logging
import os
import random
import sys
from typing import (
    AbstractSet,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

import dagster._check as check
import mock
import pendulum
import pytest
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
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_daemon_context import (
    AssetDaemonContext,
    get_implicit_auto_materialize_policy,
)
from dagster._core.definitions.asset_daemon_cursor import (
    AssetDaemonCursor,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule
from dagster._core.definitions.auto_materialize_rule_evaluation import (
    AutoMaterializeDecisionType,
    AutoMaterializeRuleEvaluation,
    AutoMaterializeRuleEvaluationData,
)
from dagster._core.definitions.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.data_version import DataVersionsByPartition
from dagster._core.definitions.events import CoercibleToAssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.observe import observe
from dagster._core.definitions.partition import (
    PartitionsSubset,
)
from dagster._core.events import AssetMaterializationPlannedData, DagsterEvent, DagsterEventType
from dagster._core.events.log import EventLogEntry
from dagster._core.execution.asset_backfill import AssetBackfillData
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.remote_representation.origin import InProcessCodeLocationOrigin
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.test_utils import (
    InProcessTestWorkspaceLoadTarget,
    create_test_daemon_workspace_context,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._daemon.asset_daemon import AssetDaemon
from dagster._seven.compat.pendulum import pendulum_freeze_time
from dagster._utils import SingleInstigatorDebugCrashFlags


class RunSpec(NamedTuple):
    asset_keys: Sequence[AssetKey]
    partition_key: Optional[str] = None
    failed_asset_keys: Optional[Sequence[AssetKey]] = None
    is_observation: bool = False


class AssetEvaluationSpec(NamedTuple):
    asset_key: str
    rule_evaluations: Sequence[Tuple[AutoMaterializeRuleEvaluation, Optional[Iterable[str]]]]
    num_requested: int = 0
    num_skipped: int = 0
    num_discarded: int = 0

    @staticmethod
    def empty(asset_key: str) -> "AssetEvaluationSpec":
        return AssetEvaluationSpec(
            asset_key=asset_key,
            rule_evaluations=[],
            num_requested=0,
            num_skipped=0,
            num_discarded=0,
        )

    @staticmethod
    def from_single_rule(
        asset_key: str,
        rule: AutoMaterializeRule,
        evaluation_data: Optional[AutoMaterializeRuleEvaluationData] = None,
    ) -> "AssetEvaluationSpec":
        return AssetEvaluationSpec(
            asset_key=asset_key,
            rule_evaluations=[
                (
                    AutoMaterializeRuleEvaluation(
                        rule_snapshot=rule.to_snapshot(), evaluation_data=evaluation_data
                    ),
                    None,
                )
            ],
            num_requested=1 if rule.decision_type == AutoMaterializeDecisionType.MATERIALIZE else 0,
            num_skipped=1 if rule.decision_type == AutoMaterializeDecisionType.SKIP else 0,
            num_discarded=1 if rule.decision_type == AutoMaterializeDecisionType.DISCARD else 0,
        )


class AssetReconciliationScenario(
    NamedTuple(
        "_AssetReconciliationScenario",
        [
            ("unevaluated_runs", Sequence[RunSpec]),
            ("assets", Optional[Sequence[Union[SourceAsset, AssetsDefinition]]]),
            ("asset_checks", Optional[Sequence[AssetChecksDefinition]]),
            ("between_runs_delta", Optional[datetime.timedelta]),
            ("evaluation_delta", Optional[datetime.timedelta]),
            ("cursor_from", Optional["AssetReconciliationScenario"]),
            ("current_time", Optional[datetime.datetime]),
            ("asset_selection", Optional[AssetSelection]),
            (
                "active_backfill_targets",
                Optional[Sequence[Union[Mapping[AssetKey, PartitionsSubset], Sequence[AssetKey]]]],
            ),
            ("dagster_runs", Optional[Sequence[DagsterRun]]),
            ("event_log_entries", Optional[Sequence[EventLogEntry]]),
            ("expected_run_requests", Optional[Sequence[RunRequest]]),
            (
                "code_locations",
                Optional[Mapping[str, Sequence[Union[SourceAsset, AssetsDefinition]]]],
            ),
            ("expected_evaluations", Optional[Sequence[AssetEvaluationSpec]]),
            ("requires_respect_materialization_data_versions", bool),
            ("supports_with_external_asset_graph", bool),
            ("expected_error_message", Optional[str]),
        ],
    )
):
    def __new__(
        cls,
        unevaluated_runs: Sequence[RunSpec],
        assets: Optional[Sequence[Union[SourceAsset, AssetsDefinition]]],
        asset_checks: Optional[Sequence[AssetChecksDefinition]] = None,
        between_runs_delta: Optional[datetime.timedelta] = None,
        evaluation_delta: Optional[datetime.timedelta] = None,
        cursor_from: Optional["AssetReconciliationScenario"] = None,
        current_time: Optional[datetime.datetime] = None,
        asset_selection: Optional[AssetSelection] = None,
        active_backfill_targets: Optional[
            Sequence[Union[Mapping[AssetKey, PartitionsSubset], Sequence[AssetKey]]]
        ] = None,
        dagster_runs: Optional[Sequence[DagsterRun]] = None,
        event_log_entries: Optional[Sequence[EventLogEntry]] = None,
        expected_run_requests: Optional[Sequence[RunRequest]] = None,
        code_locations: Optional[
            Mapping[str, Sequence[Union[SourceAsset, AssetsDefinition]]]
        ] = None,
        expected_evaluations: Optional[Sequence[AssetEvaluationSpec]] = None,
        requires_respect_materialization_data_versions: bool = False,
        supports_with_external_asset_graph: bool = True,
        expected_error_message: Optional[str] = None,
    ) -> "AssetReconciliationScenario":
        # For scenarios with no auto-materialize policies, we infer auto-materialize policies
        # and add them to the assets.
        assets_with_implicit_policies = assets
        if assets and all(
            (isinstance(a, AssetsDefinition) and not a.auto_materialize_policies_by_key)
            or isinstance(a, SourceAsset)
            for a in assets
        ):
            asset_graph = AssetGraph.from_assets([*assets, *(asset_checks or [])])
            auto_materialize_asset_keys = (
                asset_selection.resolve(asset_graph)
                if asset_selection is not None
                else asset_graph.materializable_asset_keys
            )
            assets_with_implicit_policies = with_implicit_auto_materialize_policies(
                assets, asset_graph, auto_materialize_asset_keys
            )

        return super(AssetReconciliationScenario, cls).__new__(
            cls,
            unevaluated_runs=unevaluated_runs,
            assets=assets_with_implicit_policies,
            asset_checks=asset_checks,
            between_runs_delta=between_runs_delta,
            evaluation_delta=evaluation_delta,
            cursor_from=cursor_from,
            current_time=current_time,
            asset_selection=asset_selection,
            active_backfill_targets=active_backfill_targets,
            dagster_runs=dagster_runs,
            event_log_entries=event_log_entries,
            expected_run_requests=expected_run_requests,
            code_locations=code_locations,
            expected_evaluations=expected_evaluations,
            requires_respect_materialization_data_versions=requires_respect_materialization_data_versions,
            supports_with_external_asset_graph=supports_with_external_asset_graph,
            expected_error_message=expected_error_message,
        )

    def _get_code_location_origin(
        self, scenario_name, location_name=None
    ) -> InProcessCodeLocationOrigin:
        """scenarios.py puts all the scenarios in its namespace under different 'hacky_daemon_repo_...' names."""
        return InProcessCodeLocationOrigin(
            loadable_target_origin=LoadableTargetOrigin(
                executable_path=sys.executable,
                module_name=(
                    "dagster_tests.definitions_tests.auto_materialize_tests.scenarios.scenarios"
                ),
                working_directory=os.getcwd(),
                attribute="hacky_daemon_repo_"
                + scenario_name
                + (f"_{location_name}" if location_name else ""),
            ),
            location_name=location_name or "test_location",
        )

    def do_sensor_scenario(
        self,
        instance,
        scenario_name=None,
        with_external_asset_graph=False,
        respect_materialization_data_versions=False,
    ):
        if (
            self.requires_respect_materialization_data_versions
            and not respect_materialization_data_versions
        ):
            pytest.skip("requires respect_materialization_data_versions to be True")
        assert not self.code_locations, "setting code_locations not supported for sensor tests"

        test_time = self.current_time or pendulum.now()

        with pendulum_freeze_time(test_time):

            @repository
            def repo():
                return self.assets

            # add any runs to the instance
            for dagster_run in self.dagster_runs or []:
                instance.add_run(dagster_run)
                # make sure to log the planned events
                for asset_key in dagster_run.asset_selection:
                    event = DagsterEvent(
                        event_type_value=DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                        job_name=dagster_run.job_name,
                        event_specific_data=AssetMaterializationPlannedData(
                            asset_key, partition=(dagster_run.tags or {}).get("dagster/partition")
                        ),
                    )
                    instance.report_dagster_event(event, dagster_run.run_id, logging.DEBUG)

            # add any events to the instance
            for event_log_entry in self.event_log_entries or []:
                instance.store_event(event_log_entry)

            # add any backfills to the instance
            for i, target in enumerate(self.active_backfill_targets or []):
                if isinstance(target, Mapping):
                    target_subset = AssetGraphSubset(
                        partitions_subsets_by_asset_key=target,
                        non_partitioned_asset_keys=set(),
                    )
                else:
                    target_subset = AssetGraphSubset(
                        partitions_subsets_by_asset_key={},
                        non_partitioned_asset_keys=target,
                    )
                empty_subset = AssetGraphSubset(
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
                        dynamic_partitions_store=instance, asset_graph=repo.asset_graph
                    ),
                )
                instance.add_backfill(backfill)

            if self.cursor_from is not None:

                @repository
                def prior_repo():
                    return self.cursor_from.assets

                (
                    run_requests,
                    cursor,
                    evaluations,
                ) = self.cursor_from.do_sensor_scenario(
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

            else:
                cursor = AssetDaemonCursor.empty()

        start = datetime.datetime.now()

        def test_time_fn():
            return (test_time + (datetime.datetime.now() - start)).timestamp()

        for run in self.unevaluated_runs:
            if self.between_runs_delta is not None:
                test_time += self.between_runs_delta

            with pendulum_freeze_time(test_time), mock.patch("time.time", new=test_time_fn):
                if run.is_observation:
                    observe(
                        instance=instance,
                        assets=[
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
        with pendulum_freeze_time(test_time):
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
                    asset_graph = workspace.asset_graph

            auto_materialize_asset_keys = (
                self.asset_selection.resolve(asset_graph)
                if self.asset_selection
                else asset_graph.materializable_asset_keys
            )

            run_requests, cursor, evaluations = AssetDaemonContext(
                evaluation_id=cursor.evaluation_id + 1,
                asset_graph=asset_graph,
                auto_materialize_asset_keys=auto_materialize_asset_keys,
                instance=instance,
                materialize_run_tags={},
                observe_run_tags={},
                cursor=cursor,
                auto_observe_asset_keys={
                    key
                    for key in asset_graph.observable_asset_keys
                    if asset_graph.get(key).auto_observe_interval_minutes is not None
                },
                respect_materialization_data_versions=respect_materialization_data_versions,
                logger=logging.getLogger("dagster.amp"),
            ).evaluate()

        for run_request in run_requests:
            base_job = repo.get_implicit_job_def_for_assets(run_request.asset_selection)
            assert base_job is not None

        return run_requests, cursor, evaluations

    def do_daemon_scenario(
        self,
        instance,
        scenario_name,
        debug_crash_flags: Optional[SingleInstigatorDebugCrashFlags] = None,
    ):
        assert bool(self.assets) != bool(
            self.code_locations
        ), "Must specify either assets or code_locations"

        assert (
            not self.active_backfill_targets
        ), "setting active_backfill_targets not supported for daemon tests"

        test_time = self.current_time or pendulum.now()

        with pendulum_freeze_time(test_time) if self.current_time else contextlib.nullcontext():
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

            with pendulum_freeze_time(test_time), mock.patch("time.time", new=test_time_fn):
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
                        asset
                        for assets in check.not_none(self.code_locations).values()
                        for asset in assets
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
        with pendulum_freeze_time(test_time):
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

                try:
                    list(
                        AssetDaemon(  # noqa: SLF001
                            settings=instance.get_auto_materialize_settings(),
                            pre_sensor_interval_seconds=42,
                        )._run_iteration_impl(
                            workspace_context,
                            threadpool_executor=None,
                            amp_tick_futures={},
                            debug_crash_flags=(debug_crash_flags or {}),
                        )
                    )

                    if self.expected_error_message:
                        raise Exception(
                            f"Failed to raise expected error {self.expected_error_message}"
                        )

                except Exception:
                    if not self.expected_error_message:
                        raise

                    assert self.expected_error_message in str(sys.exc_info())


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
                assets_in_run.append(a.subset_for(asset_keys_set, selected_asset_check_keys=None))
                assets_in_run.extend(
                    a.subset_for(
                        a.keys - selected_keys, selected_asset_check_keys=None
                    ).to_source_assets()
                )
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


FAIL_TAG = "test/fail"


def run_request(
    asset_keys: Sequence[CoercibleToAssetKey],
    partition_key: Optional[str] = None,
    fail_keys: Optional[Sequence[str]] = None,
    tags: Optional[Mapping[str, str]] = None,
) -> RunRequest:
    return RunRequest(
        asset_selection=[AssetKey.from_coercible(key) for key in asset_keys],
        partition_key=partition_key,
        tags={**(tags or {}), **({FAIL_TAG: json.dumps(fail_keys)} if fail_keys else {})},
    )


def asset_def(
    key: str,
    deps: Optional[Union[List[str], Mapping[str, Optional[PartitionMapping]]]] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    freshness_policy: Optional[FreshnessPolicy] = None,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
    code_version: Optional[str] = None,
    config_schema: Optional[Mapping[str, Field]] = None,
) -> AssetsDefinition:
    if deps is None:
        non_argument_deps = None
        ins = None
    elif isinstance(deps, list):
        non_argument_deps = deps
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
        deps=non_argument_deps,
        ins=ins,
        config_schema=config_schema or {"fail": Field(bool, default_value=False)},
        freshness_policy=freshness_policy,
        auto_materialize_policy=auto_materialize_policy,
        code_version=code_version,
    )
    def _asset(context, **kwargs):
        del kwargs

        if context.op_execution_context.op_config["fail"]:
            raise ValueError("")

    return _asset


def multi_asset_def(
    keys: List[str],
    deps: Optional[Union[List[str], Mapping[str, Set[str]]]] = None,
    can_subset: bool = False,
    freshness_policies: Optional[Mapping[str, FreshnessPolicy]] = None,
) -> AssetsDefinition:
    if deps is None:
        non_argument_deps = None
        internal_asset_deps = None
    elif isinstance(deps, list):
        non_argument_deps = deps
        internal_asset_deps = None
    else:
        non_argument_deps = list(set().union(*deps.values()) - set(deps.keys()))
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
        deps=non_argument_deps,
        internal_asset_deps=internal_asset_deps,
        can_subset=can_subset,
    )
    def _assets(context):
        for output in keys:
            if output in context.op_execution_context.selected_output_names:
                yield Output(output, output)

    return _assets


def observable_source_asset_def(
    key: str, partitions_def: Optional[PartitionsDefinition] = None, minutes_to_change: int = 0
):
    def _data_version() -> DataVersion:
        return (
            DataVersion(str(pendulum.now().minute // minutes_to_change))
            if minutes_to_change
            else DataVersion(str(random.random()))
        )

    @observable_source_asset(name=key, partitions_def=partitions_def)
    def _observable():
        if partitions_def is None:
            return _data_version()
        else:
            return DataVersionsByPartition(
                {partition: _data_version() for partition in partitions_def.get_partition_keys()}
            )

    return _observable


def with_auto_materialize_policy(
    assets_defs: Sequence[AssetsDefinition], auto_materialize_policy: AutoMaterializePolicy
) -> Sequence[AssetsDefinition]:
    """Note: this should be implemented in core dagster at some point, and this implementation is
    a lazy hack.
    """
    ret = []
    for assets_def in assets_defs:
        ret.append(assets_def.with_attributes(auto_materialize_policy=auto_materialize_policy))
    return ret


def with_implicit_auto_materialize_policies(
    assets_defs: Sequence[Union[SourceAsset, AssetsDefinition]],
    asset_graph: BaseAssetGraph,
    targeted_assets: Optional[AbstractSet[AssetKey]] = None,
) -> Sequence[AssetsDefinition]:
    """Accepts a list of assets, adding implied auto-materialize policies to targeted assets
    if policies do not exist.
    """
    ret = []
    for assets_def in assets_defs:
        if (
            isinstance(assets_def, AssetsDefinition)
            and not assets_def.auto_materialize_policies_by_key
        ):
            targeted_keys = (
                assets_def.keys & targeted_assets if targeted_assets else assets_def.keys
            )
            auto_materialize_policies_by_key = {}
            for key in targeted_keys:
                policy = get_implicit_auto_materialize_policy(key, asset_graph)
                if policy:
                    auto_materialize_policies_by_key[key] = policy

            ret.append(
                assets_def.with_attributes(auto_materialize_policy=auto_materialize_policies_by_key)
            )
        else:
            ret.append(assets_def)
    return ret
