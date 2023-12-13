import datetime
import hashlib
import itertools
import json
import logging
import os
import sys
import threading
from collections import namedtuple
from contextlib import contextmanager
from typing import (
    Any,
    Callable,
    Iterable,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)

import dagster._check as check
import mock
import pendulum
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetsDefinition,
    AssetSpec,
    AutoMaterializePolicy,
    DagsterInstance,
    DagsterRunStatus,
    Definitions,
    MultiPartitionKey,
    RunRequest,
    RunsFilter,
    asset,
    materialize,
)
from dagster._core.definitions.asset_condition import (
    AssetConditionEvaluation,
    AssetSubsetWithMetadata,
)
from dagster._core.definitions.asset_daemon_context import (
    AssetDaemonContext,
)
from dagster._core.definitions.asset_daemon_cursor import (
    AssetDaemonCursor,
    LegacyAssetDaemonCursorWrapper,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule
from dagster._core.definitions.auto_materialize_rule_evaluation import (
    AutoMaterializeRuleEvaluationData,
)
from dagster._core.definitions.automation_policy_sensor_definition import (
    AutomationPolicySensorDefinition,
)
from dagster._core.definitions.events import AssetKeyPartitionKey, CoercibleToAssetKey
from dagster._core.definitions.executor_definition import in_process_executor
from dagster._core.definitions.repository_definition.valid_definitions import (
    SINGLETON_REPOSITORY_NAME,
)
from dagster._core.host_representation.origin import (
    ExternalInstigatorOrigin,
    ExternalRepositoryOrigin,
    InProcessCodeLocationOrigin,
)
from dagster._core.scheduler.instigation import (
    SensorInstigatorData,
    TickStatus,
)
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._core.test_utils import (
    InProcessTestWorkspaceLoadTarget,
    create_test_daemon_workspace_context,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._daemon.asset_daemon import (
    _PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
    _PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
    AssetDaemon,
    _get_pre_sensor_auto_materialize_serialized_cursor,
    get_current_evaluation_id,
)

from .base_scenario import FAIL_TAG, run_request


def get_code_location_origin(
    scenario_state: "AssetDaemonScenarioState", location_name=None
) -> InProcessCodeLocationOrigin:
    """Hacky method to allow us to point a code location at a module-scoped attribute, even though
    the attribute is not defined until the scenario is run.
    """
    attribute_name = (
        f"_asset_daemon_target_{hashlib.md5(str(scenario_state.asset_specs).encode()).hexdigest()}"
    )
    if attribute_name not in globals():
        globals()[attribute_name] = Definitions(
            assets=scenario_state.assets,
            executor=in_process_executor,
            sensors=scenario_state.automation_policy_sensors,
        )

    return InProcessCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            module_name=(
                "dagster_tests.definitions_tests.auto_materialize_tests.asset_daemon_scenario"
            ),
            working_directory=os.getcwd(),
            attribute=attribute_name,
        ),
        location_name=location_name or "test_location",
    )


def day_partition_key(time: datetime.datetime, delta: int = 0) -> str:
    """Returns the partition key of a day partition delta days from the initial time."""
    return (time + datetime.timedelta(days=delta - 1)).strftime("%Y-%m-%d")


def hour_partition_key(time: datetime.datetime, delta: int = 0) -> str:
    """Returns the partition key of a day partition delta days from the initial time."""
    return (time + datetime.timedelta(hours=delta - 1)).strftime("%Y-%m-%d-%H:00")


def multi_partition_key(**kwargs) -> MultiPartitionKey:
    """Returns a MultiPartitionKey based off of the given kwargs."""
    return MultiPartitionKey(kwargs)


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

    def resolve(self, asset_key: AssetKey, asset_graph: AssetGraph) -> AssetSubsetWithMetadata:
        """Returns a tuple of the resolved AutoMaterializeRuleEvaluation for this spec and the
        partitions that it applies to.
        """
        subset = AssetSubset.from_asset_partitions_set(
            asset_key,
            asset_graph.get_partitions_def(asset_key),
            {
                AssetKeyPartitionKey(asset_key, partition_key)
                for partition_key in self.partitions or [None]
            },
        )
        metadata = self.rule_evaluation_data.metadata if self.rule_evaluation_data else {}
        return AssetSubsetWithMetadata(subset=subset, metadata=metadata)


