from typing import Union

import dagster as dg


@dg.schedule(cron_schedule="@daily", target="*")
def schedule(
    context: dg.ScheduleEvaluationContext,
) -> Union[dg.RunRequest, dg.SkipReason]:
    return dg.SkipReason(
        "Skipping. Change this to return a RunRequest to launch a run."
    )
