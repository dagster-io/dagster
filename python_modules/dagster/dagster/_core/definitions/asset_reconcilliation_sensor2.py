from dagster import (
    AssetKey,
    EventLogRecord,
    EventRecordsFilter,
    RunsFilter,
    DagsterInstance,
    RepositoryDefinition,
    DagsterEventType,
)
from dagster._core.storage.pipeline_run import IN_PROGRESS_RUN_STATUSES
from dagster._core.utils import toposort_flatten
from dagster._utils.calculate_data_time import get_upstream_materialization_times_for_record
from collections import defaultdict
import datetime
from typing import Set, Dict, Tuple, Optional
from dagster._core.selector.subset_selector import generate_asset_dep_graph


def _get_upstream_mapping(assets_defs, source_assets):
    upstream_str_mapping = generate_asset_dep_graph(assets_defs, source_assets)["upstream"]
    return {
        AssetKey.from_user_string(k): {AssetKey.from_user_string(vv) for vv in v}
        for k, v in upstream_str_mapping.items()
    }


def _roots_for_key(key, upstream_keys):
    if not upstream_keys[key]:
        return {key}
    return set().union(*(_roots_for_key(uk, upstream_keys) for uk in upstream_keys[key]))


def _latest_record_for_key(
    instance: DagsterInstance, key: AssetKey, latest_record_cache: Dict[AssetKey, EventLogRecord]
) -> Optional[EventLogRecord]:
    if key not in latest_record_cache:
        records = instance.get_event_records(
            EventRecordsFilter(event_type=DagsterEventType.ASSET_MATERIALIZATION, asset_key=key),
            ascending=False,
            limit=1,
        )
        latest_record = records[0] if records else None
        latest_record_cache[key] = latest_record

    return latest_record_cache[key]


def _current_run_for_key(
    instance: DagsterInstance,
    key: AssetKey,
    current_run_cache: Dict[str, Tuple[Optional[float], Set[AssetKey]]],
) -> Tuple[Optional[float], Set[AssetKey]]:
    records = instance.get_event_records(
        EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
            asset_key=key,
        ),
        ascending=False,
        limit=1,
    )
    latest_materialization_planned = records[0] if records else None
    if latest_materialization_planned is None:
        return (None, set())

    latest_run_id = latest_materialization_planned.event_log_entry.run_id
    if latest_run_id not in current_run_cache:
        results = instance.get_runs(
            filters=RunsFilter(run_ids=[latest_run_id], statuses=IN_PROGRESS_RUN_STATUSES)
        )
        current_run = results[0] if results else None
        if current_run is None:
            current_run_cache[latest_run_id] = (None, set())
        else:
            other_materialized_asset_records = instance.get_records_for_run(
                run_id=latest_run_id,
                of_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
            ).records
            other_materialized_assets = {
                event.asset_key for event in other_materialized_asset_records
            }
            current_run_cache[latest_run_id] = (
                latest_materialization_planned.event_log_entry.timestamp,
                other_materialized_assets,
            )

    return current_run_cache[latest_run_id]


