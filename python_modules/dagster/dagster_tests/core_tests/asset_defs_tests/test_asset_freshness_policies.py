from dagster import SensorDefinition
from dagster.core.asset_defs import (
    DailyAssetFreshnessPolicy,
    HourlyAssetFreshnessPolicy,
    asset,
    freshness_policies_to_repo_defs,
)


def test_one_asset_one_policy():
    @asset
    def asset1():
        pass

    jobs, schedules = freshness_policies_to_repo_defs(
        assets=[asset1],
        freshness_policies=[
            DailyAssetFreshnessPolicy(
                assets=[asset1], fresh_by=9, include_ancestor_updates_before=1
            )
        ],
    )
    assert len(jobs) == 1
    assert len(jobs[0].graph.node_defs) == 1
    assert len(schedules) == 1
    # Scheduling the job as early as possible, at 1 am, maximizes the likelihood of hitting our SLA.
    assert schedules[0].cron_schedule == "0 1 * * *"


def test_independent_assets_one_policy():
    @asset
    def asset1():
        pass

    @asset
    def asset2():
        pass

    jobs, schedules = freshness_policies_to_repo_defs(
        assets=[asset1, asset2],
        freshness_policies=[
            DailyAssetFreshnessPolicy(
                assets=[asset1], fresh_by=9, include_ancestor_updates_before=1
            )
        ],
    )
    assert len(jobs) == 1
    assert len(jobs[0].graph.node_defs) == 1
    assert len(schedules) == 1
    # Scheduling the job as early as possible, at 1 am, maximizes the likelihood of hitting our SLA.
    assert schedules[0].cron_schedule == "0 1 * * *"


def test_asset_dep_one_policy():
    @asset
    def asset1():
        pass

    @asset
    def asset2(asset1):
        pass

    jobs, schedules = freshness_policies_to_repo_defs(
        assets=[asset1, asset2],
        freshness_policies=[
            DailyAssetFreshnessPolicy(
                assets=[asset2], fresh_by=9, include_ancestor_updates_before=1
            )
        ],
    )
    assert len(jobs) == 1
    assert len(jobs[0].graph.node_defs) == 2
    assert len(schedules) == 1
    # Scheduling the job as early as possible, at 1 am, maximizes the likelihood of hitting our SLA.
    assert schedules[0].cron_schedule == "0 1 * * *"


def test_shared_dep_two_policies():
    """We have two assets that both depend on the same asset, and that both have the same freshness
    policy. These two assets might be owned by different teams that don't have an easy time
    coordinating with each other.

    We can combine them into a single job on a single schedule, which allows us to avoid computing
    the shared dependency twice.
    """

    @asset
    def shared_dep():
        pass

    @asset
    def asset1(shared_dep):
        pass

    @asset
    def asset2(shared_dep):
        pass

    jobs, schedules = freshness_policies_to_repo_defs(
        assets=[shared_dep, asset1, asset2],
        freshness_policies=[
            DailyAssetFreshnessPolicy(
                assets=[asset1], fresh_by=9, include_ancestor_updates_before=1
            ),
            DailyAssetFreshnessPolicy(
                assets=[asset2], fresh_by=9, include_ancestor_updates_before=1
            ),
        ],
    )
    assert len(jobs) == 1
    assert len(jobs[0].graph.node_defs) == 3
    assert len(schedules) == 1
    assert schedules[0].cron_schedule == "0 1 * * *"


def test_shared_dep_two_policies_different_fresh_bys():
    """We have two assets that both depend on the same asset, but that have different freshness
    requirements. asset1 needs to be refreshed by 9 am, and asset2 needs to be refreshed by 8 am.

    Because the requirements for asset2 are a strict superset of the requirements for asset1, we can
    combine them into a single job on a single schedule, which allows us to avoid computing
    the shared dependency twice.
    """

    @asset
    def shared_dep():
        pass

    @asset
    def asset1(shared_dep):
        pass

    @asset
    def asset2(shared_dep):
        pass

    jobs, schedules = freshness_policies_to_repo_defs(
        assets=[shared_dep, asset1, asset2],
        freshness_policies=[
            DailyAssetFreshnessPolicy(
                assets=[asset1], fresh_by=9, include_ancestor_updates_before=1
            ),
            DailyAssetFreshnessPolicy(
                assets=[asset2], fresh_by=8, include_ancestor_updates_before=1
            ),
        ],
    )
    assert len(jobs) == 1
    assert len(jobs[0].graph.node_defs) == 3
    assert len(schedules) == 1
    assert schedules[0].cron_schedule == "0 1 * * *"


