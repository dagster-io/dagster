def build_source_assets():
    from hacker_news_assets.assets.core.items import comments, stories

    return comments.to_source_assets() + stories.to_source_assets()


source_assets = build_source_assets()
