import json
from typing import Optional, cast

from dagster import (
    AssetKey,
    DagsterEventType,
    EventRecordsFilter,
    JobDefinition,
    RunRequest,
    SensorDefinition,
    check,
    sensor,
)


def make_hn_tables_updated_sensor(
    job: Optional[JobDefinition] = None,
    pipeline_name: Optional[str] = None,  # legacy arg
    mode: Optional[str] = None,  # legacy arg
) -> SensorDefinition:
    """
    Returns a sensor that launches the given job when the HN "comments" and "stories" tables have
    both been updated.
    """
    check.invariant(job is not None or pipeline_name is not None)
    job_or_pipeline_name = cast(str, job.name if job else pipeline_name)

    @sensor(
        name=f"{job_or_pipeline_name}_on_hn_tables_updated",
        job=job,
        pipeline_name=pipeline_name,
        mode=mode,
    )
    def hn_tables_updated_sensor(context):
        cursor_dict = json.loads(context.cursor) if context.cursor else {}
        comments_cursor = cursor_dict.get("comments")
        stories_cursor = cursor_dict.get("stories")

        comments_event_records = context.instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=AssetKey(["snowflake", "hackernews", "comments"]),
                after_cursor=comments_cursor,
            ),
            ascending=False,
            limit=1,
        )
        stories_event_records = context.instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=AssetKey(["snowflake", "hackernews", "stories"]),
                after_cursor=stories_cursor,
            ),
            ascending=False,
            limit=1,
        )

        if not comments_event_records or not stories_event_records:
            return

        # make sure we only generate events if both table_a and table_b have been materialized since
        # the last evaluation.
        yield RunRequest(run_key=None)

        # update the sensor cursor by combining the individual event cursors from the two separate
        # asset event streams
        context.update_cursor(
            json.dumps(
                {
                    "comments": comments_event_records[0].storage_id,
                    "stories": stories_event_records[0].storage_id,
                }
            )
        )

    # @sensor(
    #     name=f"{job.name}_on_hn_tables_updated", job=job, pipeline_name=pipeline_name, mode=mode
    # )
    # def hn_tables_updated_sensor(context):
    #     if context.last_run_key:
    #         last_comments_key, last_stories_key = list(map(int, context.last_run_key.split("|")))
    #     else:
    #         last_comments_key, last_stories_key = None, None

    #     comments_event_records = context.instance.get_event_records(
    #         EventRecordsFilter(
    #             asset_key=AssetKey(["snowflake", "hackernews", "comments"]),
    #             after_cursor=last_comments_key,
    #         ),
    #         ascending=False,
    #         limit=1,
    #     )

    #     stories_event_records = context.instance.get_event_records(
    #         EventRecordsFilter(
    #             asset_key=AssetKey(["snowflake", "hackernews", "stories"]),
    #             after_cursor=last_stories_key,
    #         ),
    #         ascending=False,
    #         limit=1,
    #     )

    #     if not comments_event_records or not stories_event_records:
    #         return

    #     last_comments_record_id = comments_event_records[0].storage_id
    #     last_stories_record_id = stories_event_records[0].storage_id
    #     run_key = f"{last_comments_record_id}|{last_stories_record_id}"

    #     yield RunRequest(run_key=run_key)

    return hn_tables_updated_sensor
