from abc import ABC
from enum import Enum
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    FrozenSet,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    cast,
)

import dagster._check as check
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._serdes.serdes import (
    NamedTupleSerializer,
    UnpackContext,
    UnpackedValue,
    WhitelistMap,
    whitelist_for_serdes,
)

from .asset_graph import AssetGraph
from .partition import SerializedPartitionsSubset

if TYPE_CHECKING:
    from dagster._core.instance import DynamicPartitionsStore


@whitelist_for_serdes
class AutoMaterializeDecisionType(Enum):
    """Represents the set of results of the auto-materialize logic.

    MATERIALIZE: The asset should be materialized by a run kicked off on this tick
    SKIP: The asset should not be materialized by a run kicked off on this tick, because future
        ticks are expected to materialize it.
    DISCARD: The asset should not be materialized by a run kicked off on this tick, but future
        ticks are not expected to materialize it.
    """

    MATERIALIZE = "MATERIALIZE"
    SKIP = "SKIP"
    DISCARD = "DISCARD"


@whitelist_for_serdes
class AutoMaterializeRuleSnapshot(NamedTuple):
    """A serializable snapshot of an AutoMaterializeRule for historical evaluations."""

    class_name: str
    description: str
    decision_type: AutoMaterializeDecisionType


class AutoMaterializeRuleEvaluationData(ABC):
    pass


@whitelist_for_serdes
class TextRuleEvaluationData(
    AutoMaterializeRuleEvaluationData,
    NamedTuple("_TextRuleEvaluationData", [("text", str)]),
):
    pass


@whitelist_for_serdes
class ParentUpdatedRuleEvaluationData(
    AutoMaterializeRuleEvaluationData,
    NamedTuple(
        "_ParentUpdatedRuleEvaluationData",
        [
            ("updated_asset_keys", FrozenSet[AssetKey]),
            ("will_update_asset_keys", FrozenSet[AssetKey]),
        ],
    ),
):
    pass


@whitelist_for_serdes
class WaitingOnAssetsRuleEvaluationData(
    AutoMaterializeRuleEvaluationData,
    NamedTuple(
        "_WaitingOnParentRuleEvaluationData",
        [("waiting_on_asset_keys", FrozenSet[AssetKey])],
    ),
):
    pass


RuleEvaluationResults = Sequence[Tuple[Optional[AutoMaterializeRuleEvaluationData], AbstractSet]]


@whitelist_for_serdes
class AutoMaterializeRuleEvaluation(NamedTuple):
    rule_snapshot: AutoMaterializeRuleSnapshot
    evaluation_data: Optional[AutoMaterializeRuleEvaluationData]


