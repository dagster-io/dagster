import json
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Mapping, Optional, Sequence, Set, Tuple

import toposort

from dagster._annotations import experimental
from dagster._core.storage.pipeline_run import IN_PROGRESS_RUN_STATUSES, RunsFilter

from .asset_selection import AssetSelection
from .events import AssetKey
from .run_request import RunRequest
from .sensor_definition import DefaultSensorStatus, MultiAssetSensorDefinition, SensorDefinition
from .utils import check_valid_name

if TYPE_CHECKING:
    from dagster._core.definitions import AssetsDefinition, SourceAsset
    from dagster._core.storage.event_log.base import EventLogRecord


def _get_upstream_mapping(
    selection,
    assets,
    source_assets,
) -> Mapping[AssetKey, Set[AssetKey]]:
    """Computes a mapping of assets in self._selection to their parents in the asset graph"""
    upstream = defaultdict(set)
    selection_resolved = list(selection.resolve([*assets, *source_assets]))
    for a in selection_resolved:
        a_parents = list(
            AssetSelection.keys(a).upstream(depth=1).resolve([*assets, *source_assets])
        )
        # filter out a because upstream() includes the assets in the original AssetSelection
        upstream[a] = {p for p in a_parents if p != a}
    return upstream


def _get_parent_updates(
    context,
    current_asset: AssetKey,
    parent_assets: Set[AssetKey],
    cursor: Mapping[str, int],
    will_materialize_list: Sequence[AssetKey],
    source_asset_keys: Sequence[AssetKey],
    parent_in_progress_stops_materialization: bool = False,
) -> Mapping[AssetKey, Tuple[bool, Optional[int]]]:
    """The bulk of the logic in the sensor is in this function. At the end of the function we return a
    dictionary that maps each asset to a Tuple. The Tuple contains a boolean, indicating if the asset
    has materialized or will materialize, and an optional integer indicating the cursor value the
    asset should have if the cursor gets updated (if the value is None, the cursor should remain the
    same for the asset).
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

    If parent_in_progress_stops_materialization=True, there is a final condition we want to check for.
    If any of the parents is currently being materialized we want to wait to materialize the asset
    until the parent materialization is complete so that the asset can have the most up to date data.
    So, for each parent asset we check if it has a planned asset materialization event that is newer
    than the latest complete materialization. If this is the case, we don't want the asset to materialize.
    So we set parent_asset_event_records to False for all parents (so that if the sensor is set to
    materialize if any of the parents are updated, the sensor will still choose to not materialize
    the asset) and immediately return.
    """
    from dagster._core.events import DagsterEventType
    from dagster._core.storage.event_log.base import EventRecordsFilter

    parent_asset_event_records = {}

    for p in parent_assets:
        print(f"Materializations for parent {p}")
        if p in will_materialize_list:
            # if the parent will be materialized by this sensor, then we can also
            # materialize the child
            parent_asset_event_records[p] = (True, None)
        elif p in source_asset_keys:
            # if the parent is a source asset, we assume it has always been updated
            # this will be replaced if we introduce a versioning schema for source assets
            print("parent is a source asset")
            # TODO - figure out if we need to fetch materialization records here (ie if the source asset is
            # just a normal asset in another repo)
            # TODO - figure out what the cursor should update to
            parent_asset_event_records[p] = (True, None)
        else:
            if parent_in_progress_stops_materialization:
                # if the parent is currently being materialized, then we don't want to materialize the child

                # get the most recent planned materialization
                materialization_planned_event_records = context.instance.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                        asset_key=p,
                    ),
                    ascending=False,
                    limit=1,
                )
                print(f"will materialize record {materialization_planned_event_records}")

                if materialization_planned_event_records:
                    in_progress = context.instance.get_runs(
                        filters=RunsFilter(
                            run_ids=[
                                materialization_planned_event_records[0].event_log_entry.run_id
                            ],
                            statuses=IN_PROGRESS_RUN_STATUSES,
                        )
                    )
                    if in_progress:
                        # we don't want to materialize the child asset because one of its parents is
                        # being materialized. We'll materialize the asset on the next tick when the
                        # parent is up to date
                        parent_asset_event_records = {pp: (False, None) for pp in parent_assets}

                        return parent_asset_event_records

            # the parent is not currently being materialized, so check if there is has a completed materialization
            event_records = context.instance.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=p,
                    after_cursor=cursor.get(str(p)),
                ),
                ascending=False,
                limit=1,
            )
            print(f"materialization record {event_records}")

            if event_records:
                # if the run for this ^ materialization also materialized the downstream asset, we don't consider
                # the parent asset "updated" (but we do want to update the cursor)
                other_materialized_assets = context.instance.get_records_for_run(
                    run_id=event_records[0].event_log_entry.run_id,
                    of_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                )
                other_materialized_assets = [
                    event.event_log_entry.dagster_event.event_specific_data.asset_key
                    for event in other_materialized_assets.records
                ]
                if current_asset in other_materialized_assets:
                    parent_asset_event_records[p] = (False, event_records[0].storage_id)
                else:
                    # current asset was not updated along with the parent asset, so we consider the
                    # parent asset updated
                    parent_asset_event_records[p] = (True, event_records[0].storage_id)
            else:
                # the parent has not been materialized and will not be materialized by the sensor
                parent_asset_event_records[p] = (False, None)

    return parent_asset_event_records


