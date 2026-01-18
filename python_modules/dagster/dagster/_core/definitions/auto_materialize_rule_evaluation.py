from abc import ABC, abstractproperty
from enum import Enum
from typing import NamedTuple, Optional

from dagster_shared.serdes.serdes import (
    NamedTupleSerializer,
    UnpackContext,
    UnpackedValue,
    WhitelistMap,
    whitelist_for_serdes,
)

from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionEvaluation,
    AutomationConditionEvaluationWithRunIds,
    AutomationConditionNodeSnapshot,
    HistoricalAllPartitionsSubsetSentinel,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataMapping, MetadataValue


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


class AutoMaterializeRuleEvaluationData(ABC):
    @abstractproperty
    def metadata(self) -> MetadataMapping:
        raise NotImplementedError()

    @property
    def frozen_metadata(self) -> frozenset[tuple[str, MetadataValue]]:
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
            ("updated_asset_keys", frozenset[AssetKey]),
            ("will_update_asset_keys", frozenset[AssetKey]),
        ],
    ),
):
    @property
    def metadata(self) -> MetadataMapping:
        return {
            **{
                f"updated_parent_{i + 1}": MetadataValue.asset(k)
                for i, k in enumerate(sorted(self.updated_asset_keys))
            },
            **{
                f"will_update_parent_{i + 1}": MetadataValue.asset(k)
                for i, k in enumerate(sorted(self.will_update_asset_keys))
            },
        }


@whitelist_for_serdes
class WaitingOnAssetsRuleEvaluationData(
    AutoMaterializeRuleEvaluationData,
    NamedTuple(
        "_WaitingOnParentRuleEvaluationData",
        [("waiting_on_asset_keys", frozenset[AssetKey])],
    ),
):
    @property
    def metadata(self) -> MetadataMapping:
        return {
            **{
                f"waiting_on_ancestor_{i + 1}": MetadataValue.asset(k)
                for i, k in enumerate(sorted(self.waiting_on_asset_keys))
            },
        }


# BACKCOMPAT GRAVEYARD


class BackcompatNullSerializer(NamedTupleSerializer):
    """Unpacks an arbitrary object into None."""

    def unpack(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        unpacked_dict: dict[str, UnpackedValue],
        whitelist_map: WhitelistMap,
        context: UnpackContext,
    ) -> None:
        return None


class BackcompatAutoMaterializeAssetEvaluationSerializer(NamedTupleSerializer):
    """Unpacks the legacy AutoMaterializeAssetEvaluation class into a completely empty
    AutomationConditionEvaluationWithRunIds.
    """

    def unpack(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        unpacked_dict: dict[str, UnpackedValue],
        whitelist_map: WhitelistMap,
        context: UnpackContext,
    ) -> "AutomationConditionEvaluationWithRunIds":
        return AutomationConditionEvaluationWithRunIds(
            evaluation=AutomationConditionEvaluation(
                condition_snapshot=AutomationConditionNodeSnapshot("", "", "", None, None),
                start_timestamp=None,
                end_timestamp=None,
                true_subset=SerializableEntitySubset(key=AssetKey("unknown"), value=False),
                candidate_subset=HistoricalAllPartitionsSubsetSentinel(),
                subsets_with_metadata=[],
                child_evaluations=[],
            ),
            run_ids=frozenset(),
        )


@whitelist_for_serdes(serializer=BackcompatAutoMaterializeAssetEvaluationSerializer)
class AutoMaterializeAssetEvaluation(NamedTuple): ...


@whitelist_for_serdes(serializer=BackcompatNullSerializer)
class AutoMaterializeRuleSnapshot(NamedTuple):
    class_name: str
    description: str
    decision_type: AutoMaterializeDecisionType


@whitelist_for_serdes(serializer=BackcompatNullSerializer)
class AutoMaterializeRuleEvaluation(NamedTuple):
    rule_snapshot: AutoMaterializeRuleSnapshot
    evaluation_data: Optional[AutoMaterializeRuleEvaluationData]
