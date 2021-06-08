from dagster import AssetKey, RunRequest, sensor


@sensor(pipeline_name="story_recommender", mode="prod")
def story_recommender_on_hn_table_update(context):
    """Kick off a run if both the stories and comments tables have received updates"""
    if context.last_run_key:
        last_comments_key, last_stories_key = list(map(int, context.last_run_key.split("|")))
    else:
        last_comments_key, last_stories_key = None, None

    comments_events = context.instance.events_for_asset_key(
        AssetKey(["snowflake", "hackernews", "comments"]),
        after_cursor=last_comments_key,
        ascending=False,
        limit=1,
    )

    stories_events = context.instance.events_for_asset_key(
        AssetKey(["snowflake", "hackernews", "stories"]),
        after_cursor=last_stories_key,
        ascending=False,
        limit=1,
    )

    if not comments_events or not stories_events:
        return

    last_comments_record_id = comments_events[0][0]
    last_stories_record_id = stories_events[0][0]
    run_key = f"{last_comments_record_id}|{last_stories_record_id}"

    yield RunRequest(run_key=run_key)
