from hacker_news_assets.assets import asset_group

activity_stats_job = asset_group.build_job(
    name="activity_stats",
    selection=[
        "comment_daily_stats",
        "story_daily_stats",
        "activity_daily_stats",
        "activity_forecast",
    ],
)
