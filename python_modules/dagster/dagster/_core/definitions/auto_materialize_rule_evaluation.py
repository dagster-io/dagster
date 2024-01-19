import hashlib
import operator
from abc import ABC, abstractproperty
from collections import defaultdict
from enum import Enum
from functools import reduce
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    FrozenSet,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    cast,
)

import dagster._check as check
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataMapping, MetadataValue
from dagster._serdes.serdes import (
    NamedTupleSerializer,
    UnpackContext,
    UnpackedValue,
    WhitelistMap,
    whitelist_for_serdes,
)

from .partition import DefaultPartitionsSubset, SerializedPartitionsSubset

if TYPE_CHECKING:
    from dagster._core.definitions.asset_condition import AssetSubsetWithMetadata

    from .asset_condition import (
        AssetConditionEvaluation,
        AssetConditionEvaluationWithRunIds,
        AssetConditionSnapshot,
    )


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
    @abstractproperty
    def metadata(self) -> MetadataMapping:
        raise NotImplementedError()


@whitelist_for_serdes
class TextRuleEvaluationData(
    AutoMaterializeRuleEvaluationData,
    NamedTuple("_TextRuleEvaluationData", [("text", str)]),
):
    @property
    def metadata(self) -> MetadataMapping:
        return {"text": MetadataValue.text(self.text)}


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
    @property
    def metadata(self) -> MetadataMapping:
        return {
            **{
                f"updated_parent_{i+1}": MetadataValue.asset(k)
                for i, k in enumerate(sorted(self.updated_asset_keys))
            },
            **{
                f"will_update_parent_{i+1}": MetadataValue.asset(k)
                for i, k in enumerate(sorted(self.will_update_asset_keys))
            },
        }


@whitelist_for_serdes
class WaitingOnAssetsRuleEvaluationData(
    AutoMaterializeRuleEvaluationData,
    NamedTuple(
        "_WaitingOnParentRuleEvaluationData",
        [("waiting_on_asset_keys", FrozenSet[AssetKey])],
    ),
):
    @property
    def metadata(self) -> MetadataMapping:
        return {
            **{
                f"waiting_on_ancestor_{i+1}": MetadataValue.asset(k)
                for i, k in enumerate(sorted(self.waiting_on_asset_keys))
            },
        }


RuleEvaluationResults = Tuple[AssetSubset, Sequence["AssetSubsetWithMetadata"]]


@whitelist_for_serdes
class AutoMaterializeRuleEvaluation(NamedTuple):
    rule_snapshot: AutoMaterializeRuleSnapshot
    evaluation_data: Optional[AutoMaterializeRuleEvaluationData]


# BACKCOMPAT GRAVEYARD


