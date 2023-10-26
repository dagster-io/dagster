import datetime
import logging
from typing import (
    Any,
    Callable,
    Iterable,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Type,
)

import dagster._check as check
import pendulum
from dagster import (
    AssetKey,
    AssetsDefinition,
    AssetSpec,
    AutoMaterializePolicy,
    DagsterInstance,
    RunRequest,
    asset,
)
from dagster._core.definitions import materialize
from dagster._core.definitions.asset_daemon_context import AssetDaemonContext
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.auto_materialize_rule import (
    AutoMaterializeAssetEvaluation,
    AutoMaterializeRule,
    AutoMaterializeRuleEvaluation,
    AutoMaterializeRuleEvaluationData,
)
from dagster._core.definitions.events import CoercibleToAssetKey


class AssetRuleEvaluationSpec(NamedTuple):
    rule: AutoMaterializeRule
    partitions: Optional[Sequence[str]] = None
    rule_evaluation_data: Optional[AutoMaterializeRuleEvaluationData] = None

    def with_rule_evaluation_data(
        self, data_type: Type[AutoMaterializeRuleEvaluationData], **kwargs
    ) -> "AssetRuleEvaluationSpec":
        # convert sets of CoercibleToAssetKey to frozensets of AssetKey (for convenience)
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
        return (
            AutoMaterializeRuleEvaluation(
                rule_snapshot=self.rule.to_snapshot(),
                evaluation_data=self.rule_evaluation_data,
            ),
            self.partitions,
        )


class AssetDaemonScenarioState(NamedTuple):
    asset_specs: Sequence[AssetSpec]
    current_time: datetime.datetime = pendulum.now()
    run_requests: Sequence[RunRequest] = []
    cursor: AssetDaemonCursor = AssetDaemonCursor.empty()
    evaluations: Sequence[AutoMaterializeAssetEvaluation] = []
    logger: logging.Logger = logging.getLogger("dagster.amp")
    internal_instance: Optional[DagsterInstance] = None

    @property
    def instance(self) -> DagsterInstance:
        return check.not_none(self.internal_instance)

    @property
    def assets(self) -> Sequence[AssetsDefinition]:
        def fn() -> None:
            ...

        assets = []
        params = {"key", "deps", "group_name", "code_version", "auto_materialize_policy"}
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
                new_asset_specs.append(spec._replace(**kwargs))
            else:
                new_asset_specs.append(spec)
        return self._replace(asset_specs=new_asset_specs)

    def with_all_eager(self) -> "AssetDaemonScenarioState":
        return self.with_asset_properties(auto_materialize_policy=AutoMaterializePolicy.eager())

    def with_current_time(self, time: str) -> "AssetDaemonScenarioState":
        return self._replace(current_time=pendulum.parse(time))

    def with_runs(self, *run_requests: RunRequest) -> "AssetDaemonScenarioState":
        with pendulum.test(self.current_time):
            for run_request in run_requests:
                materialize(
                    assets=self.assets,
                    instance=self.instance,
                    partition_key=run_request.partition_key,
                    tags=run_request.tags,
                    raise_on_error=False,
                    selection=run_request.asset_selection,
                )
        return self

    def add_requested_runs(self) -> "AssetDaemonScenarioState":
        return self.with_runs(*self.run_requests)

    def evaluate_tick(self) -> "AssetDaemonScenarioState":
        with pendulum.test(self.current_time):
            new_run_requests, new_cursor, new_evaluations = AssetDaemonContext(
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
        """Makes an assertion about the evaluation data associated with a specific asset."""
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
            for (ared, aps), (ered, eps) in zip(
                sorted(actual_rule_evaluations), sorted(expected_rule_evaluations)
            ):
                assert ared.rule_snapshot == ered.rule_snapshot
                assert aps == eps
                # only check evaluation data if it was set on the expected evaluation spec
                if ered.evaluation_data is not None:
                    assert ared.evaluation_data == ered.evaluation_data

        except:
            self._log_assertion_error(
                sorted(expected_rule_evaluations), sorted(actual_rule_evaluations)
            )
            raise

        return self


class AssetDaemonScenario(NamedTuple):
    id: str
    initial_state: AssetDaemonScenarioState
    scenario: Callable[[AssetDaemonScenarioState], AssetDaemonScenarioState]

    def evaluate(self) -> None:
        self.initial_state.logger.setLevel(logging.DEBUG)
        self.scenario(self.initial_state._replace(internal_instance=DagsterInstance.ephemeral()))
