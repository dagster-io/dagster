from dagster import AssetKey, FreshnessPolicy


def assert_assets_match_project(
    dbt_assets, include_seeds_and_snapshots: bool = True, prefix=None, has_non_argument_deps=False
):
    if prefix is None:
        prefix = []
    elif isinstance(prefix, str):
        prefix = [prefix]

    assert len(dbt_assets) == 1
    assets_op = dbt_assets[0].op
    assert assets_op.tags == {"kind": "dbt"}

    # this is the set of keys which are "true" inputs to the op, rather than placeholder inputs
    # which will not be used if this op is run without subsetting
    non_subset_input_keys = set(dbt_assets[0].keys_by_input_name.values()) - dbt_assets[0].keys
    assert len(non_subset_input_keys) == bool(has_non_argument_deps)

    def_outputs = sorted(set(assets_op.output_dict.keys()))
    expected_outputs = sorted(
        [
            "sort_by_calories",
            "least_caloric",
            "sort_hot_cereals_by_calories",
            "sort_cold_cereals_by_calories",
        ]
        + (["cereals", "orders_snapshot"] if include_seeds_and_snapshots else [])
    )
    assert def_outputs == expected_outputs, f"{def_outputs} != {expected_outputs}"
    for asset_name in [
        "subdir_schema/least_caloric",
        "sort_hot_cereals_by_calories",
        "cold_schema/sort_cold_cereals_by_calories",
    ]:
        asset_key = AssetKey(prefix + asset_name.split("/"))
        output_name = asset_key.path[-1]
        assert dbt_assets[0].keys_by_output_name[output_name] == asset_key
        assert dbt_assets[0].asset_deps[asset_key] == {AssetKey(prefix + ["sort_by_calories"])}

    for asset_key, group_name in dbt_assets[0].group_names_by_key.items():
        assert group_name == "default", f'{asset_key} group {group_name} != "default"'

    assert dbt_assets[0].keys_by_output_name["sort_by_calories"] == AssetKey(
        prefix + ["sort_by_calories"]
    )
    sort_by_calories_deps = dbt_assets[0].asset_deps[AssetKey(prefix + ["sort_by_calories"])]
    assert sort_by_calories_deps == {AssetKey(prefix + ["cereals"])}, sort_by_calories_deps

    expected_policies = {
        AssetKey(prefix + ["sort_hot_cereals_by_calories"]): FreshnessPolicy(
            maximum_lag_minutes=123
        ),
        AssetKey(prefix + ["cold_schema", "sort_cold_cereals_by_calories"]): FreshnessPolicy(
            maximum_lag_minutes=123,
            cron_schedule="0 9 * * *",
            cron_schedule_timezone="America/New_York",
        ),
    }
    actual_policies = dbt_assets[0].freshness_policies_by_key
    assert actual_policies == expected_policies
