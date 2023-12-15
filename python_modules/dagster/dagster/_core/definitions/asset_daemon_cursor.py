import functools
import json
from typing import (
    TYPE_CHECKING,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Type,
    TypeVar,
)

from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.auto_materialize_rule_evaluation import (
    BackcompatAutoMaterializeAssetEvaluationSerializer,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._serdes.serdes import (
    _WHITELIST_MAP,
    PackableValue,
    WhitelistMap,
    deserialize_value,
    whitelist_for_serdes,
)

from .asset_graph import AssetGraph

if TYPE_CHECKING:
    from .asset_condition import AssetCondition, AssetConditionEvaluation, AssetConditionSnapshot

T = TypeVar("T")


@whitelist_for_serdes
class AssetConditionCursorExtras(NamedTuple):
    """Represents additional state that may be optionally saved by an AssetCondition between
    evaluations.
    """

    condition_snapshot: "AssetConditionSnapshot"
    extras: Mapping[str, PackableValue]


@whitelist_for_serdes
class AssetConditionCursor(NamedTuple):
    """Represents the evaluated state of an AssetConditionCursor at a certain point in time. This
    information can be used to make future evaluations more efficient.
    """

    asset_key: AssetKey
    previous_evaluation: Optional["AssetConditionEvaluation"]
    previous_max_storage_id: Optional[int]
    previous_evaluation_timestamp: Optional[float]

    extras: Sequence[AssetConditionCursorExtras]

    @staticmethod
    def empty(asset_key: AssetKey) -> "AssetConditionCursor":
        return AssetConditionCursor(
            asset_key=asset_key,
            previous_evaluation=None,
            previous_max_storage_id=None,
            previous_evaluation_timestamp=None,
            extras=[],
        )

    def get_extras_value(
        self, condition: "AssetCondition", key: str, as_type: Type[T]
    ) -> Optional[T]:
        """Returns a value from the extras dict for the given condition, if it exists and is of the
        expected type. Otherwise, returns None.
        """
        for condition_extras in self.extras:
            if condition_extras.condition_snapshot == condition.snapshot:
                extras_value = condition_extras.extras.get(key)
                if isinstance(extras_value, as_type):
                    return extras_value
                return None
        return None

    def get_previous_requested_or_discarded_subset(
        self, condition: "AssetCondition", partitions_def: Optional[PartitionsDefinition]
    ) -> AssetSubset:
        if not self.previous_evaluation:
            return AssetSubset.empty(self.asset_key, partitions_def)
        return self.previous_evaluation.get_requested_or_discarded_subset(condition)


@whitelist_for_serdes
class AssetDaemonCursor(NamedTuple):
    """State that's stored between daemon evaluations.

    Attributes:
        evaluation_id (int): The ID of the evaluation that produced this cursor.
        asset_cursors (Sequence[AssetConditionCursor]): The state of each asset that the daemon
            is responsible for handling.
    """

    evaluation_id: int
    asset_cursors: Sequence[AssetConditionCursor]

    last_observe_request_timestamp_by_asset_key: Mapping[AssetKey, float]

    @staticmethod
    def empty(evaluation_id: int = 0) -> "AssetDaemonCursor":
        return AssetDaemonCursor(
            evaluation_id=evaluation_id,
            asset_cursors=[],
            last_observe_request_timestamp_by_asset_key={},
        )

    @property
    @functools.lru_cache(maxsize=1)
    def asset_cursors_by_key(self) -> Mapping[AssetKey, AssetConditionCursor]:
        """Efficient lookup of asset cursors by asset key."""
        return {cursor.asset_key: cursor for cursor in self.asset_cursors}

    def get_asset_cursor(self, asset_key: AssetKey) -> AssetConditionCursor:
        """Returns the AssetConditionCursor associated with the given asset key. If no stored
        cursor exists, returns an empty cursor.
        """
        return self.asset_cursors_by_key.get(asset_key) or AssetConditionCursor.empty(asset_key)

    def get_previous_evaluation(self, asset_key: AssetKey) -> Optional["AssetConditionEvaluation"]:
        """Returns the previous AssetConditionEvaluation for a given asset key, if it exists."""
        cursor = self.get_asset_cursor(asset_key)
        return cursor.previous_evaluation if cursor else None

    def with_updates(
        self,
        evaluation_id: int,
        evaluation_timestamp: float,
        newly_observe_requested_asset_keys: Sequence[AssetKey],
        asset_cursors: Sequence[AssetConditionCursor],
    ) -> "AssetDaemonCursor":
        return self._replace(
            evaluation_id=evaluation_id,
            asset_cursors=asset_cursors,
            last_observe_request_timestamp_by_asset_key={
                **self.last_observe_request_timestamp_by_asset_key,
                **{
                    asset_key: evaluation_timestamp
                    for asset_key in newly_observe_requested_asset_keys
                },
            },
        )

    def __hash__(self) -> int:
        return hash(id(self))


# BACKCOMPAT


def get_backcompat_asset_condition_cursor(
    asset_key: AssetKey,
    latest_storage_id: Optional[int],
    latest_timestamp: Optional[float],
    latest_evaluation: Optional["AssetConditionEvaluation"],
    handled_root_subset: Optional[AssetSubset],
) -> AssetConditionCursor:
    """Generates an AssetDaemonCursor from information available on the old cursor format."""
    from dagster._core.definitions.asset_condition import RuleCondition
    from dagster._core.definitions.auto_materialize_rule import MaterializeOnMissingRule

    return AssetConditionCursor(
        asset_key=asset_key,
        previous_evaluation=latest_evaluation,
        previous_evaluation_timestamp=latest_timestamp,
        previous_max_storage_id=latest_storage_id,
        extras=[
            # the only information we need to preserve from the previous cursor is the handled
            # subset
            AssetConditionCursorExtras(
                condition_snapshot=RuleCondition(MaterializeOnMissingRule()).snapshot,
                extras={MaterializeOnMissingRule.HANDLED_SUBSET_KEY: handled_root_subset},
            )
        ],
    )


def backcompat_deserialize_asset_daemon_cursor_str(
    cursor_str: str, asset_graph: Optional[AssetGraph], default_evaluation_id: int
) -> AssetDaemonCursor:
    """This serves as a backcompat layer for deserializing the old cursor format. Some information
    is impossible to fully recover, this will recover enough to continue operating as normal.
    """
    from .asset_condition import AssetConditionEvaluationWithRunIds

    data = json.loads(cursor_str)

    if isinstance(data, list):
        evaluation_id = data[0] if isinstance(data[0], int) else default_evaluation_id
        return AssetDaemonCursor.empty(evaluation_id)
    elif not isinstance(data, dict):
        return AssetDaemonCursor.empty(default_evaluation_id)

    serialized_last_observe_request_timestamp_by_asset_key = data.get(
        "last_observe_request_timestamp_by_asset_key", {}
    )
    last_observe_request_timestamp_by_asset_key = {
        AssetKey.from_user_string(key_str): timestamp
        for key_str, timestamp in serialized_last_observe_request_timestamp_by_asset_key.items()
    }

    partition_subsets_by_asset_key = {}
    for key_str, serialized_str in data.get("handled_root_partitions_by_asset_key", {}).items():
        asset_key = AssetKey.from_user_string(key_str)
        partitions_def = asset_graph.get_partitions_def(asset_key) if asset_graph else None
        if not partitions_def:
            continue
        try:
            partition_subsets_by_asset_key[asset_key] = partitions_def.deserialize_subset(
                serialized_str
            )
        except:
            continue

    handled_root_asset_graph_subset = AssetGraphSubset(
        non_partitioned_asset_keys={
            AssetKey.from_user_string(key_str)
            for key_str in data.get("handled_root_asset_keys", set())
        },
        partitions_subsets_by_asset_key=partition_subsets_by_asset_key,
    )

    serialized_latest_evaluation_by_asset_key = data.get("latest_evaluation_by_asset_key", {})
    latest_evaluation_by_asset_key = {}
    for key_str, serialized_evaluation in serialized_latest_evaluation_by_asset_key.items():
        key = AssetKey.from_user_string(key_str)

        class BackcompatDeserializer(BackcompatAutoMaterializeAssetEvaluationSerializer):
            @property
            def partitions_def(self) -> Optional[PartitionsDefinition]:
                return asset_graph.get_partitions_def(key) if asset_graph else None

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

        # these string cursors will contain AutoMaterializeAssetEvaluation objects, which get
        # deserialized into AssetConditionEvaluationWithRunIds, not AssetConditionEvaluation
        evaluation = deserialize_value(
            serialized_evaluation, AssetConditionEvaluationWithRunIds, whitelist_map=whitelist_map
        ).evaluation
        latest_evaluation_by_asset_key[key] = evaluation

    asset_cursors = []
    for asset_key, latest_evaluation in latest_evaluation_by_asset_key.items():
        asset_cursors.append(
            get_backcompat_asset_condition_cursor(
                asset_key,
                data.get("latest_storage_id"),
                data.get("latest_timestamp"),
                latest_evaluation,
                handled_root_asset_graph_subset.get_asset_subset(asset_key, asset_graph)
                if asset_graph
                else None,
            )
        )

    return AssetDaemonCursor(
        evaluation_id=default_evaluation_id,
        asset_cursors=asset_cursors,
        last_observe_request_timestamp_by_asset_key=last_observe_request_timestamp_by_asset_key,
    )


@whitelist_for_serdes
class LegacyAssetDaemonCursorWrapper(NamedTuple):
    """Wrapper class for the legacy AssetDaemonCursor object, which is not a serializable NamedTuple."""

    serialized_cursor: str

    def get_asset_daemon_cursor(self, asset_graph: Optional[AssetGraph]) -> AssetDaemonCursor:
        return backcompat_deserialize_asset_daemon_cursor_str(
            self.serialized_cursor, asset_graph, 0
        )