def test_shared_dep_two_policies_different_ancestor_updates_before():
    """We have two assets that both depend on the same asset, but that have different requirements
    for which updates from that asset need to be incorporated. By 9 am, asset1 needs to incorporate
    all updates that arrived before 1 am. By 9 am, asset2 needs to incorporate all updates that
    arrived before 2 am.

    Because the requirements for asset2 are a strict superset of the requirements for asset1, we can
    combine them into a single job on a single schedule, which allows us to avoid computing
    the shared dependency twice.
    """

    @asset
    def shared_dep():
        pass

    @asset
    def asset1(shared_dep):
        pass

    @asset
    def asset2(shared_dep):
        pass

    jobs, schedules = freshness_policies_to_repo_defs(
        assets=[shared_dep, asset1, asset2],
        freshness_policies=[
            DailyAssetFreshnessPolicy(
                assets=[asset1], fresh_by=9, include_ancestor_updates_before=1
            ),
            DailyAssetFreshnessPolicy(
                assets=[asset2], fresh_by=9, include_ancestor_updates_before=2
            ),
        ],
    )
    assert len(jobs) == 1
    assert len(jobs[0].graph.node_defs) == 3
    assert len(schedules) == 1
    assert schedules[0].cron_schedule == "0 2 * * *"


def test_shared_dep_non_overlapping_policies():
    """We have two assets that both depend on the same asset, but that have different freshness
    policies. By 9 am, asset1 needs to incorporate all updates that arrived before 8 am. By 6 am,
    asset2 needs to incorporate all updates that arrived before 5 am.

    On any particular day, there's no way for a single run to satisfy the needs of both freshness
    policies. Thus, we need two jobs, both of which includes the shared dep asset, each on their own
    schedule.
    """

    @asset
    def shared_dep():
        pass

    @asset
    def asset1(shared_dep):
        pass

    @asset
    def asset2(shared_dep):
        pass

    jobs, schedules = freshness_policies_to_repo_defs(
        assets=[shared_dep, asset1, asset2],
        freshness_policies=[
            DailyAssetFreshnessPolicy(
                assets=[asset1], fresh_by=9, include_ancestor_updates_before=8
            ),
            DailyAssetFreshnessPolicy(
                assets=[asset2], fresh_by=6, include_ancestor_updates_before=5
            ),
        ],
    )
    assert len(jobs) == 2
    assert len(jobs[0].graph.node_defs) == 2
    assert len(jobs[1].graph.node_defs) == 2
    assert len(schedules) == 2
    assert schedules[0].cron_schedule == "0 8 * * *"
    assert schedules[1].cron_schedule == "0 5 * * *"


def test_daily_rollup_depends_on_hourly():
    """
    By 2 am, we want a run of daily_rollup_asset to have completed that includes all source updates
    before 1 am.

    daily_rollup_assets relationship with its sources is mediated through hourly_asset. There will
    be a run of hourly_asset that needs to complete by 1:30 and includes all source updates before
    1 am.

    Thus, before launching our run that refreshes daily_rollup_asset, we need to wait for the
    completion of the run of hourly_asset that includes all source updates before 1 am.
    """

    @asset
    def hourly_asset():
        pass

    @asset
    def daily_rollup_asset(hourly_asset):
        pass

    jobs, sensors_and_schedules = freshness_policies_to_repo_defs(
        assets=[hourly_asset, daily_rollup_asset],
        freshness_policies=[
            HourlyAssetFreshnessPolicy(
                assets=[hourly_asset], fresh_by=30, include_ancestor_updates_before=0
            ),
            DailyAssetFreshnessPolicy(
                assets=[daily_rollup_asset],
                fresh_by=2,
                include_ancestor_updates_before=1,
            ),
        ],
    )
    assert len(jobs) == 2
    assert len(jobs[0].graph.node_defs) == 1
    assert len(jobs[1].graph.node_defs) == 1
    assert len(sensors_and_schedules) == 2
    assert sensors_and_schedules[0].cron_schedule == "0 * * * *"
    assert isinstance(sensors_and_schedules[1], SensorDefinition)
