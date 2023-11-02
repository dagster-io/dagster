from abc import ABC, abstractmethod
from typing import AbstractSet, Mapping, NamedTuple, Optional, Tuple

from dagster._core.definitions.auto_materialize_rule import (
    AutoMaterializeAssetEvaluation,
    AutoMaterializeRule,
    RuleEvaluationContext,
)
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey


class AutoExecutionEvaluationData(NamedTuple):
    """TODO: a place to put more data about why something evaluated as true or false."""

    result: bool


class AutoExecutionEvaluationResult(NamedTuple):
    """A recursive data structure to store the results of evaluating an AutoExecutionPolicy."""

    true_candidates: AbstractSet[AssetKeyPartitionKey]
    false_candidates: AbstractSet[AssetKeyPartitionKey]
    evaluated_candidates: AbstractSet[AssetKeyPartitionKey]
    candidate_by_evaluation_data: Optional[
        Mapping[Optional[AutoExecutionEvaluationData], AbstractSet[AssetKeyPartitionKey]]
    ]
    sub_results: Optional[Mapping["AutoExecutionPolicy", Optional["AutoExecutionEvaluationResult"]]]

    def to_retval(
        self, asset_key: AssetKey
    ) -> Tuple[
        AutoMaterializeAssetEvaluation,
        AbstractSet[AssetKeyPartitionKey],
        AbstractSet[AssetKeyPartitionKey],
    ]:
        """Method to reshape this object into something the existing machinery understands. This
        would not be necessary in the final version of this stack.
        """
        return AutoMaterializeAssetEvaluation(
            asset_key=asset_key,
            partition_subsets_by_condition=[],
            num_requested=len(self.true_candidates),
            num_skipped=len(self.false_candidates),
            num_discarded=0,
        ), self.true_candidates, self.false_candidates


AutoExecutionEvaluationContext = RuleEvaluationContext


class AutoExecutionPolicy(ABC):
    """A policy has a single evaluate method that takes a context and returns a result containing
    information about what candidate asset partitions its rules apply to.
    """

    @abstractmethod
    def evaluate(self, context: "AutoExecutionEvaluationContext") -> AutoExecutionEvaluationResult:
        ...

    def __or__(self, other: "AutoExecutionPolicy") -> "OrAutoExecutionPolicy":
        return OrAutoExecutionPolicy(left=self, right=other)

    def __and__(self, other: "AutoExecutionPolicy") -> "AndAutoExecutionPolicy":
        return AndAutoExecutionPolicy(left=self, right=other)

    def __invert__(self) -> "NotAutoExecutionPolicy":
        return NotAutoExecutionPolicy(self)

    @staticmethod
    def parent_updated() -> "AutoExecutionPolicy":
        return RuleAutoExecutionPolicy(AutoMaterializeRule.materialize_on_parent_updated())

    @staticmethod
    def parent_missing() -> "AutoExecutionPolicy":
        return RuleAutoExecutionPolicy(AutoMaterializeRule.skip_on_parent_missing())

    @staticmethod
    def materialized_since_cron(
        cron_schedule: str, timezone: str = "UTC", all_partitions: bool = False
    ) -> "AutoExecutionPolicy":
        # the underlying rule returns true if the asset has NOT been materialized since the cron
        # schedule tick, so we need to invert the results
        return ~RuleAutoExecutionPolicy(
            AutoMaterializeRule.materialize_on_cron(
                cron_schedule=cron_schedule,
                timezone=timezone,
                all_partitions=all_partitions,
            )
        )


class OrAutoExecutionPolicy(
    AutoExecutionPolicy,
    NamedTuple(
        "_OrAutoExecutionPolicy",
        [("left", AutoExecutionPolicy), ("right", AutoExecutionPolicy)],
    ),
):
    def evaluate(self, context: "AutoExecutionEvaluationContext") -> AutoExecutionEvaluationResult:
        left_result = self.left.evaluate(context)
        # only need to evaluate the false candidates
        right_result = self.right.evaluate(context.with_candidates(left_result.false_candidates))
        return AutoExecutionEvaluationResult(
            true_candidates=left_result.true_candidates | right_result.true_candidates,
            false_candidates=left_result.false_candidates & right_result.false_candidates,
            evaluated_candidates=context.candidates,
            candidate_by_evaluation_data={},
            sub_results={self.left: left_result, self.right: right_result},
        )


class AndAutoExecutionPolicy(
    AutoExecutionPolicy,
    NamedTuple(
        "_AndAutoExecutionPolicy",
        [("left", AutoExecutionPolicy), ("right", AutoExecutionPolicy)],
    ),
):
    def evaluate(self, context: "AutoExecutionEvaluationContext") -> AutoExecutionEvaluationResult:
        left_result = self.left.evaluate(context)
        # only need to evaluate the true candidates
        right_result = self.right.evaluate(context.with_candidates(left_result.true_candidates))
        return AutoExecutionEvaluationResult(
            true_candidates=left_result.true_candidates & right_result.true_candidates,
            false_candidates=left_result.false_candidates | right_result.false_candidates,
            evaluated_candidates=context.candidates,
            candidate_by_evaluation_data={},
            sub_results={self.left: left_result, self.right: right_result},
        )


class NotAutoExecutionPolicy(
    AutoExecutionPolicy,
    NamedTuple(
        "_NotAutoExecutionPolicy",
        [("child", AutoExecutionPolicy)],
    ),
):
    def evaluate(self, context: "AutoExecutionEvaluationContext") -> AutoExecutionEvaluationResult:
        child_result = self.child.evaluate(context)
        return AutoExecutionEvaluationResult(
            true_candidates=child_result.false_candidates,
            false_candidates=child_result.true_candidates,
            evaluated_candidates=context.candidates,
            candidate_by_evaluation_data={},
            sub_results={self.child: child_result},
        )


class RuleAutoExecutionPolicy(
    AutoExecutionPolicy,
    NamedTuple(
        "_RuleAutoExecutionPolicy",
        [("rule", AutoMaterializeRule)],
    ),
):
    def evaluate(self, context: "AutoExecutionEvaluationContext") -> AutoExecutionEvaluationResult:
        result = self.rule.evaluate_for_asset(context=context)
        true_candidates = set().union(*[subset for _, subset in result])
        return AutoExecutionEvaluationResult(
            true_candidates=true_candidates,
            false_candidates=context.candidates - true_candidates,
            evaluated_candidates=context.candidates,
            candidate_by_evaluation_data={},
            sub_results=None,
        )