def assets_to_materialize(
    instance: DagsterInstance, repository_def: RepositoryDefinition
) -> Set[AssetKey]:
    """Returns a set of AssetKeys to materialize in order to abide by the given FreshnessPolicies.
    Attempts to minimize the total number of asset executions.
    """
    assets_defs_by_key = repository_def._assets_defs_by_key  # pylint: disable=protected-access
    source_asset_defs_by_key = repository_def.source_assets_by_key

    assets_defs = assets_defs_by_key.values()
    source_assets = source_asset_defs_by_key.values()

    upstream_keys: Mapping[AssetKey, Set[AssetKey]] = _get_upstream_mapping(
        assets_defs=assets_defs, source_assets=source_assets
    )
    upstream_key_strs = generate_asset_dep_graph(assets_defs, source_assets)["upstream"]

    # look within a 12-hour time window to combine future runs together
    current_time = datetime.datetime.now(datetime.timezone.utc)
    plan_window_start = current_time
    plan_window_end = plan_window_start + datetime.timedelta(hours=12)

    # a dictionary mapping each asset to a set of constraints that must be satisfied about the data
    # times of its upstream assets
    constraints_by_key = defaultdict(set)

    _latest_record_cache: Dict[AssetKey, EventLogRecord] = dict()
    _current_run_cache: Dict[str, Tuple[Optional[Float], Set[AssetKey]]] = dict()

    # for each asset with a FreshnessPolicy, get all unsolved constraints for the given time window
    for key, assets_def in assets_defs_by_key.items():
        freshness_policy = assets_def.freshness_policies_by_key.get(key)
        if freshness_policy is not None:
            latest_record = _latest_record_for_key(instance, key, _latest_record_cache)
            upstream_materialization_times = get_upstream_materialization_times_for_record(
                instance=instance,
                upstream_asset_key_mapping=upstream_key_strs,
                relevant_upstream_keys=_roots_for_key(key, upstream_keys),
                record=latest_record,
            )
            constraints_by_key[key] = set(
                freshness_policy.constraints_for_time_window(
                    plan_window_start, plan_window_end, upstream_materialization_times
                )
            )

    toposorted_assets = toposort_flatten(upstream_keys)
    # propagate constraints upwards through the graph
    #
    # we ignore whether or not the constraint we're propagating corresponds to an asset which
    # is actually upstream of the asset we're operating on, as we'll filter those invalid
    # constraints out in the next step, and it's expensive to calculate if a given asset is
    # upstream of another asset.
    for key in reversed(toposorted_assets):
        for upstream_key in upstream_keys[key]:
            # pass along all of your constraints to your parents
            constraints_by_key[upstream_key] |= constraints_by_key[key]

    # now we have a full set of constraints, we can find solutions for them as we move back down
    will_materialize: Set[AssetKey] = set()
    expected_data_times_by_key: Dict[Dict[AssetKey, float]] = defaultdict(dict)
    for key in toposorted_assets:
        # check to find if this asset is currently being materialized by a run, and if so, which
        # other assets are being materialized in that run
        current_run_data_time, currently_materializing = _current_run_for_key(
            instance, key, _current_run_cache
        )

        expected_data_times = {key: current_time}

        # first, set your expected data times for each of your directly upstream keys to either
        # the current time (if we plan on materializing this key this tick), or the latest
        # materialization time for that key
        for upstream_key in upstream_keys[key]:
            if upstream_key in will_materialize:
                expected_data_times[upstream_key] = current_time
            else:
                expected_data_times[upstream_key] = datetime.datetime.fromtimestamp(
                    _latest_record_for_key(
                        instance, upstream_key, _latest_record_cache
                    ).event_log_entry.timestamp,
                    tz=datetime.timezone.utc,
                )

        # next, combine together all information from upstreams
        for upstream_key in upstream_keys[key]:
            for upstream_upstream_key, expected_data_time in expected_data_times_by_key[
                upstream_key
            ].items():
                expected_data_times[upstream_upstream_key] = min(
                    expected_data_times.get(upstream_upstream_key, expected_data_time),
                    expected_data_time,
                )

        # the current data time is based off of the most recent materialization
        latest_record = _latest_record_for_key(instance, key, _latest_record_cache)
        constraint_keys = {k for k, _, _ in constraints_by_key[key]}
        current_data_times = get_upstream_materialization_times_for_record(
            instance,
            upstream_key_strs,
            relevant_upstream_keys=set(expected_data_times.keys()) & constraint_keys,
            record=latest_record,
        )

        # go through each of your constraints and combine them into a single one which can be
        # solved locally
        merged_constraint = None
        for constraint_key, required_data_time, required_by_time in sorted(constraints_by_key[key]):

            if not (
                # this constraint is irrelevant, as it is satisfied by the current data time
                current_data_times[constraint_key] > required_data_time
                # this constraint is irrelevant, as a currently-executing run will satisfy it
                or (
                    constraint_key in currently_materializing
                    and current_run_data_time > required_data_time
                )
                # this constraint is irrelevant, as it does not correspond to an asset which is
                # directly upstream of this asset, nor to an asset which is transitively
                # upstream of this asset and will be materialized this tick
                or constraint_key not in expected_data_times
            ):

                # attempt to merge as many constraints as possible into a single execution
                if merged_constraint is None:
                    merged_constraint = (required_data_time, required_by_time)
                # you can merge this constraint with the existing one, as it requires data
                # from a time before the current time window ends
                elif required_data_time < merged_constraint[1]:
                    merged_constraint = (
                        # take the stricter of the two requirements
                        max(required_data_time, merged_constraint[0]),
                        # take the stricter of the two requirements
                        min(required_by_time, merged_constraint[1]),
                    )

        # now that you have a compressed constraint which has merged as many constraints as
        # possible, kick off a run when you're halfway through that time window
        if merged_constraint is not None and merged_constraint[0] <= current_time:
            will_materialize.add(key)
            # only propogate these expected data times if you plan on kicking off a run
            expected_data_times_by_key[key] = expected_data_times
        else:
            # otherwise, the expected data time will be the current one
            expected_data_times_by_key[key] = current_data_times

    return will_materialize
