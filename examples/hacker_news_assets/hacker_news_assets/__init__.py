from hacker_news_assets.resources import RESOURCES_LOCAL

from dagster import AssetGroup, ScheduleDefinition, repository


@repository
def core():
    assets = AssetGroup.from_package_name(
        "hacker_news_assets.assets.core", resource_defs=RESOURCES_LOCAL
    )
    return [assets]


@repository
def activity_analytics():
    assets = AssetGroup.from_package_name(
        "hacker_news_assets.assets.activity_analytics", resource_defs=RESOURCES_LOCAL
    )
    return [
        assets,
        ScheduleDefinition(
            job=assets.build_job("daily_activity_analytics"), cron_schedule="@daily"
        ),
    ]


@repository
def recommender():
    assets = AssetGroup.from_package_name(
        "hacker_news_assets.assets.recommender", resource_defs=RESOURCES_LOCAL
    )
    return [assets]
