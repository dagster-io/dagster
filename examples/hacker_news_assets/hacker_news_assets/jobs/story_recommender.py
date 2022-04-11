from hacker_news_assets.assets import local_assets, prod_assets, staging_assets

from dagster import AssetGroup, JobDefinition


def make_story_recommender_job(asset_group: AssetGroup) -> JobDefinition:
    return asset_group.build_job(
        name="story_recommender",
        selection=["comment_stories*"],
    )


story_recommender_prod_job = make_story_recommender_job(prod_assets)
story_recommender_staging_job = make_story_recommender_job(staging_assets)
story_recommender_local_job = make_story_recommender_job(local_assets)
