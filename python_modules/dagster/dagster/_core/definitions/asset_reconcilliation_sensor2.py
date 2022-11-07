class Constraint:
    window_start: datetime = None
    window_end: datetime = None
    after_keys: Set[AssetKey] = None


def plan_runs():
    current_time = datetime.datetime.now()
    assets_defs_by_key = {}
    levels = toposort_levels(asset_keys)

    # look within a 12-hour time window to combine future runs together
    plan_window_start = pendulum.now()
    plan_window_end = plan_window_start + pendulum.duration(hours=12)

    # a dictionary mapping each asset to a set of constraints that must be satisfied about the data
    # times of its upstream assets
    constraints_by_key = defaultdict(set)

    # for each asset with a FreshnessPolicy, get all unsolved constraints for the given time window
    for key, policy in freshness_policies_by_key.items():
        latest_record = ...
        upstream_materialization_times = get_upstream_materialization_times_for_record(
            latest_record
        )
        constraints_by_key[key] = set(
            policy.constraints_for_time_window(
                plan_window_start, plan_window_end, upstream_materialization_times
            )
        )

    # propagate constraints upwards through the graph
    #
    # we ignore whether or not the constraint we're propagating corresponds to an asset which
    # is actually upstream of the asset we're operating on, as we'll filter those invalid
    # constraints out in the next step, and it's expensive to calculate if a given asset is
    # upstream of another asset.
    for level in reversed(levels):
        for key in level:
            for upstream_key in upstream_keys[key]:
                # pass along all of your constraints to your parents
                constraints_by_key[upstream_key] |= constraints_by_key[key]

    # now we have a full set of constraints, we can find solutions for them as we move back down
    # the graph
    will_materialize = set()
    expected_data_times_by_key = {}
    for level in levels:
        for key in level:
            # basically, check the materialization planned events, if the latest one corresponds
            # to an in-progress run this is the start time of that run, if it corresponds to a
            # not-started run, this is the current time, otherwise it's the time of the most recent
            # materialization
            #
            # this also pulls in any other asset keys that are being materialized in the active run
            current_run_data_time, currently_materializing = _get_current_expected_time()
            expected_data_times[key] = current_time

            # first, set your expected data times for each of your directly upstream keys to either
            # the current time (if we plan on materializing this key this tick), or the latest
            # materialization time for that key
            for upstream_key in upstream_keys[key]:
                if upstream_key in will_materialize:
                    expected_data_times[upstream_key] = current_time
                else:
                    expected_data_times[upstream_key] = latest_materialization_by_key[upstream_key]

            # next, combine together all information from upstreams
            for upstream_key in upstream_keys[key]:
                for upstream_upstream_key, expected_data_time in expected_data_times_by_key[
                    upstream_key
                ].items():
                    expected_data_times[upstream_upstream_key] = min(
                        expected_data_times.get(upstream_upstream_key, default=expected_data_time),
                        expected_data_time,
                    )

            # go through each of your constraints and combine them into a single one which can be
            # solved locally
            merged_constraint = None
            for constraint_key, required_data_time, required_by_time in sorted(
                constraints_by_key[key]
            ):

                if not (
                    # this constraint is irrelevant, as a currently-executing run will solve it
                    (
                        constraint_key in currently_materializing
                        and current_run_data_time > required_data_time
                    )
                    # this constraint is irrelevant, as it does not correspond to an asset which is
                    # directly upstream of this asset, nor to an asset which is transitively
                    # upstream of this asset and will be materialized this tick
                    or constraint_key not in expected_data_times
                    # this constraint is irrelevant, as it requires data more recent than the data
                    # for this constraint key if we were to execute this asset on this tick
                    or required_data_time > expected_data_times[constraint_key]
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
            # possible, see if you can solve it by kicking off a run now
            if merged_constraint is not None and merged_constraint[0] < current_time:
                will_materialize.add(key)
                # only propogate these expected data times if you plan on kicking off a run
                expected_data_times_by_key[key] = expected_data_times

    if len(should_materialize) > 0:
        context.update_cursor(json.dumps(cursor_update_dict))
        context._cursor_has_been_updated = True  # pylint: disable=protected-access
        return RunRequest(
            run_key=f"{context.cursor}", asset_selection=list(should_materialize), tags=run_tags
        )
