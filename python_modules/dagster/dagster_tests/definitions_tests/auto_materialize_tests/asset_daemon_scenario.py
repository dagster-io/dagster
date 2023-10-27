import datetime
import hashlib
import logging
import os
import sys
from collections import namedtuple
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
)

import dagster._check as check
from dagster._core.definitions.executor_definition import in_process_executor
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
import pendulum
from dagster import (
    AssetKey,
    AssetsDefinition,
    AssetSpec,
    AutoMaterializePolicy,
    DagsterInstance,
    Definitions,
    RunRequest,
    asset,
)
from dagster._core.definitions import materialize
from dagster._core.definitions.asset_daemon_context import (
    AssetDaemonContext,
)
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.auto_materialize_rule import (
    AutoMaterializeAssetEvaluation,
    AutoMaterializeRule,
    AutoMaterializeRuleEvaluation,
    AutoMaterializeRuleEvaluationData,
)
from dagster._core.definitions.events import CoercibleToAssetKey
from dagster._core.definitions.executor_definition import in_process_executor
from dagster._core.host_representation.origin import InProcessCodeLocationOrigin
from dagster._core.storage.dagster_run import RunsFilter
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._core.test_utils import (
    InProcessTestWorkspaceLoadTarget,
    create_test_daemon_workspace_context,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
import hashlib
from dagster._daemon.asset_daemon import CURSOR_KEY, AssetDaemon

from .base_scenario import run_request


def get_code_location_origin(
    scenario_state: "AssetDaemonScenarioState", location_name=None
) -> InProcessCodeLocationOrigin:
    """Hacky method to allow us to point a code location at a module-scoped attribute, even though
    the attribute is not defined until the scenario is run.
    """
    attribute_name = (
        f"_asset_daemon_target_{hashlib.md5(str(scenario_state.asset_specs).encode()).hexdigest()}"
    )
    globals()[attribute_name] = Definitions(
        assets=scenario_state.assets, executor=in_process_executor
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

    def resolve(self) -> Tuple[AutoMaterializeRuleEvaluation, Optional[Sequence[str]]]:
        """Returns a tuple of the resolved AutoMaterializeRuleEvaluation for this spec and the
        partitions that it applies to.
        """
        return (
            AutoMaterializeRuleEvaluation(
                rule_snapshot=self.rule.to_snapshot(),
                evaluation_data=self.rule_evaluation_data,
            ),
            sorted(self.partitions) if self.partitions else None,
        )


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
    current_time: datetime.datetime = pendulum.now()
    run_requests: Sequence[RunRequest] = []
    cursor: AssetDaemonCursor = AssetDaemonCursor.empty()
    evaluations: Sequence[AutoMaterializeAssetEvaluation] = []
    logger: logging.Logger = logging.getLogger("dagster.amp")
    # this is set by the scenario runner
    scenario_instance: Optional[DagsterInstance] = None
    is_daemon: bool = False

    @property
    def instance(self) -> DagsterInstance:
        return check.not_none(self.scenario_instance)

    @property
    def assets(self) -> Sequence[AssetsDefinition]:
        def fn() -> None:
            ...

        assets = []
        params = {
            "key",
            "deps",
            "group_name",
            "code_version",
            "auto_materialize_policy",
            "partitions_def",
        }
        for spec in self.asset_specs:
            assets.append(
                asset(compute_fn=fn, **{k: v for k, v in spec._asdict().items() if k in params})
            )
        return assets

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
        with pendulum.test(self.current_time):
            for rr in run_requests:
                materialize(
                    assets=self.assets,
                    instance=self.instance,
                    partition_key=rr.partition_key,
                    tags=rr.tags,
                    raise_on_error=False,
                    selection=rr.asset_selection,
                )
        return self

    def with_requested_runs(self) -> "AssetDaemonScenarioState":
        return self.with_runs(*self.run_requests)

    def _evaluate_tick_fast(
        self,
    ) -> Tuple[Sequence[RunRequest], AssetDaemonCursor, Sequence[AutoMaterializeAssetEvaluation]]:
        return AssetDaemonContext(
            asset_graph=self.asset_graph,
            target_asset_keys=None,
            instance=self.instance,
            materialize_run_tags={},
            observe_run_tags={},
            cursor=self.cursor,
            auto_observe=True,
            respect_materialization_data_versions=False,
            logger=self.logger,
        ).evaluate()

    def _evaluate_tick_daemon(
        self,
    ) -> Tuple[Sequence[RunRequest], AssetDaemonCursor, Sequence[AutoMaterializeAssetEvaluation]]:
        target = InProcessTestWorkspaceLoadTarget(get_code_location_origin(self))

        with create_test_daemon_workspace_context(
            workspace_load_target=target, instance=self.instance
        ) as workspace_context:
            workspace = workspace_context.create_request_context()
            assert (
                workspace.get_code_location_error("test_location") is None
            ), workspace.get_code_location_error("test_location")

            list(
                AssetDaemon(interval_seconds=42)._run_iteration_impl(  # noqa: SLF001
                    workspace_context,
                    {},
                )
            )
            new_cursor = AssetDaemonCursor.from_serialized(
                check.not_none(
                    self.instance.daemon_cursor_storage.get_cursor_values({CURSOR_KEY}).get(
                        CURSOR_KEY
                    )
                ),
                self.asset_graph,
            )
            new_run_requests = [
                run_request(
                    list(run.asset_selection or []), partition_key=run.tags.get(PARTITION_NAME_TAG)
                )
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
        with pendulum.test(self.current_time):
            if self.is_daemon:
                new_run_requests, new_cursor, new_evaluations = self._evaluate_tick_daemon()
            else:
                new_run_requests, new_cursor, new_evaluations = self._evaluate_tick_fast()

        return self._replace(
            run_requests=new_run_requests,
            cursor=new_cursor,
            evaluations=new_evaluations,
        )

    def _log_assertion_error(self, expected: Sequence[Any], actual: Sequence[Any]) -> None:
        expected_str = "\n\n".join("\t" + str(rr) for rr in expected)
        actual_str = "\n\n".join("\t" + str(rr) for rr in actual)
        message = f"\nExpected: \n\n{expected_str}\n\nActual: \n\n{actual_str}\n"
        self.logger.error(message)

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

        return self

    def assert_evaluation(
        self,
        key: CoercibleToAssetKey,
        expected_evaluation_specs: Sequence[AssetRuleEvaluationSpec],
        num_requested: Optional[int] = None,
        num_skipped: Optional[int] = None,
        num_discarded: Optional[int] = None,
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
                assert all(n is None for n in (num_requested, num_skipped, num_discarded))
            except:
                self.logger.error(
                    "\nAll Evaluations: \n\n" + "\n\n".join("\t" + str(e) for e in self.evaluations)
                )
                raise
            return self
        if num_requested is not None:
            assert actual_evaluation.num_requested == num_requested
        if num_skipped is not None:
            assert actual_evaluation.num_skipped == num_skipped
        if num_discarded is not None:
            assert actual_evaluation.num_discarded == num_discarded

        # unpack the serialized partition subsets into an easier format
        actual_rule_evaluations = [
            (
                rule_evaluation,
                sorted(
                    serialized_subset.deserialize(
                        check.not_none(self.asset_graph.get_partitions_def(asset_key))
                    ).get_partition_keys()
                )
                if serialized_subset is not None
                else None,
            )
            for rule_evaluation, serialized_subset in actual_evaluation.partition_subsets_by_condition
        ]
        expected_rule_evaluations = [ees.resolve() for ees in expected_evaluation_specs]

        try:
            for (actual_data, actual_partitions), (expected_data, expected_partitions) in zip(
                sorted(actual_rule_evaluations), sorted(expected_rule_evaluations)
            ):
                assert actual_data.rule_snapshot == expected_data.rule_snapshot
                assert actual_partitions == expected_partitions
                # only check evaluation data if it was set on the expected evaluation spec
                if expected_data.evaluation_data is not None:
                    assert actual_data.evaluation_data == expected_data.evaluation_data

        except:
            self._log_assertion_error(
                sorted(expected_rule_evaluations), sorted(actual_rule_evaluations)
            )
            raise

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

    def evaluate_daemon(self, instance: DagsterInstance) -> None:
        self.initial_state.logger.setLevel(logging.DEBUG)
        self.execution_fn(self.initial_state._replace(scenario_instance=instance, is_daemon=True))
