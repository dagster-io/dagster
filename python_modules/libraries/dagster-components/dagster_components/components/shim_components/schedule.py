from dagster_components.blueprint import scaffold_with
from dagster_components.components.shim_components.base import ShimBlueprint, ShimComponent


class ScheduleBlueprint(ShimBlueprint):
    def get_text(self) -> str:
        return """# import dagster as dg
# 
#
# @dg.schedule(cron_schedule=..., target=...)
# def my_schedule(context: dg.ScheduleEvaluationContext): ...

"""


@scaffold_with(ScheduleBlueprint)
class RawScheduleComponent(ShimComponent):
    """Schedule component."""
