from dagster import AssetGroup, JobDefinition


def build_activity_stats_job(asset_group: AssetGroup) -> JobDefinition:
    return asset_group.build_job(
        name="activity_stats",
        selection=[
            "comment_daily_stats",
            "story_daily_stats",
            "activity_daily_stats",
            "activity_forecast",
        ],
    )
