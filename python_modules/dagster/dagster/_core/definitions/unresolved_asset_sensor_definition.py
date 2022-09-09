import json
from collections import defaultdict
from typing import TYPE_CHECKING, Mapping, Optional, Sequence, Set, Tuple

import toposort

from dagster._annotations import experimental

from .asset_selection import AssetSelection
from .events import AssetKey
from .run_request import RunRequest
from .sensor_definition import DefaultSensorStatus, SensorDefinition
from .utils import check_valid_name

if TYPE_CHECKING:
    from dagster._core.definitions import AssetsDefinition, SourceAsset
    from dagster._core.storage.event_log.base import EventLogRecord


@experimental
class UnresolvedAssetSensorDefinition:
    def __init__(
        self,
        asset_selection: AssetSelection,
        name: str,
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    ):
        # TODO - type checks
        self._selection = asset_selection
        self._name = check_valid_name(name)
        self._minimum_interval_seconds = minimum_interval_seconds
        self._description = description
        self._default_status = default_status

    @property
    def name(self):
        return self._name

    def _get_upstream_mapping(
        self,
        assets: Sequence["AssetsDefinition"],
        source_assets: Sequence["SourceAsset"],
    ) -> Mapping[AssetKey, Set[AssetKey]]:
        """Computes a mapping of assets in self._selection to their parents in the asset graph"""
        upstream = defaultdict(set)
        selection_resolved = list(self._selection.resolve([*assets, *source_assets]))
        for a in selection_resolved:
            a_parents = list(AssetSelection.keys(a).upstream().resolve([*assets, *source_assets]))
            # filter out a because upstream() includes the assets in the original AssetSelection
            upstream[a] = {p for p in a_parents if p != a}
        return upstream

    def _get_parent_materializations(
        self,
        context,
        parent_assets: Set[AssetKey],
        cursor: Mapping[str, int],
        will_materialize_list: Sequence[AssetKey],
    ) -> Mapping[AssetKey, Tuple[bool, Optional["EventLogRecord"]]]:
        """The bulk of the logic in the sensor is in this function. At the end of the function we return a
        dictionary that maps each asset to a Tuple. The Tuple contains a boolean, indicating if the asset
        has materialized or will materialize, and an optional EventLogRecord. The EventLogRecord is included
        when the asset has a completed materialization, and is None in all other cases.

        Here's how we get there:

        We want to get the materialization information for all of the parents of an asset to determine
        if we want to materialize the asset in this sensor tick. We also need to construct the cursor
        dictionary for the asset so that we don't process the same materialization events for the parent
        assets again.

        We iterate through each parent of the asset and determine its materialization info. The parent
        asset's materialization status can be one of three options:
        1. The parent has materialized since the last time the child was materialized (determined by the
            cursor).
        2. The parent will be materialized as part of the materialization that will be kicked off by the
            sensor.
        3. The parent has not been materialized and will not be materialized by the sensor.

        In cases 1 and 2 we indicate that the parent has been updated by setting its value in
        parent_asset_event_records to True. For case 3 we set it's value to False.

        There is a final condition we want to check for. If any of the parents is currently being materialized
        we want to wait to materialize the asset until the parent materialization is complete so that the
        asset can have the most up to date data. So, for each parent asset we check if it has a planned asset
        materialization event that is newer than the latest complete materialization. If this is the case, we
        don't want the asset to materialize. So we set parent_asset_event_records to False for all
        parents (so that if the sensor is set to materialize if any of the parents are updated, the sensor will
        still choose to not materialize the asset) and immediately return.
        """
        from dagster._core.events import DagsterEventType
        from dagster._core.storage.event_log.base import EventRecordsFilter

        parent_asset_event_records = {}

        for p in parent_assets:
            if p in will_materialize_list:
                # if the parent will be materialized by this sensor, then we can also
                # materialize the child
                parent_asset_event_records[p] = (True, None)
            else:
                # if the parent has been materialized and is not currently being materialized, then
                # we want to materialize the child

                # get the most recent completed materialization
                event_records = context.instance.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION,
                        asset_key=p,
                        after_cursor=cursor.get(str(p)),
                    ),
                    ascending=False,
                    limit=1,
                )

                # get the most recent planned materialization
                materialization_planned_event_records = context.instance.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                        asset_key=p,
                    ),
                    ascending=False,
                    limit=1,
                )

                if event_records and materialization_planned_event_records:
                    # planned materialization is from a different run than the most recent
                    # completed materialization
                    if (
                        event_records[0].event_log_entry.run_id
                        != materialization_planned_event_records[0].event_log_entry.run_id
                    ):
                        # we don't want to materialize the child asset because one of its parents is
                        # being materialized. We'll materialize the asset on the next tick when the
                        # parent is up to date
                        parent_asset_event_records = {pp: (False, None) for pp in parent_assets}

                        return parent_asset_event_records

                # there is no materialization in progress, so we can update the event dict and cursor
                # dict accordingly
                if event_records:
                    parent_asset_event_records[p] = (True, event_records[0])
                else:
                    # the parent has not been materialized and will not be materialized by the sensor
                    parent_asset_event_records[p] = (False, None)

        return parent_asset_event_records

    def _make_cursor_update_dict(
        self,
        parent_event_records: Mapping[AssetKey, Tuple[bool, Optional["EventLogRecord"]]],
        current_cursor: Mapping[str, int],
    ) -> Mapping[str, int]:
        """Given the materialization event records for the parents of an asset, construct the cursor dictionary for the asset
        using the following rules:
        1. if the parent asset has been materialized and the event record exists (ie the asset will not be
            materialized by this sensor), then the cursor should update to the storage id of the event record
        2. if the parent asset will be materialized by this sensor tick, then we don't know what the storage id will be so we
            keep the cursor the same (TODO figure out what we should actually do)
        3. if the parent asset has not been materialized and will not be materialized by the sensor then we keep the
            cursor the same
        """

        cursor_update_dict = {}
        for p, (materialization_status, event_record) in parent_event_records.items():
            if materialization_status and event_record is not None:
                cursor_update_dict[str(p)] = event_record.storage_id
            elif materialization_status:
                # TODO - figure out the right thing cursor for this scenario
                cursor_update_dict[str(p)] = self._get_cursor(current_cursor, p)
            else:
                cursor_update_dict[str(p)] = self._get_cursor(current_cursor, p)

        return cursor_update_dict

    def _get_cursor(self, cursor, asset_key):
        return cursor.get(str(asset_key)) if cursor.get(str(asset_key)) else {}

    def _make_sensor(self, upstream: Mapping[AssetKey, Set[AssetKey]]) -> SensorDefinition:
        """Creates the sensor that will monitor the parents of all provided assets and determine
        which assets should be materialized (ie their parents have been updated).

        The cursor for this sensor is a dictionary mapping stringified AssetKeys to dictionaries. The
        dictionary for an asset is a mapping of the stringified AssetKeys of its parents to the storage id
        of the latest materialization that has resulted in the child asset materializing
        """

        def sensor_fn(context):

            cursor_dict = json.loads(context.cursor) if context.cursor else {}
            should_materialize = []
            cursor_update_dict = {}

            # sort the assets topologically so that we process them in order
            toposort_assets = list(toposort.toposort(upstream))
            # unpack the list of sets into a list
            toposort_assets = [
                asset for layer in toposort_assets for asset in layer if asset in upstream.keys()
            ]

            # determine which assets should materialize based on the materialization status of their
            # parents
            for a in toposort_assets:
                a_cursor = self._get_cursor(cursor_dict, a)
                parent_materialization_records = self._get_parent_materializations(
                    context,
                    parent_assets=upstream[a],
                    cursor=a_cursor,
                    will_materialize_list=should_materialize,
                )

                if all(
                    [
                        materialization_status
                        for materialization_status, _ in parent_materialization_records.values()
                    ]
                ):  # TODO should we allow the user to specify all() vs any() here?
                    should_materialize.append(a)
                    cursor_update_dict[str(a)] = self._make_cursor_update_dict(
                        parent_event_records=parent_materialization_records, current_cursor=a_cursor
                    )
                else:
                    # if the asset shouldn't be materialized, then keep the cursor the same
                    cursor_update_dict[str(a)] = self._get_cursor(cursor_dict, a)

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
    ) -> SensorDefinition:
        return self._make_sensor(self._get_upstream_mapping(assets, source_assets))


@experimental
def build_asset_sensor(
    selection: AssetSelection,
    name: str,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
) -> UnresolvedAssetSensorDefinition:
    return UnresolvedAssetSensorDefinition(
        asset_selection=selection,
        name=name,
        minimum_interval_seconds=minimum_interval_seconds,
        description=description,
        default_status=default_status,
    )
