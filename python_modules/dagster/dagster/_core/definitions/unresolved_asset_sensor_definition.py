import json
from collections import defaultdict
from typing import TYPE_CHECKING, Optional, Sequence

import toposort

from dagster._annotations import experimental

from .asset_selection import AssetSelection
from .run_request import RunRequest
from .sensor_definition import DefaultSensorStatus, SensorDefinition
from .utils import check_valid_name

if TYPE_CHECKING:
    from dagster._core.definitions import AssetsDefinition, SourceAsset


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
    ):
        """Computes a mapping of assets in self._selection to their parents in the asset graph"""
        upstream = defaultdict(set)
        selection_resolved = list(self._selection.resolve([*assets, *source_assets]))
        for a in selection_resolved:
            a_parents = list(AssetSelection.keys(a).upstream().resolve([*assets, *source_assets]))
            # filter out a because upstream() includes the assets in the original AssetSelection
            upstream[a] = {p for p in a_parents if p != a}
        return upstream

    def _get_parent_materializations(self, context, parent_assets, cursor, will_materialize_list):
        """The bulk of the logic in the sensor is in this function. Here's what's happening:

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
        cursor_update_dict = {}

        print(f"CURSOR DICT {cursor}")

        for p in parent_assets:
            if p in will_materialize_list:
                # if the parent will be materialized by this sensor, then we can also
                # materialize the child
                parent_asset_event_records[p] = True
                # TODO - figure out what to do with the cursor in this case
                cursor_update_dict[str(p)] = cursor.get(str(p))
            else:
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
                print(f"MATERIALIZATION ER {event_records}")
                # get the most recent planned materialization
                materialization_planned_event_records = context.instance.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                        asset_key=p,
                        # after_cursor=cursor.get(str(p)),
                    ),
                    ascending=False,
                    limit=1,
                )
                print(f"MATERIALIZATION PLANNED ER {materialization_planned_event_records}")

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
                        parent_asset_event_records = {pp: False for pp in parent_assets}
                        cursor_update_dict = {str(pp): cursor.get(str(pp)) for pp in parent_assets}

                        print(f"RETURNING because current materialization {cursor_update_dict}")

                        return parent_asset_event_records, cursor_update_dict

                # there is no materialization in progress, so we can update the event dict and cursor
                # dict accordingly
                if event_records:
                    # TODO - i could store the event record data, but this is really only useful if
                    # we want to allow users to write complex functions to determine if the asset should
                    # materialize. If we keep the True/False, then we should rename the dict to indicate what it actually stores
                    # parent_asset_event_records[p] = event_records[0]
                    parent_asset_event_records[p] = True
                    cursor_update_dict[str(p)] = event_records[0].storage_id
                else:
                    parent_asset_event_records[p] = False
                    cursor_update_dict[str(p)] = cursor.get(str(p))

        print(f"RETURNING because normal {cursor_update_dict}")
        return parent_asset_event_records, cursor_update_dict

    def _make_sensor(self, upstream):
        """Creates the sensor that will monitor the parents of all provided assets and determine
        which assets should be materialized (ie their parents have been updated).

        The cursor for this sensor is a dictionary mapping stringified AssetKeys to dictionaries. The
        dictionary for an asset is a mapping of the stringified AssetKeys of its parents to the storage id
        of the latest materialization that has been resulted in the child asset materializing
        """

        def sensor_fn(context):

            cursor_dict = json.loads(context.cursor) if context.cursor else {}
            should_materialize = []
            cursor_update_dict = {}

            print(f"START OF SENSOR CURSOR DICT {cursor_dict}")

            # sort the assets topologically so that we process them in order
            toposort_assets = list(toposort.toposort(upstream))
            # unpack the list of sets into a list
            toposort_assets = [j for i in toposort_assets for j in i]

            # determine which assets should materialize because all of their parents have
            # materialized
            for a in toposort_assets:
                if a not in upstream.keys():
                    # all of the assets in upstream (keys and values) are sorted in toposort_assets
                    # so if a is not a key, it's not one of the assets we're monitoring
                    continue

                a_cursor = cursor_dict.get(str(a)) if cursor_dict.get(str(a)) else {}
                (
                    parent_asset_event_records,
                    a_cursor_update_dict,
                ) = self._get_parent_materializations(
                    context,
                    parent_assets=upstream[a],
                    cursor=a_cursor,
                    will_materialize_list=should_materialize,
                )

                if all(
                    parent_asset_event_records.values()
                ):  # TODO should we allow the user to specify all() vs any() here?
                    should_materialize.append(a)
                    cursor_update_dict[str(a)] = a_cursor_update_dict
                else:
                    cursor_update_dict[str(a)] = cursor_dict.get(str(a)) if cursor_dict.get(str(a)) else {}


            print(f"SHOULD MATERIALIZE {should_materialize}")
            print(f"CURSOR UPDATE DICT {cursor_update_dict}")

            if len(should_materialize) > 0:
                context.update_cursor(json.dumps(cursor_update_dict))
                print(f"END OF SENSOR CURSOR DICT {cursor_dict}")
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
