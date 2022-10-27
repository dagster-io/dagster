from datetime import datetime, timezone
from typing import AbstractSet, Mapping, Optional, Tuple

from ..definitions.events import AssetKey
from ..instance import DagsterInstance

ROOT_DATA_TAG = ".dagster/root_data_ids"


def get_upstream_materialization_times_for_key(
    instance: DagsterInstance,
    asset_key: AssetKey,
    upstream_asset_key_mapping: Mapping[str, AbstractSet[str]],
) -> Mapping[str, Tuple[Optional[int], Optional[datetime]]]:
    """
    Recursive method to derive the timestamps of the materializations of upstream assets
    which were used to produce a given materialization.

        * For an asset with no parents, this value is just the timestamp of the given
        materialization.

        * For an asset with a single parent (which is a root), we find the most recent
        materialization of that parent which happened /before/ the given materialization, as this
        is the timestamp of the data which was used to produce the given materialization.

        * For an asset with a single parent (which is not a root), we find the most recent
        materialization of the parent which happened /before/ the given materialization, then find
        the data times of that event. This process continues recursively up to the root. If an
        asset has multiple parents, it is possible to have consumed different timestamps of root
        assets from different parent paths. In these cases, we take the maximum timestamp for each
        key.

    To make this process more performant, whenever we calculate these values for a given asset
    materialization, we cache this information in the DagsterInstance database by tagging the
    event with the timestamps of its upstream materializations. Before calculating any value, we
    check if we've already stored it, and if so we can exit early.
    """
    from dagster._core.events import DagsterEventType
    from dagster._core.storage.event_log.base import EventRecordsFilter

    def _get_root_keys(asset_key):
        def _recursive(key_str):
            upstream_key_strs = upstream_asset_key_mapping[key_str]
            if not upstream_key_strs:
                return {key_str}
            return set().union(
                *(_recursive(upstream_key_str) for upstream_key_str in upstream_key_strs)
            )

        return _recursive(asset_key.to_user_string())

    def _get_upstream_materialization_times(record):

        # check if we've already calculated data times for this record
        cur_tags = instance.get_asset_event_tags(record.storage_id)
        if ROOT_DATA_TAG in cur_tags:
            return cur_tags[ROOT_DATA_TAG]

        # find parent asset keys
        cur_key = record.event_log_entry.dagster_event.event_specific_data.materialization.asset_key
        upstream_keys = upstream_asset_key_mapping[cur_key.to_user_string()]

        if not upstream_keys:
            # you're a root key, so no need to recurse
            root_data = {
                cur_key.to_user_string(): (
                    record.storage_id,
                    record.event_log_entry.timestamp,
                )
            }
        else:
            root_data = {}
            for upstream_key_str in upstream_keys:
                upstream_key = AssetKey.from_user_string(upstream_key_str)
                upstream_records = instance.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION,
                        asset_key=upstream_key,
                        before_cursor=record.storage_id,
                    ),
                    ascending=False,
                    limit=1,
                )
                if not upstream_records:
                    # no materialization happened before this one
                    # in these cases, set the root data times to None as no upstream data was used
                    # for this materialization (as far as we can tell)
                    for root_key in _get_root_keys(upstream_key):
                        root_data[root_key] = (None, None)

                else:
                    # recurse to find the materialization times used to generated your parents
                    upstream_times = _get_upstream_materialization_times(upstream_records[0])
                    for key, tup in upstream_times.items():
                        tup = tuple(tup)
                        # if root data is missing, override other values
                        if tup == (None, None) or root_data.get(key) == (None, None):
                            root_data[key] = (None, None)
                        else:
                            root_data[key] = max(root_data.get(key, tup), tup)

        # now that we've done this calculation, store it in the database
        instance.add_asset_event_tags(record.storage_id, {ROOT_DATA_TAG: root_data})
        return root_data

    # get most recent asset materialization event record for this asset
    records = instance.get_event_records(
        EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=asset_key,
        ),
        ascending=False,
        limit=1,
    )

    if len(records) == 0:
        return {root_key: (None, None) for root_key in _get_root_keys(asset_key)}
    else:
        return {
            key: (
                value[0],
                datetime.fromtimestamp(value[1], tz=timezone.utc) if value[1] is not None else None,
            )
            for key, value in _get_upstream_materialization_times(records[0]).items()
        }