class BackcompatAutoMaterializeAssetEvaluationSerializer(NamedTupleSerializer):
    """This handles backcompat for the old AutoMaterializeAssetEvaluation objects, turning them into
    AssetConditionEvaluationWithRunIds objects.
    """

    def _asset_condition_snapshot_from_rule_snapshot(
        self, rule_snapshot: AutoMaterializeRuleSnapshot
    ) -> "AssetConditionSnapshot":
        from .asset_condition import AssetConditionSnapshot, RuleCondition

        unique_id_parts = [rule_snapshot.class_name, rule_snapshot.description]
        unique_id = hashlib.md5("".join(unique_id_parts).encode()).hexdigest()

        return AssetConditionSnapshot(
            class_name=RuleCondition.__name__,
            description=rule_snapshot.description,
            unique_id=unique_id,
        )

    def _get_child_rule_evaluation(
        self,
        asset_key: AssetKey,
        partition_subsets_by_condition: Sequence[
            Tuple["AutoMaterializeRuleEvaluation", Optional[SerializedPartitionsSubset]]
        ],
        is_partitioned: bool,
        rule_snapshot: AutoMaterializeRuleSnapshot,
    ) -> "AssetConditionEvaluation":
        from .asset_condition import (
            AssetConditionEvaluation,
            AssetSubsetWithMetadata,
        )

        condition_snapshot = self._asset_condition_snapshot_from_rule_snapshot(rule_snapshot)

        if is_partitioned:
            # for partitioned assets, we can't deserialize SerializedPartitionsSubset into an
            # AssetSubset, so we just return a dummy empty default partition subset
            value = DefaultPartitionsSubset(set())
        else:
            value = len(partition_subsets_by_condition) > 0

        true_subset = AssetSubset(asset_key, value)

        return AssetConditionEvaluation(
            condition_snapshot=condition_snapshot,
            true_subset=true_subset,
            candidate_subset=None,
            subsets_with_metadata=[]
            if is_partitioned
            else [
                AssetSubsetWithMetadata(
                    subset=true_subset, metadata=rule_evaluation.evaluation_data.metadata
                )
                for rule_evaluation, _ in partition_subsets_by_condition
                if rule_evaluation.evaluation_data
            ],
        )

    def _get_child_decision_type_evaluation(
        self,
        asset_key: AssetKey,
        partition_subsets_by_condition: Sequence[
            Tuple["AutoMaterializeRuleEvaluation", Optional[SerializedPartitionsSubset]]
        ],
        rule_snapshots: Sequence[AutoMaterializeRuleSnapshot],
        is_partitioned: bool,
        decision_type: AutoMaterializeDecisionType,
    ) -> Optional["AssetConditionEvaluation"]:
        from .asset_condition import (
            AssetConditionEvaluation,
            AssetConditionSnapshot,
            NotAssetCondition,
            OrAssetCondition,
        )

        partition_subsets_by_condition_by_rule_snapshot = defaultdict(list)
        for elt in partition_subsets_by_condition:
            partition_subsets_by_condition_by_rule_snapshot[elt[0].rule_snapshot].append(elt)

        child_evaluations = [
            self._get_child_rule_evaluation(
                asset_key,
                partition_subsets_by_condition_by_rule_snapshot[rule_snapshot],
                is_partitioned,
                rule_snapshot,
            )
            for rule_snapshot in rule_snapshots
            if rule_snapshot.decision_type == decision_type
        ]

        if decision_type == AutoMaterializeDecisionType.DISCARD:
            # for the discard type, we don't have an OrAssetCondition
            if len(child_evaluations) != 1:
                return None
            evaluation = child_evaluations[0]
        else:
            unique_id_parts = [
                OrAssetCondition.__name__,
                *[e.condition_snapshot.unique_id for e in child_evaluations],
            ]
            unique_id = hashlib.md5("".join(unique_id_parts).encode()).hexdigest()
            decision_type_snapshot = AssetConditionSnapshot(
                class_name=OrAssetCondition.__name__, description="", unique_id=unique_id
            )
            initial = (
                AssetSubset(asset_key, DefaultPartitionsSubset(set()))
                if is_partitioned
                else AssetSubset.empty(asset_key, None)
            )
            evaluation = AssetConditionEvaluation(
                condition_snapshot=decision_type_snapshot,
                true_subset=reduce(
                    operator.or_, (e.true_subset for e in child_evaluations), initial
                ),
                candidate_subset=None,
                subsets_with_metadata=[],
                child_evaluations=child_evaluations,
            )

        if decision_type == AutoMaterializeDecisionType.MATERIALIZE:
            return evaluation

        # non-materialize conditions are inverted
        unique_id_parts = [
            NotAssetCondition.__name__,
            evaluation.condition_snapshot.unique_id,
        ]
        unique_id = hashlib.md5("".join(unique_id_parts).encode()).hexdigest()
        return AssetConditionEvaluation(
            condition_snapshot=AssetConditionSnapshot(
                class_name=NotAssetCondition.__name__, description="", unique_id=unique_id
            ),
            # for partitioned assets, we don't bother calculating the true subset, as we can't
            # properly deserialize the inner results
            true_subset=evaluation.true_subset
            if evaluation.true_subset.is_partitioned
            else evaluation.true_subset._replace(value=not evaluation.true_subset.bool_value),
            candidate_subset=None,
            subsets_with_metadata=[],
            child_evaluations=[evaluation],
        )

    def unpack(
        self,
        unpacked_dict: Dict[str, UnpackedValue],
        whitelist_map: WhitelistMap,
        context: UnpackContext,
    ) -> "AssetConditionEvaluationWithRunIds":
        from .asset_condition import (
            AndAssetCondition,
            AssetConditionEvaluation,
            AssetConditionSnapshot,
        )

        asset_key = cast(AssetKey, unpacked_dict.get("asset_key"))
        partition_subsets_by_condition = cast(
            Sequence[Tuple[AutoMaterializeRuleEvaluation, Optional[SerializedPartitionsSubset]]],
            unpacked_dict.get("partition_subsets_by_condition"),
        )
        rule_snapshots = (
            cast(Sequence[AutoMaterializeRuleSnapshot], unpacked_dict.get("rule_snapshots", []))
            or []
        )
        is_partitioned = any(tup[1] is not None for tup in partition_subsets_by_condition)

        # get the sub-evaluations for each decision type
        materialize_evaluation = self._get_child_decision_type_evaluation(
            asset_key,
            partition_subsets_by_condition,
            rule_snapshots,
            is_partitioned,
            AutoMaterializeDecisionType.MATERIALIZE,
        )
        not_skip_evaluation = self._get_child_decision_type_evaluation(
            asset_key,
            partition_subsets_by_condition,
            rule_snapshots,
            is_partitioned,
            AutoMaterializeDecisionType.SKIP,
        )
        not_discard_evaluation = self._get_child_decision_type_evaluation(
            asset_key,
            partition_subsets_by_condition,
            rule_snapshots,
            is_partitioned,
            AutoMaterializeDecisionType.DISCARD,
        )

        # filter out any None evaluations (should realistically only happen for discard)
        child_evaluations = list(
            filter(None, [materialize_evaluation, not_skip_evaluation, not_discard_evaluation])
        )

        # the top level condition is the AND of all the sub-conditions
        unique_id_parts = [
            AndAssetCondition.__name__,
            *[e.condition_snapshot.unique_id for e in child_evaluations],
        ]
        unique_id = hashlib.md5("".join(unique_id_parts).encode()).hexdigest()
        condition_snapshot = AssetConditionSnapshot(
            class_name=AndAssetCondition.__name__, description="", unique_id=unique_id
        )

        return AssetConditionEvaluation(
            condition_snapshot=condition_snapshot,
            true_subset=reduce(operator.and_, (e.true_subset for e in child_evaluations)),
            candidate_subset=None,
            subsets_with_metadata=[],
            child_evaluations=child_evaluations,
        ).with_run_ids(cast(AbstractSet[str], unpacked_dict.get("run_ids", set())))


@whitelist_for_serdes(serializer=BackcompatAutoMaterializeAssetEvaluationSerializer)
class AutoMaterializeAssetEvaluation(NamedTuple):
    ...


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
