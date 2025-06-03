from dagster._core.definitions.decorators.schedule_decorator import schedule
from dagster.components.lib.shim_components.base import ShimScaffolder
from dagster.components.scaffold.scaffold import ScaffoldRequest, scaffold_with


class ScheduleScaffolder(ShimScaffolder):
    def get_text(self, request: ScaffoldRequest) -> str:
        return f"""from typing import Union

import dagster as dg


@dg.schedule(cron_schedule="@daily", target="*")
def {request.target_path.stem}(context: dg.ScheduleEvaluationContext) -> Union[dg.RunRequest, dg.SkipReason]:
    return dg.SkipReason("Skipping. Change this to return a RunRequest to launch a run.")
"""


scaffold_with(ScheduleScaffolder)(schedule)
