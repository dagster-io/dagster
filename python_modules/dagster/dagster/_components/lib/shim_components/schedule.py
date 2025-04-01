from dagster import schedule
from dagster._components.lib.shim_components.base import ShimScaffolder
from dagster._components.scaffold.scaffold import scaffold_with


class ScheduleScaffolder(ShimScaffolder):
    def get_text(self, filename: str) -> str:
        return f"""# import dagster as dg
# 
#
# @dg.schedule(cron_schedule=..., target=...)
# def {filename}(context: dg.ScheduleEvaluationContext): ...

"""


scaffold_with(ScheduleScaffolder)(schedule)
