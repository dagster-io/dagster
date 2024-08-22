import dataclasses
import itertools
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, NamedTuple, Optional, Sequence, Tuple, Type, cast

import dagster._check as check
from dagster import AssetKey, DagsterInstance, RunRequest, RunsFilter
from dagster._core.definitions.asset_daemon_context import AssetDaemonContext
from dagster._core.definitions.asset_daemon_cursor import (
    AssetDaemonCursor,
    backcompat_deserialize_asset_daemon_cursor_str,
)
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule
from dagster._core.definitions.auto_materialize_rule_evaluation import (
    AutoMaterializeRuleEvaluationData,
)
from dagster._core.definitions.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AssetSubsetWithMetadata,
    AutomationConditionEvaluation,
)
from dagster._core.definitions.events import AssetKeyPartitionKey, CoercibleToAssetKey
from dagster._core.definitions.repository_definition.valid_definitions import (
    SINGLETON_REPOSITORY_NAME,
)
from dagster._core.remote_representation.origin import (
    RemoteInstigatorOrigin,
    RemoteRepositoryOrigin,
)
from dagster._core.scheduler.instigation import SensorInstigatorData, TickStatus
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._core.test_utils import freeze_time, wait_for_futures
from dagster._daemon.asset_daemon import (
    _PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
    _PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
    AssetDaemon,
    _get_pre_sensor_auto_materialize_cursor,
    asset_daemon_cursor_from_instigator_serialized_cursor,
    get_current_evaluation_id,
)
from dagster._serdes.serdes import DeserializationError, deserialize_value, serialize_value

from .base_scenario import run_request
from .scenario_state import ScenarioSpec, ScenarioState, get_code_location_origin


class AssetRuleEvaluationSpec(NamedTuple):
    """Provides a convenient way to specify information about an AutoMaterializeRuleEvaluation
    that is expected to exist within the context of a test.

    Args:
        rule (AutoMaterializeRule): The rule that will exist on the evaluation.
        partitions (Optional[Sequence[str]]): The partition keys that this rule evaluation will
            apply to.
        rule_evaluation_data (Optional[AutoMaterializeRuleEvaluationData]): The specific rule
            evaluation data that will exist on the evaluation.

    """

    rule: AutoMaterializeRule
    partitions: Optional[Sequence[str]] = None
    rule_evaluation_data: Optional[AutoMaterializeRuleEvaluationData] = None

    def with_rule_evaluation_data(
        self, data_type: Type[AutoMaterializeRuleEvaluationData], **kwargs
    ) -> "AssetRuleEvaluationSpec":
        """Adds rule evaluation data of the given type to this spec. Formats keyword which are sets
        of CoercibleToAssetKey into frozensets of AssetKey for convenience.
        """
        transformed_kwargs = {
            key: frozenset(AssetKey.from_coercible(v) for v in value)
            if isinstance(value, set)
            else value
            for key, value in kwargs.items()
        }
        return self._replace(
            rule_evaluation_data=data_type(**transformed_kwargs),
        )

    def resolve(self, asset_key: AssetKey, asset_graph: BaseAssetGraph) -> AssetSubsetWithMetadata:
        """Returns a tuple of the resolved AutoMaterializeRuleEvaluation for this spec and the
        partitions that it applies to.
        """
        subset = AssetSubset.from_asset_partitions_set(
            asset_key,
            asset_graph.get(asset_key).partitions_def,
            {
                AssetKeyPartitionKey(asset_key, partition_key)
                for partition_key in self.partitions or [None]
            },
        )
        metadata = self.rule_evaluation_data.metadata if self.rule_evaluation_data else {}
        return AssetSubsetWithMetadata(subset=subset, metadata=metadata)


