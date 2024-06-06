from abc import ABC, abstractproperty
from collections import defaultdict
from enum import Enum
from typing import AbstractSet, Dict, FrozenSet, NamedTuple, Optional, Sequence, Tuple, Union, cast

import dagster._check as check
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataMapping, MetadataValue
from dagster._serdes.serdes import (
    _WHITELIST_MAP,
    NamedTupleSerializer,
    PackableValue,
    UnpackContext,
    UnpackedValue,
    WhitelistMap,
    deserialize_value,
    whitelist_for_serdes,
)
from dagster._utils.security import non_secure_md5_hash_str

from .declarative_automation.serialized_objects import (
    AssetConditionEvaluation,
    AssetConditionEvaluationWithRunIds,
    AssetConditionSnapshot,
    AssetSubsetWithMetadata,
)
from .partition import PartitionsDefinition, SerializedPartitionsSubset


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

    @property
    def frozen_metadata(self) -> FrozenSet[Tuple[str, MetadataValue]]:
        return frozenset(self.metadata.items())


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


RuleEvaluations = Tuple[AssetSubset, Sequence["AssetSubsetWithMetadata"], PackableValue]


@whitelist_for_serdes
class AutoMaterializeRuleEvaluation(NamedTuple):
    rule_snapshot: AutoMaterializeRuleSnapshot
    evaluation_data: Optional[AutoMaterializeRuleEvaluationData]


# BACKCOMPAT GRAVEYARD


def deserialize_auto_materialize_asset_evaluation_to_asset_condition_evaluation_with_run_ids(
    serialized_evaluation: str, partitions_def: Optional[PartitionsDefinition]
) -> "AssetConditionEvaluationWithRunIds":
    """Provides a backcompat layer to allow deserializing old AutoMaterializeAssetEvaluation
    objects into the new AssetConditionEvaluationWithRunIds objects.
    """
    from .declarative_automation.serialized_objects import AssetConditionEvaluationWithRunIds

    class BackcompatDeserializer(BackcompatAutoMaterializeAssetEvaluationSerializer):
        @property
        def partitions_def(self) -> Optional[PartitionsDefinition]:
            return partitions_def

    # create a new WhitelistMap that can deserialize SerializedPartitionSubset objects stored
    # on the old cursor format
    whitelist_map = WhitelistMap(
        object_serializers=_WHITELIST_MAP.object_serializers,
        object_deserializers={
            **_WHITELIST_MAP.object_deserializers,
            "AutoMaterializeAssetEvaluation": BackcompatDeserializer(
                klass=AssetConditionEvaluationWithRunIds
            ),
        },
        enum_serializers=_WHITELIST_MAP.enum_serializers,
    )

    return deserialize_value(
        serialized_evaluation, AssetConditionEvaluationWithRunIds, whitelist_map=whitelist_map
    )


def deserialize_serialized_partitions_subset_to_asset_subset(
    serialized: SerializedPartitionsSubset,
    asset_key: AssetKey,
    partitions_def: Optional[PartitionsDefinition],
) -> AssetSubset:
    if partitions_def is None or not serialized.can_deserialize(partitions_def):
        # partitions def has changed since storage time
        return AssetSubset.empty(asset_key, partitions_def)

    return AssetSubset(asset_key=asset_key, value=serialized.deserialize(partitions_def))


