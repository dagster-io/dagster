import inspect
import json
from collections import defaultdict
from itertools import chain
from typing import TYPE_CHECKING, List, Mapping, Optional, Sequence

from dagster._annotations import experimental
from dagster._core.errors import DagsterInvalidDefinitionError

from .asset_selection import AssetSelection
from .events import AssetKey
from .run_request import PipelineRunReaction, RunRequest, SkipReason
from .sensor_definition import (
    DefaultSensorStatus,
    MultiAssetSensorDefinition,
    MultiAssetSensorEvaluationContext,
    SensorDefinition,
)
from .target import ExecutableDefinition
from .utils import check_valid_name

if TYPE_CHECKING:
    from dagster._core.definitions import AssetsDefinition, SourceAsset


class UnresolvedAssetSensorDefinition:
    def __init__(self):
        pass

    def resolve(
        self,
        assets: Sequence["AssetsDefinition"],
        source_assets: Sequence["SourceAsset"],
    ):
        pass


@experimental
class UnresolvedAssetSensorDefinitionV1(UnresolvedAssetSensorDefinition):
    def __init__(
        self,
        asset_selection: AssetSelection,
        name: str,
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    ):
        self._selection = asset_selection
        self._name = name
        self._minimum_interval_seconds = minimum_interval_seconds
        self._description = description
        self._default_status = default_status

        super(UnresolvedAssetSensorDefinitionV1, self).__init__()

    @property
    def name(self):
        return self._name

    def _get_upstream_mapping(
        self,
        assets: Sequence["AssetsDefinition"],
        source_assets: Sequence["SourceAsset"],
    ):
        """Computes a mapping of assets in self._selection to their parents in the asset graph"""
        upstream = defaultdict(set)
        selection_resolved = list(self._selection.resolve([*assets, *source_assets]))
        for a in selection_resolved:
            a_parents = list(AssetSelection.keys(a).upstream().resolve([*assets, *source_assets]))
            # filter out a because upstream() includes the assets in the original AssetSelection
            upstream[a] = {p for p in a_parents if p != a}
        return upstream

    def _get_parent_materializations(self, context, asset_key, parent_assets, cursor):
        from dagster._core.events import DagsterEventType
        from dagster._core.storage.event_log.base import EventRecordsFilter

        print(f"CURSOR for {asset_key} {cursor}")
        parent_asset_event_records = {}
        cursor_update_dict = {}
        for p in parent_assets:
            print(f"AFTER CURSOR for {p} {cursor.get(str(p))}")
            event_records = context.instance.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=p,
                    after_cursor=cursor.get(str(p)),
                ),
                ascending=False,
                limit=1,
            )
            if event_records:
                parent_asset_event_records[p] = event_records[0]
                cursor_update_dict[str(p)] = event_records[0].storage_id
            else:
                parent_asset_event_records[p] = None
                cursor_update_dict[str(p)] = cursor.get(str(p))

        return parent_asset_event_records, cursor_update_dict

    def _make_sensor(self, upstream):
        """
        cursor - dict for each asset in selection. each parent in the dict has a cursor

        for each asset in selection, get the cursor for the parents and fetch latest events
        if all assets have materialized, then add asset to should_materialize
        update the cursor
        """

        def sensor_fn(context):
            cursor_dict = json.loads(context.cursor) if context.cursor else {}
            print(f"CURSOR {cursor_dict}")
            should_materialize = []
            cursor_update_dict = {}
            for a in upstream.keys():
                a_cursor = cursor_dict.get(str(a)) if cursor_dict.get(str(a)) else {}
                (
                    parent_asset_event_records,
                    a_cursor_update_dict,
                ) = self._get_parent_materializations(context, a, upstream[a], a_cursor)

                if all(
                    parent_asset_event_records.values()
                ):  # should we allow the user to specify all() vs any() here?
                    should_materialize.append(a)
                    cursor_update_dict[str(a)] = a_cursor_update_dict

            print(f"SHOULD MATERIALIZE {should_materialize}")

            if len(should_materialize) > 0:
                context.update_cursor(json.dumps(cursor_update_dict))
                return RunRequest(run_key=f"{context.cursor}", asset_selection=should_materialize)

        return SensorDefinition(
            evaluation_fn=sensor_fn,
            name=self.name,
            job_name="__ASSET_JOB",
            minimum_interval_seconds=self._minimum_interval_seconds,
        )

    def resolve(
        self,
        assets: Sequence["AssetsDefinition"],
        source_assets: Sequence["SourceAsset"],
    ):
        return self._make_sensor(self._get_upstream_mapping(assets, source_assets))


