from hacker_news_assets.assets import asset_group

story_recommender_job = asset_group.build_job(
    name="story_recommender",
    selection=["comment_stories*"],
)
