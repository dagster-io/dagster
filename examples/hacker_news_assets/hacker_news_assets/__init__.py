from hacker_news_assets.resources import RESOURCES_LOCAL

from dagster import AssetGroup, repository

core_assets = AssetGroup.from_package_name(
    "hacker_news_assets.assets.core", resource_defs=RESOURCES_LOCAL
)


@repository
def core():
    return [core_assets]


@repository
def activity_analytics():
    assets = AssetGroup.from_package_name(
        "hacker_news_assets.assets.activity_analytics", resource_defs=RESOURCES_LOCAL
    )
    return [assets]


@repository
def recommender():
    assets = AssetGroup.from_package_name(
        "hacker_news_assets.assets.recommender", resource_defs=RESOURCES_LOCAL
    )
    return [assets]