# class UnresolvedAssetSensorDefinitionV2(UnresolvedAssetSensorDefinition):
#     def __init__(self, asset_selection, name):
#         self._selection = asset_selection
#         self._name = name

#         super(UnresolvedAssetSensorDefinitionV2, self).__init__()

#     @property
#     def name(self):
#         return self._name

#     def get_dependency_mapping(
#         self,
#         assets: Sequence["AssetsDefinition"],
#         source_assets: Sequence["SourceAsset"],
#     ):
#         """Computes a mapping of assets in self._selection to their parents in the asset graph"""
#         upstream = defaultdict(set)
#         downstream = defaultdict(set)
#         selection_resolved = list(self._selection.resolve([*assets, *source_assets]))
#         for a in selection_resolved:
#             a_parents = list(AssetSelection.keys(a).upstream().resolve([*assets, *source_assets]))
#             # filter out a because upstream() includes the assets in the original AssetSelection
#             upstream[a] = {p for p in a_parents if p != a}
#             for p in upstream[a]:
#                 downstream[p].add(a)
#         return {"upstream": upstream, "downstream": downstream}

#     def make_sensor(self, dependency_mapping: Mapping[AssetKey, Sequence[AssetKey]]):

#         upstream = dependency_mapping["upstream"]
#         downstream = dependency_mapping["downstream"]

#         def sensor_fn(context: MultiAssetSensorEvaluationContext):
#             latest_events = context.latest_materialization_records_by_key()

#             should_materialize: List[AssetKey] = []

#             # we want to materialize an asset if all of its parents have been materialized more recently
#             # than the asset was materialized
#             for a in upstream.keys():
#                 a_materialization = latest_events.get(a)
#                 parents_materialization = {k: v for k, v in latest_events.items() if k in upstream[a]}

#                 if all(parents_materialization.values()):  # all parents have been materialized
#                     parent_timestamps = [
#                         parent_event.event_log_entry.timestamp
#                         for parent_event in parents_materialization.values()
#                     ]

#                     if a_materialization is not None:
#                         a_timestamp = a_materialization.event_log_entry.timestamp
#                         if all(
#                             [a_timestamp < p_time for p_time in parent_timestamps]
#                         ):  # all parents have been materialized more recently than a
#                             should_materialize.append(a)
#                     else:
#                         should_materialize.append(a)

#             print(f"SHOULD MATERIALIZE {should_materialize}")
#             if len(should_materialize) > 0:
#                 # we need to update the cursor for all of the parent assets. We update the cursor for an asset if
#                 # all of the downstream assets have been materialized more recently than the asset

#                 # TODO - this won't account for failures in the materialization of assets in should_materialize
#                 # ie we update the cursor before knowing if the materializations succeeded. Should we handle this?
#                 cursor_update_dict = {}
#                 for p in downstream.keys():
#                     should_update = True
#                     for c in downstream[p]:
#                         if (
#                             latest_events[c].event_log_entry.timestamp
#                             <= latest_events[p].event_log_entry.timestamp
#                             and c not in should_materialize
#                         ):
#                             # one of the downstream hasn't been materialized yet
#                             should_update = False

#                     if should_update:
#                         cursor_update_dict[p] = latest_events[p]
#                     else:
#                         cursor_update_dict[p] = None

#                 context.advance_cursor(cursor_update_dict)

#                 # now need to actually launch the run of all should_materialize
#                 return RunRequest(run_key=f"{context.cursor}", asset_selection=should_materialize)

#         return MultiAssetSensorDefinition(
#             asset_keys=list(set(chain.from_iterable(upstream.values()))) + list(upstream.keys()),
#             asset_materialization_fn=sensor_fn,
#             name=self.name,
#             job_name="__ASSET_JOB",
#         )

#     def resolve(
#         self,
#         assets: Sequence["AssetsDefinition"],
#         source_assets: Sequence["SourceAsset"],
#     ):
#         return self.make_sensor(self.get_dependency_mapping(assets, source_assets))


@experimental
def build_asset_sensor(
    selection: AssetSelection,
    name: str,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
) -> UnresolvedAssetSensorDefinition:
    return UnresolvedAssetSensorDefinitionV1(
        asset_selection=selection,
        name=name,
        minimum_interval_seconds=minimum_interval_seconds,
        description=description,
        default_status=default_status,
    )
