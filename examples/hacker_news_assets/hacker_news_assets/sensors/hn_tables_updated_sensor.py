from typing import Optional

from dagster import (
    AssetKey,
    EventRecordsFilter,
    JobDefinition,
    RunRequest,
    SensorDefinition,
    sensor,
)


def make_hn_tables_updated_sensor(job: Optional[JobDefinition] = None) -> SensorDefinition:
    """
    Returns a sensor that launches the given job when the HN "comments" and "stories" tables have
    both been updated.
    """

    @sensor(name=f"{job.name}_on_hn_tables_updated", job=job)
    def hn_tables_updated_sensor(context):
        if context.last_run_key:
            last_comments_key, last_stories_key = list(map(int, context.last_run_key.split("|")))
        else:
            last_comments_key, last_stories_key = None, None

        comments_event_records = context.instance.get_event_records(
            EventRecordsFilter(asset_key=AssetKey(["comments"]), after_cursor=last_comments_key),
            ascending=False,
            limit=1,
        )

        stories_event_records = context.instance.get_event_records(
            EventRecordsFilter(asset_key=AssetKey(["stories"]), after_cursor=last_stories_key),
            ascending=False,
            limit=1,
        )

        if not comments_event_records or not stories_event_records:
            return

        last_comments_record_id = comments_event_records[0].storage_id
        last_stories_record_id = stories_event_records[0].storage_id
        run_key = f"{last_comments_record_id}|{last_stories_record_id}"

        yield RunRequest(run_key=run_key)

    return hn_tables_updated_sensor