def _make_sensor(
    selection: AssetSelection,
    name: str,
    and_condition: bool = True,  # TODO better name for this parameter
    parent_in_progress_stops_materialization: bool = False,  # TODO - better name for this parameter
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
) -> SensorDefinition:
    """Creates the sensor that will monitor the parents of all provided assets and determine
    which assets should be materialized (ie their parents have been updated).

    The cursor for this sensor is a dictionary mapping stringified AssetKeys to dictionaries. The
    dictionary for an asset is a mapping of the stringified AssetKeys of its parents to the storage id (int)
    of the latest materialization that has resulted in the child asset materializing
    """

    def sensor_fn(context):
        asset_defs_by_key = context._repository_def._assets_defs_by_key
        source_asset_defs_by_key = context._repository_def.source_assets_by_key
        upstream: Mapping[AssetKey, Set[AssetKey]] = _get_upstream_mapping(
            selection=selection,
            assets=asset_defs_by_key.values(),
            source_assets=source_asset_defs_by_key.values(),
        )

        cursor_dict: Dict[str, Dict[str, int]] = (
            json.loads(context.cursor) if context.cursor else {}
        )
        should_materialize: List[AssetKey] = []
        cursor_update_dict: Dict[str, Dict[str, int]] = {}

        # sort the assets topologically so that we process them in order
        toposort_assets = list(toposort.toposort(upstream))
        # unpack the list of sets into a list and only keep the ones we are monitoring
        toposort_assets = [
            asset for layer in toposort_assets for asset in layer if asset in upstream.keys()
        ]

        # determine which assets should materialize based on the materialization status of their
        # parents
        for a in toposort_assets:
            a_cursor = cursor_dict.get(str(a), {})
            cursor_update_dict[str(a)] = {}
            parent_update_records = _get_parent_updates(
                context,
                current_asset=a,
                parent_assets=upstream[a],
                cursor=a_cursor,
                will_materialize_list=should_materialize,
                source_asset_keys=list(source_asset_defs_by_key.keys()),
                parent_in_progress_stops_materialization=parent_in_progress_stops_materialization,
            )

            condition = all if and_condition else any
            if condition(
                [
                    materialization_status
                    for materialization_status, _ in parent_update_records.values()
                ]
            ):
                should_materialize.append(a)
                for p, (_, cursor_value) in parent_update_records.items():
                    cursor_update_dict[str(a)][str(p)] = (
                        cursor_value if cursor_value else a_cursor.get(str(p))
                    )
            else:
                # if the asset shouldn't be materialized, then keep the cursor the same
                cursor_update_dict[str(a)] = cursor_dict.get(str(a), {})

        if len(should_materialize) > 0:
            context.update_cursor(json.dumps(cursor_update_dict))
            context.cursor_has_been_updated = True
            return RunRequest(run_key=f"{context.cursor}", asset_selection=should_materialize)

    return MultiAssetSensorDefinition(
        asset_keys=[],  # TODO - what goes here?
        asset_materialization_fn=sensor_fn,
        name=name,
        job_name="__ASSET_JOB",
        minimum_interval_seconds=minimum_interval_seconds,
        description=description,
        default_status=default_status,
    )


