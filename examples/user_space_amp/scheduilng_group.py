from typing import List, NamedTuple

from dagster import (
    AssetKey,
    AssetSelection,
    Definitions,
    RunRequest,
    SensorEvaluationContext,
    SkipReason,
    _check as check,
    asset,
    define_asset_job,
    multi_asset_sensor,
)


def build_eager_sensor(name: str, upstream_asset_keys, job_def):
    check.list_param(upstream_asset_keys, "asset_keys", of_type=AssetKey)

    @multi_asset_sensor(
        name=name,
        monitored_assets=AssetSelection.keys(*upstream_asset_keys),
        job=job_def,
        minimum_interval_seconds=2,
    )
    def _sensor_impl(context: SensorEvaluationContext):
        # todo write code that ensures that both assets have materializations
        records_by_key = context.latest_materialization_records_by_key(upstream_asset_keys)
        no_records = set()
        for asset_key, latest in records_by_key.items():
            if latest is None:
                no_records.add(asset_key)

        if no_records == set(upstream_asset_keys):
            return SkipReason(f"No new materializations detected for {upstream_asset_keys}")

        context.advance_cursor(records_by_key)
        return RunRequest()

    return _sensor_impl


@asset
def root_asset() -> None:
    pass


@asset(deps=[root_asset])
def asset_a() -> None:
    pass


@asset(deps=[root_asset])
def asset_b() -> None:
    pass


@asset(deps=[asset_a])
def asset_c() -> None:
    pass


@asset(deps=[asset_b])
def asset_d() -> None:
    pass


@asset(deps=[asset_c, asset_d])
def final_asset() -> None:
    pass


class MaterializationGroup(NamedTuple):
    name: str
    selection: AssetSelection
    upstream_asset_keys: List[AssetKey]  # TODO: programmtically compute using graph traversal


def build_for_materialization_groups(materialization_groups: List[MaterializationGroup]):
    jobs = {
        mg.name: define_asset_job(name=f"{mg.name}_name_job", selection=mg.selection)
        for mg in materialization_groups
    }

    sensors = {
        mg.name: build_eager_sensor(
            name=f"{mg.name}_sensor",
            upstream_asset_keys=mg.upstream_asset_keys,
            job_def=jobs[mg.name],
        )
        for mg in materialization_groups
    }

    return list(sensors.values())


# This is where I stopped, but it would be fairly straight forward to compute
# these groups from a higher-level API that does some graph traversals
materialization_groups = [
    MaterializationGroup(
        name="downstream_of_a",
        selection=AssetSelection.assets(asset_a, asset_c),
        upstream_asset_keys=[root_asset.key],
    ),
    MaterializationGroup(
        name="downstream_of_b",
        selection=AssetSelection.assets(asset_b, asset_d),
        upstream_asset_keys=[root_asset.key],
    ),
    MaterializationGroup(
        name="final_asset",
        selection=AssetSelection.assets(final_asset),
        upstream_asset_keys=[asset_c.key, asset_d.key],
    ),
]

defs = Definitions(
    assets=[root_asset, asset_a, asset_b, asset_c, asset_d, final_asset],
    sensors=build_for_materialization_groups(materialization_groups),
)
