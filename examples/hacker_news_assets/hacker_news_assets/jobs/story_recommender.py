from dagster import AssetGroup, JobDefinition


def build_story_recommender_job(asset_group: AssetGroup) -> JobDefinition:
    return asset_group.build_job(
        name="story_recommender",
        selection=["comment_stories*"],
    )