@experimental
def build_asset_reconciliation_sensor(
    selection: AssetSelection,
    name: str,
    and_condition: bool = True,  # TODO better name for this parameter
    parent_in_progress_stops_materialization: bool = False,  # TODO - better name for this parameter
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
) -> MultiAssetSensorDefinition:
    """Constructs a sensor that will monitor the parents of the provided assets and materialize an asset
    based on the materialization of its parents. This will keep the monitored assets up to date with the
    latest data available to them. The sensor defaults to materializing a child asset when all of
    its parents have materialized, but it can be set to materialize the child asset when any of its
    parents have materialized.

    Example:
    If you have the following asset graph

        a       b       c
        \       /\      /
            d       e
            \       /
                f

    and create the sensor build_asset_reconciliation_sensor(AssetSelection.assets(d, e, f), name="my_reconciliation_sensor")

    * If a, b, and c are all materialized, then on the next sensor tick, the sensor will see that d and e can
        be materialized. Since d and e will be materialized, f can also be materialized. The sensor will kick off a
        run that will materialize d, e, and f.
    * If on the next sensor tick, a, b, and c have not been materialized again the sensor will not launch a run.
    * If before the next sensor tick, just asset a and b have been materialized, the sensor will launch a run to
        materialize d.
    * If asset c is materialized by the next sensor tick, the sensor will see that e can be materialized (since b and
        c have both been materialized since the last materialization of e). The sensor will also see that f can be materialized
        since d was updated in the previous sensor tick and e will be materialized by the sensor. The sensor will launch a run
        the materialize e and f.
    * If by the next sensor tick, only asset b has been materialized. The sensor will not launch a run since d and e both have
        a parent that has not been updated.
    * If during the next sensor tick, there is a materialization of a in progress, the sensor will not launch a run to
        materialize d. Once a has completed materialization, the next sensor tick will launch a run to materialize d.

    Other considerations:
    * If an asset has a SourceAsset as a parent, the sensor will always consider the source asset to updated
        since the previous sensor tick. If you have the asset graph my_source->my_asset where my_source is
        a SourceAsset. The sensor created from build_asset_reconciliation_sensor(AssetSelection.assets(my_asset), name="my_sensor")
        will materialize my_asset on every sensor tick.

    Args:
        selection (AssetSelection): The group of assets you want to monitor
        name (str): The name to give the sensor.
        and_condition (bool): If True (the default) the sensor will only materialize an asset when
            all of its parents have materialized. If False, the sensor will materialize an asset when
            any of its parents have materialized.
        parent_in_progress_stops_materialization (bool): If True, the sensor will not materialize an
            asset there is an in-progress run that will materialize any of the asset's parents. Defaults to
            False.
        minimum_interval_seconds (Optional[int]): The minimum amount of time that should elapse between sensor invocations.
        description (Optional[str]): A description for the sensor.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.

    Returns: A MultiAssetSensor that will monitor the parents of the provided assets to determine when
        the provided assets should be materialized
    """
    check_valid_name(name)
    return _make_sensor(
        selection=selection,
        name=name,
        and_condition=and_condition,
        parent_in_progress_stops_materialization=parent_in_progress_stops_materialization,
        minimum_interval_seconds=minimum_interval_seconds,
        description=description,
        default_status=default_status,
    )