@dataclass(frozen=True)
class AssetDaemonScenarioState(ScenarioState):
    """Specifies the state of a given AssetDaemonScenario. This state can be modified by changing
    the set of asset definitions it contains, executing runs, updating the time, evaluating ticks, etc.

    At any point in time, assertions can be made about the state of the scenario. Typically, you
    would add runs to the scenario, evaluate a tick, then make assertions about the runs that were
    requested for that tick, or the evaluations that were stored for each asset.

    Args:
        asset_specs (Sequence[AssetSpec]): The specs describing all assets that are part of this
            scenario.
        current_time (datetime): The current time of the scenario.
    """

    run_requests: Sequence[RunRequest] = field(default_factory=list)
    serialized_cursor: str = field(default=serialize_value(AssetDaemonCursor.empty(0)))
    evaluations: Sequence[AutomationConditionEvaluation] = field(default_factory=list)
    tick_index: int = 1

    # set by scenario runner
    is_daemon: bool = False
    sensor_name: Optional[str] = None
    threadpool_executor: Optional[ThreadPoolExecutor] = None
    request_backfills: bool = False

    def with_serialized_cursor(self, serialized_cursor: str) -> "AssetDaemonScenarioState":
        return dataclasses.replace(self, serialized_cursor=serialized_cursor)

    def _evaluate_tick_fast(
        self,
    ) -> Tuple[Sequence[RunRequest], AssetDaemonCursor, Sequence[AutomationConditionEvaluation]]:
        try:
            cursor = deserialize_value(self.serialized_cursor, AssetDaemonCursor)
        except DeserializationError:
            cursor = backcompat_deserialize_asset_daemon_cursor_str(
                self.serialized_cursor, self.asset_graph, 0
            )

        new_run_requests, new_cursor, new_evaluations = AssetDaemonContext(
            evaluation_id=cursor.evaluation_id + 1,
            asset_graph=self.asset_graph,
            auto_materialize_asset_keys={
                key
                for key in self.asset_graph.materializable_asset_keys
                if self.asset_graph.get(key).auto_materialize_policy is not None
            },
            instance=self.instance,
            materialize_run_tags={},
            observe_run_tags={},
            cursor=cursor,
            auto_observe_asset_keys={
                key
                for key in self.asset_graph.external_asset_keys
                if self.asset_graph.get(key).auto_observe_interval_minutes is not None
            },
            respect_materialization_data_versions=False,
            logger=self.logger,
            request_backfills=self.request_backfills,
        ).evaluate()
        check.is_list(new_run_requests, of_type=RunRequest)
        check.inst(new_cursor, AssetDaemonCursor)
        check.is_list(new_evaluations, of_type=AutomationConditionEvaluation)

        # make sure these run requests are available on the instance
        for request in new_run_requests:
            asset_selection = check.not_none(request.asset_selection)
            job_def = self.scenario_spec.defs.get_implicit_job_def_for_assets(asset_selection)
            self.instance.create_run_for_job(
                job_def=check.not_none(job_def),
                asset_selection=set(asset_selection),
                tags=request.tags,
            )
        return new_run_requests, new_cursor, new_evaluations

    def _evaluate_tick_daemon(
        self,
    ) -> Tuple[
        Sequence[RunRequest],
        AssetDaemonCursor,
        Sequence[AutomationConditionEvaluation],
    ]:
        with self._create_workspace_context() as workspace_context:
            workspace = workspace_context.create_request_context()
            assert (
                workspace.get_code_location_error("test_location") is None
            ), workspace.get_code_location_error("test_location")

            sensor = (
                next(
                    iter(workspace.get_code_location("test_location").get_repositories().values())
                ).get_external_sensor(self.sensor_name)
                if self.sensor_name
                else None
            )

            if sensor:
                # start sensor if it hasn't started already
                self.instance.start_sensor(sensor)

            amp_tick_futures = {}

            list(
                AssetDaemon(  # noqa: SLF001
                    settings=self.instance.get_auto_materialize_settings(),
                    pre_sensor_interval_seconds=42,
                )._run_iteration_impl(
                    workspace_context,
                    threadpool_executor=self.threadpool_executor,
                    amp_tick_futures=amp_tick_futures,
                    debug_crash_flags={},
                )
            )

            wait_for_futures(amp_tick_futures)

            if sensor:
                auto_materialize_instigator_state = check.not_none(
                    self.instance.get_instigator_state(
                        sensor.get_external_origin_id(), sensor.selector_id
                    )
                )
                new_cursor = asset_daemon_cursor_from_instigator_serialized_cursor(
                    cast(
                        SensorInstigatorData,
                        check.not_none(auto_materialize_instigator_state).instigator_data,
                    ).cursor,
                    self.asset_graph,
                )
            else:
                new_cursor = _get_pre_sensor_auto_materialize_cursor(
                    self.instance, self.asset_graph
                )
            new_run_requests = [
                run_request(
                    list(run.asset_selection or []),
                    partition_key=run.tags.get(PARTITION_NAME_TAG),
                )._replace(tags=run.tags)
                for run in self.instance.get_runs(
                    filters=RunsFilter(
                        tags={"dagster/asset_evaluation_id": str(new_cursor.evaluation_id)}
                    )
                )
            ]
            backfill_requests = [
                RunRequest.for_asset_graph_subset(
                    backfill.asset_backfill_data.target_subset, tags=backfill.tags
                )
                for backfill in self.instance.get_backfills()
                if backfill.tags.get("dagster/asset_evaluation_id") == str(new_cursor.evaluation_id)
                and backfill.asset_backfill_data is not None
            ]

            new_run_requests.extend(backfill_requests)
            new_evaluations = [
                e.get_evaluation_with_run_ids(
                    self.asset_graph.get(e.asset_key).partitions_def
                ).evaluation
                for e in check.not_none(
                    self.instance.schedule_storage
                ).get_auto_materialize_evaluations_for_evaluation_id(new_cursor.evaluation_id)
            ]
            return new_run_requests, new_cursor, new_evaluations

    def evaluate_tick_daemon(self):
        with freeze_time(self.current_time):
            run_requests, cursor, _ = self._evaluate_tick_daemon()
        new_state = self.with_serialized_cursor(serialize_value(cursor))
        return new_state, run_requests

    def evaluate_tick(self, label: Optional[str] = None) -> "AssetDaemonScenarioState":
        self.logger.critical("********************************")
        self.logger.critical(f"EVALUATING TICK {label or self.tick_index}")
        self.logger.critical("********************************")

        with freeze_time(self.current_time):
            if self.is_daemon:
                (
                    new_run_requests,
                    new_cursor,
                    new_evaluations,
                ) = self._evaluate_tick_daemon()
            else:
                new_run_requests, new_cursor, new_evaluations = self._evaluate_tick_fast()

        return dataclasses.replace(
            self,
            run_requests=new_run_requests,
            serialized_cursor=serialize_value(new_cursor),
            evaluations=new_evaluations,
            tick_index=self.tick_index + 1,
        )

    def _log_assertion_error(self, expected: Sequence[Any], actual: Sequence[Any]) -> None:
        expected_str = "\n\n".join("\t" + str(rr) for rr in expected)
        actual_str = "\n\n".join("\t" + str(rr) for rr in actual)
        message = f"\nExpected: \n\n{expected_str}\n\nActual: \n\n{actual_str}\n"
        self.logger.error(message)

    def get_sensor_origin(self):
        if not self.sensor_name:
            return None
        code_location_origin = get_code_location_origin(self.scenario_spec)
        return RemoteInstigatorOrigin(
            repository_origin=RemoteRepositoryOrigin(
                code_location_origin=code_location_origin,
                repository_name=SINGLETON_REPOSITORY_NAME,
            ),
            instigator_name=self.sensor_name,
        )

    def _assert_requested_runs_daemon(self, expected_run_requests: Sequence[RunRequest]) -> None:
        """Additional assertions for daemon mode. Checks that the most recent tick matches the
        expected requested asset partitions.
        """
        sensor_origin = self.get_sensor_origin()
        if sensor_origin:
            origin_id = sensor_origin.get_id()
            selector_id = sensor_origin.get_selector().get_id()
        else:
            origin_id = _PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID
            selector_id = _PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID

        latest_tick = sorted(
            self.instance.get_ticks(
                origin_id=origin_id,
                selector_id=selector_id,
            ),
            key=lambda tick: tick.tick_id,
        )[-1]

        expected_requested_asset_partitions = {
            AssetKeyPartitionKey(asset_key=ak, partition_key=rr.partition_key)
            for rr in expected_run_requests
            for ak in (rr.asset_selection or set())
        }
        assert (
            latest_tick.status == TickStatus.SUCCESS
            if len(expected_requested_asset_partitions) > 0
            else TickStatus.SKIPPED
        )

        assert latest_tick.requested_asset_materialization_count == len(
            expected_requested_asset_partitions
        )
        assert latest_tick.requested_asset_keys == {
            asset_partition.asset_key for asset_partition in expected_requested_asset_partitions
        }

    def assert_requested_runs(
        self, *expected_run_requests: RunRequest
    ) -> "AssetDaemonScenarioState":
        """Asserts that the set of runs requested by the previously-evaluated tick is identical to
        the set of runs specified in the expected_run_requests argument.
        """

        def sort_run_request_key_fn(run_request) -> Tuple[AssetKey, Optional[str]]:
            return (min(run_request.asset_selection), run_request.partition_key)

        sorted_run_requests = sorted(self.run_requests, key=sort_run_request_key_fn)
        sorted_expected_run_requests = sorted(expected_run_requests, key=sort_run_request_key_fn)

        try:
            assert len(sorted_run_requests) == len(sorted_expected_run_requests)
            for arr, err in zip(sorted_run_requests, sorted_expected_run_requests):
                assert set(arr.asset_selection or []) == set(err.asset_selection or [])
                assert arr.partition_key == err.partition_key
        except:
            self._log_assertion_error(sorted_expected_run_requests, sorted_run_requests)
            raise

        if self.is_daemon:
            self._assert_requested_runs_daemon(sorted_expected_run_requests)

        return self

    def _assert_evaluation_daemon(
        self, key: AssetKey, actual_evaluation: AutomationConditionEvaluation
    ) -> None:
        """Additional assertions for daemon mode. Checks that the evaluation for the given asset
        contains the expected run ids.
        """
        sensor_origin = self.get_sensor_origin()
        current_evaluation_id = check.not_none(
            get_current_evaluation_id(self.instance, sensor_origin)
        )
        new_run_ids_for_asset = {
            run.run_id
            for run in self.instance.get_runs(
                filters=RunsFilter(tags={"dagster/asset_evaluation_id": str(current_evaluation_id)})
            )
            if key in (run.asset_selection or set())
        }
        evaluation_record = next(
            iter(
                [
                    e
                    for e in check.not_none(
                        self.instance.schedule_storage
                    ).get_auto_materialize_evaluations_for_evaluation_id(current_evaluation_id)
                    if e.asset_key == key
                ]
            )
        )
        assert (
            new_run_ids_for_asset
            == evaluation_record.get_evaluation_with_run_ids(
                self.asset_graph.get(key).partitions_def
            ).run_ids
        )

    def assert_evaluation(
        self,
        key: CoercibleToAssetKey,
        expected_evaluation_specs: Sequence[AssetRuleEvaluationSpec],
        num_requested: Optional[int] = None,
    ) -> "AssetDaemonScenarioState":
        """Asserts that AutoMaterializeRuleEvaluations on the AutoMaterializeAssetEvaluation for the
        given asset key match the given expected_evaluation_specs.

        If num_requested, num_skipped, or num_discarded are specified, these values will also be
        checked against the actual evaluation.
        """
        asset_key = AssetKey.from_coercible(key)
        actual_evaluation = next((e for e in self.evaluations if e.asset_key == asset_key), None)

        if actual_evaluation is None:
            try:
                assert len(expected_evaluation_specs) == 0
                assert num_requested is None
            except:
                self.logger.error(
                    "\nAll Evaluations: \n\n" + "\n\n".join("\t" + str(e) for e in self.evaluations)
                )
                raise
            return self
        if num_requested is not None:
            assert actual_evaluation.true_subset.size == num_requested

        def get_leaf_evaluations(
            e: AutomationConditionEvaluation,
        ) -> Sequence[AutomationConditionEvaluation]:
            if len(e.child_evaluations) == 0:
                return [e]
            leaf_evals = []
            for child_eval in e.child_evaluations:
                leaf_evals.extend(get_leaf_evaluations(child_eval))
            return leaf_evals

        actual_subsets_with_metadata = list(
            itertools.chain(
                *[
                    leaf_eval.subsets_with_metadata
                    # backcompat as previously we stored None metadata for any true evaluation
                    or (
                        [AssetSubsetWithMetadata(subset=leaf_eval.true_subset, metadata={})]
                        if leaf_eval.true_subset.size
                        else []
                    )
                    for leaf_eval in get_leaf_evaluations(actual_evaluation)
                ]
            )
        )
        expected_subsets_with_metadata = [
            ees.resolve(asset_key, self.asset_graph) for ees in expected_evaluation_specs
        ]

        try:
            for actual_sm, expected_sm in zip(
                sorted(
                    actual_subsets_with_metadata,
                    key=lambda x: (frozenset(x.subset.asset_partitions), str(x.metadata)),
                ),
                sorted(
                    expected_subsets_with_metadata,
                    key=lambda x: (frozenset(x.subset.asset_partitions), str(x.metadata)),
                ),
            ):
                assert actual_sm.subset.asset_partitions == expected_sm.subset.asset_partitions
                # only check evaluation data if it was set on the expected evaluation spec
                if expected_sm.metadata:
                    assert actual_sm.metadata == expected_sm.metadata

        except:
            self._log_assertion_error(
                sorted(expected_subsets_with_metadata, key=lambda x: str(x)),
                sorted(actual_subsets_with_metadata, key=lambda x: str(x)),
            )
            raise

        if self.is_daemon:
            self._assert_evaluation_daemon(asset_key, actual_evaluation)

        return self


class AssetDaemonScenario(NamedTuple):
    """Describes a scenario that the AssetDaemon should be tested against. Consists of an id
    describing what is to be tested, an initial state, and a scenario function which will modify
    that state and make assertions about it along the way.
    """

    id: str
    initial_spec: ScenarioSpec
    execution_fn: Callable[[AssetDaemonScenarioState], AssetDaemonScenarioState]

    def evaluate_fast(self) -> None:
        self.execution_fn(AssetDaemonScenarioState(self.initial_spec))

    def evaluate_daemon(
        self, instance: DagsterInstance, sensor_name: Optional[str] = None, threadpool_executor=None
    ) -> "AssetDaemonScenarioState":
        return self.execution_fn(
            AssetDaemonScenarioState(
                self.initial_spec,
                instance=instance,
                is_daemon=True,
                sensor_name=sensor_name,
                threadpool_executor=threadpool_executor,
            )
        )
