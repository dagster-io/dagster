from dagster import AssetKey, EventRecordsFilter, RunRequest, sensor

from ..jobs.story_recommender import story_recommender_prod_job, story_recommender_staging_job


@sensor(job=story_recommender_prod_job)
def story_recommender_on_hn_table_update_prod(context):
    yield from _story_recommender_on_hn_table_update(context)


@sensor(job=story_recommender_staging_job)
def story_recommender_on_hn_table_update_staging(context):
    yield from _story_recommender_on_hn_table_update(context)


def _story_recommender_on_hn_table_update(context):
    """Kick off a run if both the stories and comments tables have received updates"""
    if context.last_run_key:
        last_comments_key, last_stories_key = list(map(int, context.last_run_key.split("|")))
    else:
        last_comments_key, last_stories_key = None, None

    comments_event_records = context.instance.get_event_records(
        EventRecordsFilter(
            asset_key=AssetKey(["snowflake", "hackernews", "comments"]),
            after_cursor=last_comments_key,
        ),
        ascending=False,
        limit=1,
    )

    stories_event_records = context.instance.get_event_records(
        EventRecordsFilter(
            asset_key=AssetKey(["snowflake", "hackernews", "stories"]),
            after_cursor=last_stories_key,
        ),
        ascending=False,
        limit=1,
    )

    if not comments_event_records or not stories_event_records:
        return

    last_comments_record_id = comments_event_records[0].storage_id
    last_stories_record_id = stories_event_records[0].storage_id
    run_key = f"{last_comments_record_id}|{last_stories_record_id}"

    yield RunRequest(run_key=run_key)
