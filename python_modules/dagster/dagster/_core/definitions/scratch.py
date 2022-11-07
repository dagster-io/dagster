def plan_runs():
    current_time = datetime.datetime.now()
    assets_defs_by_key = {}
    levels = toposort_levels(asset_keys)

    plan_window_start = pendulum.now()
    plan_window_end = plan_window_start + pendulum.duration(hours=12)

    constraints_by_key = defaultdict(set)
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

    for level in reversed(levels):
        for key in level:
            for upstream_key in upstream_keys[key]:
                constraints_by_key[upstream_key] |= constraints_by_key[key]

    will_materialize = set()
    expected_data_times_by_key = {}
    for level in levels:
        for key in level:
            current_run_data_time, currently_materializing = _get_current_expected_time()
            expected_data_times[key] = current_time

            for upstream_key in upstream_keys[key]:
                if upstream_key in will_materialize:
                    expected_data_times[upstream_key] = current_time
                else:
                    expected_data_times[upstream_key] = latest_materialization_by_key[upstream_key]

            for upstream_key in upstream_keys[key]:
                for upstream_upstream_key, expected_data_time in expected_data_times_by_key[
                    upstream_key
                ].items():
                    expected_data_times[upstream_upstream_key] = min(
                        expected_data_times.get(upstream_upstream_key, default=expected_data_time),
                        expected_data_time,
                    )

            merged_constraint = None
            for constraint_key, required_data_time, required_by_time in sorted(
                constraints_by_key[key]
            ):

                if not (
                    (
                        constraint_key in currently_materializing
                        and current_run_data_time > required_data_time
                    )
                    or constraint_key not in expected_data_times
                    or required_data_time > expected_data_times[constraint_key]
                ):

                    if merged_constraint is None:
                        merged_constraint = (required_data_time, required_by_time)
                    elif required_data_time < merged_constraint[1]:
                        merged_constraint = (
                            max(required_data_time, merged_constraint[0]),
                            min(required_by_time, merged_constraint[1]),
                        )

            if merged_constraint is not None and merged_constraint[0] < current_time:
                will_materialize.add(key)
                expected_data_times_by_key[key] = expected_data_times

    if len(should_materialize) > 0:
        context.update_cursor(json.dumps(cursor_update_dict))
        context._cursor_has_been_updated = True  # pylint: disable=protected-access
        return RunRequest(
            run_key=f"{context.cursor}", asset_selection=list(should_materialize), tags=run_tags
        )