class AssetSpecWithPartitionsDef(
    namedtuple(
        "AssetSpecWithPartitionsDef",
        AssetSpec._fields + ("partitions_def",),
        defaults=(None,) * (1 + len(AssetSpec._fields)),
    )
):
    ...


class AssetDaemonScenarioState(NamedTuple):
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

    asset_specs: Sequence[Union[AssetSpec, AssetSpecWithPartitionsDef]]
    current_time: datetime.datetime = pendulum.now("UTC")
    run_requests: Sequence[RunRequest] = []
    serialized_cursor: str = AssetDaemonCursor.empty().serialize()
    evaluations: Sequence[AssetConditionEvaluation] = []
    logger: logging.Logger = logging.getLogger("dagster.amp")
    tick_index: int = 1
    # this is set by the scenario runner
    scenario_instance: Optional[DagsterInstance] = None
    is_daemon: bool = False
    sensor_name: Optional[str] = None
    automation_policy_sensors: Optional[Sequence[AutomationPolicySensorDefinition]] = None

    @property
    def instance(self) -> DagsterInstance:
        return check.not_none(self.scenario_instance)

    @property
    def assets(self) -> Sequence[AssetsDefinition]:
        def compute_fn(context: AssetExecutionContext) -> None:
            fail_keys = {
                AssetKey.from_coercible(s)
                for s in json.loads(context.run.tags.get(FAIL_TAG) or "[]")
            }
            if context.asset_key in fail_keys:
                raise Exception("Asset failed")

        assets = []
        params = {
            "key",
            "deps",
            "group_name",
            "code_version",
            "auto_materialize_policy",
            "freshness_policy",
            "partitions_def",
        }
        for spec in self.asset_specs:
            assets.append(
                asset(
                    compute_fn=compute_fn,
                    **{k: v for k, v in spec._asdict().items() if k in params},
                )
            )
        return assets

    @property
    def defs(self) -> Definitions:
        return Definitions(assets=self.assets, sensors=self.automation_policy_sensors)

    @property
    def asset_graph(self) -> AssetGraph:
        return AssetGraph.from_assets(self.assets)

    def with_asset_properties(
        self, keys: Optional[Iterable[CoercibleToAssetKey]] = None, **kwargs
    ) -> "AssetDaemonScenarioState":
        """Convenience method to update the properties of one or more assets in the scenario state."""
        new_asset_specs = []
        for spec in self.asset_specs:
            if keys is None or spec.key in {AssetKey.from_coercible(key) for key in keys}:
                if "partitions_def" in kwargs:
                    # partitions_def is not a field on AssetSpec, so we need to do this hack
                    new_asset_specs.append(
                        AssetSpecWithPartitionsDef(**{**spec._asdict(), **kwargs})
                    )
                else:
                    new_asset_specs.append(spec._replace(**kwargs))
            else:
                new_asset_specs.append(spec)
        return self._replace(asset_specs=new_asset_specs)

    def with_automation_policy_sensors(
        self,
        sensors: Optional[Sequence[AutomationPolicySensorDefinition]],
    ):
        return self._replace(automation_policy_sensors=sensors)

    def with_all_eager(
        self, max_materializations_per_minute: int = 1
    ) -> "AssetDaemonScenarioState":
        return self.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.eager(
                max_materializations_per_minute=max_materializations_per_minute
            )
        )

    def with_current_time(self, time: str) -> "AssetDaemonScenarioState":
        return self._replace(current_time=pendulum.parse(time))

    def with_current_time_advanced(self, **kwargs) -> "AssetDaemonScenarioState":
        # hacky support for adding years
        if "years" in kwargs:
            kwargs["days"] = kwargs.get("days", 0) + 365 * kwargs.pop("years")
        return self._replace(current_time=self.current_time + datetime.timedelta(**kwargs))

    def with_runs(self, *run_requests: RunRequest) -> "AssetDaemonScenarioState":
        start = datetime.datetime.now()

        def test_time_fn() -> float:
            # this function will increment the current timestamp in real time, relative to the
            # fake current_time on the scenario state
            return (self.current_time + (datetime.datetime.now() - start)).timestamp()

        with pendulum.test(self.current_time), mock.patch("time.time", new=test_time_fn):
            for rr in run_requests:
                materialize(
                    assets=self.assets,
                    instance=self.instance,
                    partition_key=rr.partition_key,
                    tags=rr.tags,
                    raise_on_error=False,
                    selection=rr.asset_selection,
                )
        # increment current_time by however much time elapsed during the materialize call
        return self._replace(current_time=pendulum.from_timestamp(test_time_fn()))

    def with_not_started_runs(self) -> "AssetDaemonScenarioState":
        """Execute all runs in the NOT_STARTED state and delete them from the instance. The scenario
        adds in the run requests from previous ticks as runs in the NOT_STARTED state, so this method
        executes requested runs from previous ticks.
        """
        not_started_runs = self.instance.get_runs(
            filters=RunsFilter(statuses=[DagsterRunStatus.NOT_STARTED])
        )
        for run in not_started_runs:
            self.instance.delete_run(run_id=run.run_id)
        return self.with_runs(
            *[
                run_request(
                    asset_keys=list(run.asset_selection or set()),
                    partition_key=run.tags.get(PARTITION_NAME_TAG),
                )
                for run in not_started_runs
            ]
        )

    def with_dynamic_partitions(
        self, partitions_def_name: str, partition_keys: Sequence[str]
    ) -> "AssetDaemonScenarioState":
        self.instance.add_dynamic_partitions(
            partitions_def_name=partitions_def_name, partition_keys=partition_keys
        )
        return self

    def _evaluate_tick_fast(
        self,
    ) -> Tuple[Sequence[RunRequest], AssetDaemonCursor, Sequence[AssetConditionEvaluation]]:
        cursor = AssetDaemonCursor.from_serialized(self.serialized_cursor, self.asset_graph)

        new_run_requests, new_cursor, new_evaluations = AssetDaemonContext(
            evaluation_id=cursor.evaluation_id + 1,
            asset_graph=self.asset_graph,
            auto_materialize_asset_keys={
                key
                for key, policy in self.asset_graph.auto_materialize_policies_by_key.items()
                if policy is not None
            },
            instance=self.instance,
            materialize_run_tags={},
            observe_run_tags={},
            cursor=cursor,
            auto_observe_asset_keys={
                key
                for key in self.asset_graph.source_asset_keys
                if self.asset_graph.get_auto_observe_interval_minutes(key) is not None
            },
            respect_materialization_data_versions=False,
            logger=self.logger,
        ).evaluate()

        # make sure these run requests are available on the instance
        for request in new_run_requests:
            asset_selection = check.not_none(request.asset_selection)
            job_def = self.defs.get_implicit_job_def_for_assets(asset_selection)
            self.instance.create_run_for_job(
                job_def=check.not_none(job_def),
                asset_selection=set(asset_selection),
                tags=request.tags,
            )
        return new_run_requests, new_cursor, new_evaluations

    @contextmanager
    def _create_workspace_context(self):
        target = InProcessTestWorkspaceLoadTarget(get_code_location_origin(self))
        with create_test_daemon_workspace_context(
            workspace_load_target=target, instance=self.instance
        ) as workspace_context:
            yield workspace_context

    @contextmanager
    def _get_external_sensor(self, sensor_name):
        with self._create_workspace_context() as workspace_context:
            workspace = workspace_context.create_request_context()
            sensor = next(
                iter(workspace.get_code_location("test_location").get_repositories().values())
            ).get_external_sensor(sensor_name)
            assert sensor
            yield sensor

    def start_sensor(self, sensor_name: str):
        with self._get_external_sensor(sensor_name) as sensor:
            self.instance.start_sensor(sensor)
        return self

    def stop_sensor(self, sensor_name: str):
        with self._get_external_sensor(sensor_name) as sensor:
            self.instance.stop_sensor(sensor.get_external_origin_id(), sensor.selector_id, sensor)
        return self

    def _evaluate_tick_daemon(
        self,
    ) -> Tuple[
        Sequence[RunRequest],
        AssetDaemonCursor,
        Sequence[AssetConditionEvaluation],
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

            list(
                AssetDaemon(  # noqa: SLF001
                    pre_sensor_interval_seconds=42
                )._run_iteration_impl(
                    workspace_context,
                    debug_crash_flags={},
                    sensor_state_lock=threading.Lock(),
                )
            )

            if sensor:
                auto_materialize_instigator_state = check.not_none(
                    self.instance.get_instigator_state(
                        sensor.get_external_origin_id(), sensor.selector_id
                    )
                )
                compressed_cursor = (
                    cast(
                        SensorInstigatorData,
                        check.not_none(auto_materialize_instigator_state).instigator_data,
                    ).cursor
                    or AssetDaemonCursor.empty().serialize()
                )
                new_cursor = (
                    LegacyAssetDaemonCursorWrapper.from_compressed(
                        compressed_cursor
                    ).get_asset_daemon_cursor(self.asset_graph)
                    if compressed_cursor
                    else AssetDaemonCursor.empty()
                )
            else:
                raw_cursor = _get_pre_sensor_auto_materialize_serialized_cursor(self.instance)
                new_cursor = (
                    AssetDaemonCursor.from_serialized(
                        raw_cursor,
                        self.asset_graph,
                    )
                    if raw_cursor
                    else AssetDaemonCursor.empty()
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
            new_evaluations = [
                e.evaluation
                for e in check.not_none(
                    self.instance.schedule_storage
                ).get_auto_materialize_evaluations_for_evaluation_id(new_cursor.evaluation_id)
            ]
        return new_run_requests, new_cursor, new_evaluations

    def evaluate_tick(self) -> "AssetDaemonScenarioState":
        self.logger.critical("********************************")
        self.logger.critical(f"EVALUATING TICK {self.tick_index}")
        self.logger.critical("********************************")
        with pendulum.test(self.current_time):
            if self.is_daemon:
                (
                    new_run_requests,
                    new_cursor,
                    new_evaluations,
                ) = self._evaluate_tick_daemon()
            else:
                new_run_requests, new_cursor, new_evaluations = self._evaluate_tick_fast()

        return self._replace(
            run_requests=new_run_requests,
            serialized_cursor=new_cursor.serialize(),
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
        code_location_origin = get_code_location_origin(self)
        return ExternalInstigatorOrigin(
            external_repository_origin=ExternalRepositoryOrigin(
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
        self, key: AssetKey, actual_evaluation: AssetConditionEvaluation
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
        evaluation_with_run_ids = next(
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
        assert new_run_ids_for_asset == evaluation_with_run_ids.run_ids

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

        def get_leaf_evaluations(e: AssetConditionEvaluation) -> Sequence[AssetConditionEvaluation]:
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
                        [AssetSubsetWithMetadata(leaf_eval.true_subset, {})]
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
                sorted(actual_subsets_with_metadata, key=lambda x: str(x)),
                sorted(expected_subsets_with_metadata, key=lambda x: str(x)),
            ):
                assert actual_sm.subset == expected_sm.subset
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
    initial_state: AssetDaemonScenarioState
    execution_fn: Callable[[AssetDaemonScenarioState], AssetDaemonScenarioState]

    def evaluate_fast(self) -> None:
        self.initial_state.logger.setLevel(logging.DEBUG)
        self.execution_fn(
            self.initial_state._replace(scenario_instance=DagsterInstance.ephemeral())
        )

    def evaluate_daemon(
        self, instance: DagsterInstance, sensor_name: Optional[str] = None
    ) -> "AssetDaemonScenarioState":
        self.initial_state.logger.setLevel(logging.DEBUG)
        return self.execution_fn(
            self.initial_state._replace(
                scenario_instance=instance, is_daemon=True, sensor_name=sensor_name
            )
        )
