"""index_refresh_sensor — re-run evaluation when the index version changes (Point 8).

Compares data/index_version.txt against the sensor cursor and requests a run on
change, so the same evaluation runs after an index refresh. In Version 1a the
"index" is a checked-in marker file; in production this swaps for a real index
version signal. Edit index_version.txt while `dagster dev` is running and the
sensor fires a new evaluation.
"""

from dagster import RunRequest, SkipReason, sensor

from ragas_evaluation_pipeline.config import INDEX_VERSION_PATH
from ragas_evaluation_pipeline.jobs import evaluation_job


@sensor(job=evaluation_job, minimum_interval_seconds=30)
def index_refresh_sensor(context):
    current = INDEX_VERSION_PATH.read_text(encoding="utf-8").strip()
    if context.cursor == current:
        return SkipReason(f"index version unchanged ({current})")
    context.update_cursor(current)
    return RunRequest(run_key=current, tags={"index_version": current})