@whitelist_for_serdes
class AutoMaterializeAssetEvaluation(NamedTuple):
    """Represents the results of the auto-materialize logic for a single asset.

    Properties:
        asset_key (AssetKey): The asset key that was evaluated.
        partition_subsets_by_condition: The rule evaluations that impact if the asset should be
            materialized, skipped, or discarded. If the asset is partitioned, this will be a list of
            tuples, where the first element is the condition and the second element is the
            serialized subset of partitions that the condition applies to. If it's not partitioned,
            the second element will be None.
        num_requested (int): The number of asset partitions that were requested to be materialized
        num_skipped (int): The number of asset partitions that were skipped
        num_discarded (int): The number of asset partitions that were discarded
        run_ids (Set[str]): The set of run IDs created for this evaluation
        rule_snapshots (Optional[Sequence[AutoMaterializeRuleSnapshot]]): The snapshots of the
            rules on the policy at the time it was evaluated.
    """

    asset_key: AssetKey
    partition_subsets_by_condition: Sequence[
        Tuple["AutoMaterializeRuleEvaluation", Optional[SerializedPartitionsSubset]]
    ]
    num_requested: int
    num_skipped: int
    num_discarded: int
    run_ids: Set[str] = set()
    rule_snapshots: Optional[Sequence[AutoMaterializeRuleSnapshot]] = None

    @property
    def is_empty(self) -> bool:
        return (
            sum([self.num_requested, self.num_skipped, self.num_discarded]) == 0
            and len(self.partition_subsets_by_condition) == 0
        )

    @staticmethod
    def from_rule_evaluation_results(
        asset_graph: AssetGraph,
        asset_key: AssetKey,
        asset_partitions_by_rule_evaluation: Sequence[
            Tuple[AutoMaterializeRuleEvaluation, AbstractSet[AssetKeyPartitionKey]]
        ],
        num_requested: int,
        num_skipped: int,
        num_discarded: int,
        dynamic_partitions_store: "DynamicPartitionsStore",
    ) -> "AutoMaterializeAssetEvaluation":
        auto_materialize_policy = asset_graph.auto_materialize_policies_by_key.get(asset_key)

        if not auto_materialize_policy:
            check.failed(f"Expected auto materialize policy on asset {asset_key}")

        partitions_def = asset_graph.get_partitions_def(asset_key)
        if partitions_def is None:
            return AutoMaterializeAssetEvaluation(
                asset_key=asset_key,
                partition_subsets_by_condition=[
                    (rule_evaluation, None)
                    for rule_evaluation, _ in asset_partitions_by_rule_evaluation
                ],
                num_requested=num_requested,
                num_skipped=num_skipped,
                num_discarded=num_discarded,
                rule_snapshots=auto_materialize_policy.rule_snapshots,
            )
        else:
            return AutoMaterializeAssetEvaluation(
                asset_key=asset_key,
                partition_subsets_by_condition=[
                    (
                        rule_evaluation,
                        SerializedPartitionsSubset.from_subset(
                            subset=partitions_def.empty_subset().with_partition_keys(
                                check.not_none(ap.partition_key) for ap in asset_partitions
                            ),
                            partitions_def=partitions_def,
                            dynamic_partitions_store=dynamic_partitions_store,
                        ),
                    )
                    for rule_evaluation, asset_partitions in asset_partitions_by_rule_evaluation
                ],
                num_requested=num_requested,
                num_skipped=num_skipped,
                num_discarded=num_discarded,
                rule_snapshots=auto_materialize_policy.rule_snapshots,
            )

    def _deserialize_rule_evaluation_result(
        self,
        rule_evaluation: AutoMaterializeRuleEvaluation,
        serialized_subset: Optional[SerializedPartitionsSubset],
        asset_graph: AssetGraph,
    ) -> Optional[
        Tuple[Optional[AutoMaterializeRuleEvaluationData], AbstractSet[AssetKeyPartitionKey]]
    ]:
        partitions_def = asset_graph.get_partitions_def(self.asset_key)
        if serialized_subset is None:
            if partitions_def is None:
                return (rule_evaluation.evaluation_data, {AssetKeyPartitionKey(self.asset_key)})
        elif serialized_subset.can_deserialize(partitions_def) and partitions_def is not None:
            return (
                rule_evaluation.evaluation_data,
                {
                    AssetKeyPartitionKey(self.asset_key, partition_key)
                    for partition_key in serialized_subset.deserialize(
                        partitions_def=partitions_def
                    ).get_partition_keys()
                },
            )
        # old serialized result is no longer valid
        return None

    def get_rule_evaluation_results(
        self, rule_snapshot: AutoMaterializeRuleSnapshot, asset_graph: AssetGraph
    ) -> RuleEvaluationResults:
        """For a given rule snapshot, returns the calculated evaluations for that rule."""
        results = []
        for rule_evaluation, serialized_subset in self.partition_subsets_by_condition:
            # filter for the same rule
            if rule_evaluation.rule_snapshot != rule_snapshot:
                continue
            deserialized_result = self._deserialize_rule_evaluation_result(
                rule_evaluation, serialized_subset, asset_graph
            )
            if deserialized_result:
                results.append(deserialized_result)
        return results

    def _get_asset_partitions_with_decision_type(
        self, decision_type: AutoMaterializeDecisionType, asset_graph: AssetGraph
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns the set of asset partitions with a given decision type applied to them."""
        asset_partitions = set()
        for rule_evaluation, serialized_subset in self.partition_subsets_by_condition:
            if rule_evaluation.rule_snapshot.decision_type != decision_type:
                continue
            deserialized_result = self._deserialize_rule_evaluation_result(
                rule_evaluation, serialized_subset, asset_graph
            )
            if deserialized_result is None:
                continue
            asset_partitions.update(deserialized_result[1])
        return asset_partitions

    def get_requested_or_discarded_asset_partitions(
        self, asset_graph: AssetGraph
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns the set of asset partitions which were either requested or discarded on this
        evaluation.
        """
        to_materialize = self._get_asset_partitions_with_decision_type(
            AutoMaterializeDecisionType.MATERIALIZE, asset_graph
        )
        if not to_materialize:
            return set()
        to_skip = self._get_asset_partitions_with_decision_type(
            AutoMaterializeDecisionType.SKIP, asset_graph
        )
        return to_materialize - to_skip

    def get_evaluated_asset_partitions(
        self, asset_graph: AssetGraph
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns the set of asset partitions which were evaluated by any rule on this evaluation."""
        # no asset partition can be evaluated by SKIP or DISCARD rules without having at least one
        # materialize rule evaluation
        return self._get_asset_partitions_with_decision_type(
            AutoMaterializeDecisionType.MATERIALIZE, asset_graph
        )

    def equivalent_to_stored_evaluation(
        self, stored_evaluation: Optional["AutoMaterializeAssetEvaluation"], asset_graph: AssetGraph
    ) -> bool:
        """This function returns if a stored record is equivalent to this one. To do so, we can't
        just use regular namedtuple equality, as the serialized partition subsets will be
        potentially have different string values.
        """
        if stored_evaluation is None:
            # empty evaluations are not stored on the cursor
            return self.is_empty
        return (
            self.asset_key == stored_evaluation.asset_key
            and set(self.rule_snapshots or []) == set(stored_evaluation.rule_snapshots or [])
            # if num_requested / num_discarded > 0 on the stored evaluation, then something changed
            # in the global state on the previous tick
            and stored_evaluation.num_requested == 0
            and stored_evaluation.num_discarded == 0
            and stored_evaluation.num_skipped == self.num_skipped
            # when rule evaluation results are deserialized from json, they are lists instead of
            # tuples, so we must convert them before comparing
            and sorted(self.partition_subsets_by_condition)
            == sorted([tuple(x) for x in stored_evaluation.partition_subsets_by_condition])
        )


# BACKCOMPAT GRAVEYARD


class BackcompatAutoMaterializeConditionSerializer(NamedTupleSerializer):
    """This handles backcompat for the old AutoMaterializeCondition objects, turning them into the
    proper AutoMaterializeRuleEvaluation objects. This is necessary because old
    AutoMaterializeAssetEvaluation objects will have serialized AutoMaterializeCondition objects,
    and we need to be able to deserialize them.

    In theory, as these serialized objects happen to be purged periodically, we can remove this
    backcompat logic at some point in the future.
    """

    def unpack(
        self,
        unpacked_dict: Dict[str, UnpackedValue],
        whitelist_map: WhitelistMap,
        context: UnpackContext,
    ) -> AutoMaterializeRuleEvaluation:
        from .auto_materialize_rule import (
            AutoMaterializeRule,
            DiscardOnMaxMaterializationsExceededRule,
        )

        if self.klass in (
            FreshnessAutoMaterializeCondition,
            DownstreamFreshnessAutoMaterializeCondition,
        ):
            return AutoMaterializeRuleEvaluation(
                rule_snapshot=AutoMaterializeRule.materialize_on_required_for_freshness().to_snapshot(),
                evaluation_data=None,
            )
        elif self.klass == MissingAutoMaterializeCondition:
            return AutoMaterializeRuleEvaluation(
                rule_snapshot=AutoMaterializeRule.materialize_on_missing().to_snapshot(),
                evaluation_data=None,
            )
        elif self.klass == ParentMaterializedAutoMaterializeCondition:
            updated_asset_keys = unpacked_dict.get("updated_asset_keys")
            if isinstance(updated_asset_keys, set):
                updated_asset_keys = cast(FrozenSet[AssetKey], frozenset(updated_asset_keys))
            else:
                updated_asset_keys = frozenset()
            will_update_asset_keys = unpacked_dict.get("will_update_asset_keys")
            if isinstance(will_update_asset_keys, set):
                will_update_asset_keys = cast(
                    FrozenSet[AssetKey], frozenset(will_update_asset_keys)
                )
            else:
                will_update_asset_keys = frozenset()
            return AutoMaterializeRuleEvaluation(
                rule_snapshot=AutoMaterializeRule.materialize_on_parent_updated().to_snapshot(),
                evaluation_data=ParentUpdatedRuleEvaluationData(
                    updated_asset_keys=updated_asset_keys,
                    will_update_asset_keys=will_update_asset_keys,
                ),
            )
        elif self.klass == ParentOutdatedAutoMaterializeCondition:
            waiting_on_asset_keys = unpacked_dict.get("waiting_on_asset_keys")
            if isinstance(waiting_on_asset_keys, set):
                waiting_on_asset_keys = cast(FrozenSet[AssetKey], frozenset(waiting_on_asset_keys))
            else:
                waiting_on_asset_keys = frozenset()
            return AutoMaterializeRuleEvaluation(
                rule_snapshot=AutoMaterializeRule.skip_on_parent_outdated().to_snapshot(),
                evaluation_data=WaitingOnAssetsRuleEvaluationData(
                    waiting_on_asset_keys=waiting_on_asset_keys
                ),
            )
        elif self.klass == MaxMaterializationsExceededAutoMaterializeCondition:
            return AutoMaterializeRuleEvaluation(
                rule_snapshot=DiscardOnMaxMaterializationsExceededRule(limit=1).to_snapshot(),
                evaluation_data=None,
            )
        check.failed(f"Unexpected class {self.klass}")


@whitelist_for_serdes(serializer=BackcompatAutoMaterializeConditionSerializer)
class FreshnessAutoMaterializeCondition(NamedTuple):
    ...


@whitelist_for_serdes(serializer=BackcompatAutoMaterializeConditionSerializer)
class DownstreamFreshnessAutoMaterializeCondition(NamedTuple):
    ...


@whitelist_for_serdes(serializer=BackcompatAutoMaterializeConditionSerializer)
class ParentMaterializedAutoMaterializeCondition(NamedTuple):
    ...


@whitelist_for_serdes(serializer=BackcompatAutoMaterializeConditionSerializer)
class MissingAutoMaterializeCondition(NamedTuple):
    ...


@whitelist_for_serdes(serializer=BackcompatAutoMaterializeConditionSerializer)
class ParentOutdatedAutoMaterializeCondition(NamedTuple):
    ...


@whitelist_for_serdes(serializer=BackcompatAutoMaterializeConditionSerializer)
class MaxMaterializationsExceededAutoMaterializeCondition(NamedTuple):
    ...