class BackcompatAutoMaterializeAssetEvaluationSerializer(NamedTupleSerializer):
    """This handles backcompat for the old AutoMaterializeAssetEvaluation objects, turning them into
    AssetConditionEvaluationWithRunIds objects.
    """

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        """This property gets overridden by subclasses at runtime, once the partitions_def for the
        specific record we're deserializing is known.
        """
        raise NotImplementedError()

    def deserialize_serialized_partitions_subset_or_none(
        self,
        asset_key: AssetKey,
        serialized: Union[None, SerializedPartitionsSubset],
    ) -> AssetSubset:
        if serialized is None:
            # Confusingly, we used `None` to indicate "all of an unpartitioned asset" in the old
            # serialization scheme
            return AssetSubset(asset_key=asset_key, value=True)
        return deserialize_serialized_partitions_subset_to_asset_subset(
            serialized, asset_key, self.partitions_def
        )

    def _asset_condition_snapshot_from_rule_snapshot(
        self, rule_snapshot: AutoMaterializeRuleSnapshot
    ) -> "AssetConditionSnapshot":
        from .declarative_automation.legacy.rule_condition import RuleCondition
        from .declarative_automation.serialized_objects import AssetConditionSnapshot

        unique_id_parts = [rule_snapshot.class_name, rule_snapshot.description]
        unique_id = non_secure_md5_hash_str("".join(unique_id_parts).encode())

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
        from .declarative_automation.serialized_objects import HistoricalAllPartitionsSubsetSentinel

        condition_snapshot = self._asset_condition_snapshot_from_rule_snapshot(rule_snapshot)

        subsets_with_metadata = [
            AssetSubsetWithMetadata(
                subset=self.deserialize_serialized_partitions_subset_or_none(asset_key, serialized),
                metadata=rule_evaluation.evaluation_data.metadata,
            )
            for rule_evaluation, serialized in partition_subsets_by_condition
            if rule_evaluation.evaluation_data
        ]

        true_subset = AssetSubset.empty(asset_key, self.partitions_def)
        for _, serialized in partition_subsets_by_condition:
            true_subset |= self.deserialize_serialized_partitions_subset_or_none(
                asset_key, serialized
            )

        return AssetConditionEvaluation(
            condition_snapshot=condition_snapshot,
            true_subset=true_subset,
            candidate_subset=HistoricalAllPartitionsSubsetSentinel()
            if is_partitioned
            else AssetSubset.all(asset_key, None),
            start_timestamp=None,
            end_timestamp=None,
            subsets_with_metadata=subsets_with_metadata,
            child_evaluations=[],
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
        from .declarative_automation.operators.boolean_operators import (
            NotAssetCondition,
            OrAssetCondition,
        )
        from .declarative_automation.serialized_objects import HistoricalAllPartitionsSubsetSentinel

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
            for rule_snapshot in (
                set(rule_snapshots) | set(partition_subsets_by_condition_by_rule_snapshot.keys())
            )
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
            unique_id = non_secure_md5_hash_str("".join(unique_id_parts).encode())
            decision_type_snapshot = AssetConditionSnapshot(
                class_name=OrAssetCondition.__name__, description="Any of", unique_id=unique_id
            )
            true_subset = AssetSubset.empty(asset_key, self.partitions_def)
            for e in child_evaluations:
                true_subset |= e.true_subset
            evaluation = AssetConditionEvaluation(
                condition_snapshot=decision_type_snapshot,
                true_subset=true_subset,
                candidate_subset=HistoricalAllPartitionsSubsetSentinel()
                if is_partitioned
                else AssetSubset.all(asset_key, None),
                subsets_with_metadata=[],
                child_evaluations=child_evaluations,
                start_timestamp=None,
                end_timestamp=None,
            )

        if decision_type == AutoMaterializeDecisionType.MATERIALIZE:
            return evaluation

        # non-materialize conditions are inverted
        unique_id_parts = [
            NotAssetCondition.__name__,
            evaluation.condition_snapshot.unique_id,
        ]
        unique_id = non_secure_md5_hash_str("".join(unique_id_parts).encode())

        if is_partitioned:
            # In reality, we'd like to invert the inner true_subset here, but this is an
            # expensive operation, and error-prone as the set of all partitions may have changed
            # since the evaluation was stored. Instead, we just use an empty subset.
            true_subset = AssetSubset.empty(asset_key, self.partitions_def)
        else:
            true_subset = evaluation.true_subset._replace(
                value=not evaluation.true_subset.bool_value
            )
        return AssetConditionEvaluation(
            condition_snapshot=AssetConditionSnapshot(
                class_name=NotAssetCondition.__name__, description="Not", unique_id=unique_id
            ),
            true_subset=true_subset,
            candidate_subset=HistoricalAllPartitionsSubsetSentinel()
            if is_partitioned
            else AssetSubset.all(asset_key, None),
            subsets_with_metadata=[],
            child_evaluations=[evaluation],
            start_timestamp=None,
            end_timestamp=None,
        )

    def unpack(
        self,
        unpacked_dict: Dict[str, UnpackedValue],
        whitelist_map: WhitelistMap,
        context: UnpackContext,
    ) -> "AssetConditionEvaluationWithRunIds":
        from .declarative_automation.operators.boolean_operators import AndAssetCondition
        from .declarative_automation.serialized_objects import HistoricalAllPartitionsSubsetSentinel

        asset_key = cast(AssetKey, unpacked_dict.get("asset_key"))
        partition_subsets_by_condition = cast(
            Sequence[Tuple[AutoMaterializeRuleEvaluation, Optional[SerializedPartitionsSubset]]],
            unpacked_dict.get("partition_subsets_by_condition"),
        )
        rule_snapshots = (
            cast(Sequence[AutoMaterializeRuleSnapshot], unpacked_dict.get("rule_snapshots", []))
            or []
        )
        is_partitioned = (
            any(tup[1] is not None for tup in partition_subsets_by_condition)
            if partition_subsets_by_condition
            # if we don't have any partition_subsets_by_condition to look at, we can't tell if this
            # asset was partitioned at the time that the evaluation was stored, so instead we assume
            # that its current partition status is the same as its partition status at storage time.
            else self.partitions_def is not None
        )

        # get the sub-evaluations for each decision type
        materialize_evaluation = check.not_none(
            self._get_child_decision_type_evaluation(
                asset_key,
                partition_subsets_by_condition,
                rule_snapshots,
                is_partitioned,
                AutoMaterializeDecisionType.MATERIALIZE,
            )
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
        unique_id = non_secure_md5_hash_str("".join(unique_id_parts).encode())
        condition_snapshot = AssetConditionSnapshot(
            class_name=AndAssetCondition.__name__, description="All of", unique_id=unique_id
        )

        # all AssetSubsets generated here are created using the current partitions_def, so they
        # will be valid
        true_subset = materialize_evaluation.true_subset.as_valid(self.partitions_def)
        if not_skip_evaluation:
            true_subset -= not_skip_evaluation.child_evaluations[0].true_subset
        if not_discard_evaluation:
            true_subset -= not_discard_evaluation.child_evaluations[0].true_subset

        return AssetConditionEvaluation(
            condition_snapshot=condition_snapshot,
            true_subset=true_subset,
            candidate_subset=HistoricalAllPartitionsSubsetSentinel()
            if is_partitioned
            else AssetSubset.all(asset_key, None),
            subsets_with_metadata=[],
            child_evaluations=child_evaluations,
            start_timestamp=None,
            end_timestamp=None,
        ).with_run_ids(cast(AbstractSet[str], unpacked_dict.get("run_ids", set())))


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
        from .auto_materialize_rule import AutoMaterializeRule
        from .auto_materialize_rule_impls import DiscardOnMaxMaterializationsExceededRule

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
class FreshnessAutoMaterializeCondition(NamedTuple): ...


@whitelist_for_serdes(serializer=BackcompatAutoMaterializeConditionSerializer)
class DownstreamFreshnessAutoMaterializeCondition(NamedTuple): ...


@whitelist_for_serdes(serializer=BackcompatAutoMaterializeConditionSerializer)
class ParentMaterializedAutoMaterializeCondition(NamedTuple): ...


@whitelist_for_serdes(serializer=BackcompatAutoMaterializeConditionSerializer)
class MissingAutoMaterializeCondition(NamedTuple): ...


@whitelist_for_serdes(serializer=BackcompatAutoMaterializeConditionSerializer)
class ParentOutdatedAutoMaterializeCondition(NamedTuple): ...


@whitelist_for_serdes(serializer=BackcompatAutoMaterializeConditionSerializer)
class MaxMaterializationsExceededAutoMaterializeCondition(NamedTuple): ...
